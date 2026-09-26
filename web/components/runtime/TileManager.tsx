"use client";
/* eslint-disable react-hooks/immutability -- R3F runtime state is intentionally mutable outside React's render cycle. */

import { useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";
import { Component, Suspense, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ACTIVE_RADIUS_M, DEACTIVATE_RADIUS_M } from "./spatial";
import { computeDesiredTiles, resolveVisibleTileSet, shouldRequestTile, streamDistance } from "./stabilityLogic";
import { observeVisibility, stability } from "./stability";
import type { RuntimeRefs, RuntimeSummary, TileMode, TileRuntimeRecord, TileSidecar, WorldTile } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";
import { harmonizeScene } from "./visualSystem";

type Props = {
  tiles: WorldTile[];
  mode: TileMode;
  refs: RuntimeRefs;
  onSummary: (summary: RuntimeSummary) => void;
  onInitialReady: () => void;
  materials: BGCVisualMaterials;
  quality: import("./types").EnvironmentQuality;
  priorityTileId?: string | null;
  navigation: import("./types").NavigationMode;
};

class TileErrorBoundary extends Component<{ children: ReactNode; onError: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onError(); }
  render() { return this.state.failed ? null : this.props.children; }
}

function TileAsset({ record, visible, refs, materials, quality, onReady }: {
  record: TileRuntimeRecord;
  visible: boolean;
  refs: RuntimeRefs;
  onReady: (id: string) => void;
  materials: BGCVisualMaterials;
  quality: import("./types").EnvironmentQuality;
}) {
  const gltf = useGLTF(record.url);
  useEffect(() => {
    gltf.scene.name = record.tile_id;
    harmonizeScene(gltf.scene, materials, quality);
    refs.tileScenes.current.set(record.tile_id, gltf.scene);
    onReady(record.tile_id);
    return () => { refs.tileScenes.current.delete(record.tile_id); };
  }, [gltf.scene, materials, onReady, quality, record.tile_id, refs.tileScenes]);
  return <primitive object={gltf.scene} visible={visible} />;
}

export function TileManager({ tiles, mode, refs, materials, quality, priorityTileId, navigation, onSummary, onInitialReady }: Props) {
  const records = useMemo(() => new Map<string, TileRuntimeRecord>(tiles.map((tile) => [tile.tile_id, {
    ...tile,
    state: "UNREQUESTED",
    distance: Number.POSITIVE_INFINITY,
    last_used_ms: 0,
    requested_count: 0,
    model_ready: false,
  } as TileRuntimeRecord])), [tiles]);
  const [mountedIds, setMountedIds] = useState<string[]>([]);
  const [visibleIds, setVisibleIds] = useState<Set<string>>(new Set());
  const lastEvaluation = useRef(0);
  const initialReadySent = useRef(false);
  const transitions = useRef(0);

  useEffect(() => {
    refs.tileRecords.current = records;
    initialReadySent.current = false;
  }, [records, refs.tileRecords]);

  const loadSidecar = useCallback(async (record: TileRuntimeRecord) => {
    if (record.sidecar) return;
    const response = await fetch(`/world/tiles/${record.tile_id}.json`);
    if (!response.ok) throw new Error(`Tile sidecar failed: ${record.tile_id} HTTP ${response.status}`);
    const sidecar = await response.json() as TileSidecar;
    record.sidecar = sidecar;
    refs.sidecars.current.set(record.tile_id, sidecar);
    // Metadata is optional for rendering; a sidecar failure only limits picking/collision.
  }, [refs.sidecars]);

  const requestTile = useCallback((record: TileRuntimeRecord) => {
    if (record.state !== "UNREQUESTED") return;
    record.state = "PRELOADING";
    record.requested_count += 1;
    stability.tile_requests += 1;
    if (record.requested_count > 1) stability.repeated_tile_requests += 1;
    transitions.current += 1;
    stability.tile_state_transitions += 1;
    useGLTF.preload(record.url);
    void loadSidecar(record).catch(() => { /* Render the GLB even when metadata is unavailable. */ });
    setMountedIds((current) => current.includes(record.tile_id) ? current : [...current, record.tile_id]);
  }, [loadSidecar]);

  useEffect(() => {
    if (mode !== "ALL_LOADED") return;
    records.forEach((record) => requestTile(record));
  }, [mode, records, requestTile]);

  const markReady = useCallback((tileId: string) => {
    const record = records.get(tileId);
    if (record) record.model_ready = true;
    if (record?.state === "PRELOADING") {
      record.state = "READY";
      transitions.current += 1;
      stability.tile_state_transitions += 1;
    }
  }, [records]);

  useFrame(({ camera }) => {
    const now = performance.now();
    if (now - lastEvaluation.current < 150) return;
    lastEvaluation.current = now;
    const anchors = refs.anchors.current;
    if (priorityTileId) {
      const priority = records.get(priorityTileId);
      if (priority) requestTile(priority);
    }
    const desired = computeDesiredTiles(tiles, anchors);
    const ready = new Set<string>();
    const active = new Set<string>();
    let preloading = 0;
    let cached = 0;
    let errors = 0;
    let bytes = 0;
    let requests = 0;
    let repeated = 0;

    records.forEach((record) => {
      record.distance = streamDistance(record, anchors);
      if (mode === "ALL_LOADED") requestTile(record);
      else if (record.state === "UNREQUESTED" && shouldRequestTile(record.distance)) requestTile(record);

      if ((record.state === "READY" || record.state === "CACHED") && (mode === "ALL_LOADED" || record.distance <= ACTIVE_RADIUS_M)) {
        record.state = "ACTIVE";
        record.last_used_ms = now;
        transitions.current += 1;
      } else if (record.state === "ACTIVE" && mode === "DYNAMIC" && record.distance > DEACTIVATE_RADIUS_M) {
        record.state = "CACHED";
        transitions.current += 1;
      }
      if (record.state === "READY" && record.distance > ACTIVE_RADIUS_M) record.state = "CACHED";
      if (record.model_ready && record.state !== "ERROR") ready.add(record.tile_id);
      if (record.state === "ACTIVE") active.add(record.tile_id);
      if (record.state === "PRELOADING") preloading += 1;
      if (record.state === "CACHED" || record.state === "READY") cached += 1;
      if (record.state === "ERROR") errors += 1;
      if (record.requested_count) { bytes += record.size_bytes; requests += record.requested_count; }
      if (record.requested_count > 1) repeated += record.requested_count - 1;
    });
    const visible = resolveVisibleTileSet(mode === "ALL_LOADED" ? ready : new Set([...desired, ...active]), ready, refs.visibleTileIds.current, mode === "ALL_LOADED");
    // Defer retirement until at least one replacement is already mounted and ready.
    for (const id of visible) {
      const record = records.get(id);
      if (record?.state === "CACHED" && !desired.has(id) && mode === "DYNAMIC") continue;
      if (record?.state !== "ACTIVE" && record?.model_ready) { record!.state = "ACTIVE"; active.add(id); }
    }
    refs.visibleTileIds.current = visible;
    refs.activeTileIds.current = visible;
    setVisibleIds((previous) => previous.size === visible.size && [...visible].every((id) => previous.has(id)) ? previous : visible);
    observeVisibility(initialReadySent.current, visible.size, now, { mode: navigation, camera: [camera.position.x, camera.position.y, camera.position.z], anchors: anchors.map((a) => ({ ...a })), active_ids: [...active], preloading });
    const summary: RuntimeSummary = {
      active: active.size,
      visible: visible.size,
      visibleIds: [...visible].sort(),
      desired: desired.size,
      ready: ready.size,
      preloading,
      cached,
      errors,
      activeIds: [...active].sort(),
      networkBytes: bytes,
      networkRequests: requests,
      repeatedRequests: repeated,
      activeLod1: [],
      camera: [Number(camera.position.x.toFixed(1)), Number(camera.position.y.toFixed(1)), Number(camera.position.z.toFixed(1))],
      transitions: transitions.current,
    };
    onSummary(summary);
    if (!initialReadySent.current && visible.size > 0) {
      initialReadySent.current = true;
      onInitialReady();
    }
  });

  return <>{mountedIds.map((id) => {
    const record = records.get(id)!;
    return <TileErrorBoundary key={id} onError={() => { record.state = "ERROR"; record.model_ready = false; }}><Suspense fallback={null}><TileAsset record={record} visible={visibleIds.has(id)} refs={refs} materials={materials} quality={quality} onReady={markReady} /></Suspense></TileErrorBoundary>;
  })}</>;
}
