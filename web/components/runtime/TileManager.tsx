"use client";
/* eslint-disable react-hooks/immutability -- R3F runtime state is intentionally mutable outside React's render cycle. */

import { useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ACTIVE_RADIUS_M, DEACTIVATE_RADIUS_M, PRELOAD_RADIUS_M, RETENTION_RADIUS_M, distanceToTileBounds } from "./spatial";
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
};

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

export function TileManager({ tiles, mode, refs, materials, quality, onSummary, onInitialReady }: Props) {
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
    if (record.model_ready && record.state === "PRELOADING") record.state = "READY";
  }, [refs.sidecars]);

  const requestTile = useCallback((record: TileRuntimeRecord) => {
    if (record.state !== "UNREQUESTED") return;
    record.state = "PRELOADING";
    record.requested_count += 1;
    transitions.current += 1;
    useGLTF.preload(record.url);
    void loadSidecar(record).catch(() => { record.state = "ERROR"; });
    setMountedIds((current) => current.includes(record.tile_id) ? current : [...current, record.tile_id]);
  }, [loadSidecar]);

  useEffect(() => {
    if (mode !== "ALL_LOADED") return;
    records.forEach((record) => requestTile(record));
  }, [mode, records, requestTile]);

  const markReady = useCallback((tileId: string) => {
    const record = records.get(tileId);
    if (record) record.model_ready = true;
    if (record?.sidecar && record.state === "PRELOADING") {
      record.state = "READY";
      transitions.current += 1;
    }
  }, [records]);

  useFrame(({ camera }) => {
    const now = performance.now();
    if (now - lastEvaluation.current < 150) return;
    lastEvaluation.current = now;
    const focus = refs.focus.current;
    const visible = new Set<string>();
    const active = new Set<string>();
    let preloading = 0;
    let cached = 0;
    let errors = 0;
    let bytes = 0;
    let requests = 0;
    let repeated = 0;

    records.forEach((record) => {
      record.distance = distanceToTileBounds(focus.x, focus.z, record);
      if (mode === "ALL_LOADED") requestTile(record);
      else if (record.state === "UNREQUESTED" && record.distance <= PRELOAD_RADIUS_M) requestTile(record);

      if ((record.state === "READY" || record.state === "CACHED") && (mode === "ALL_LOADED" || record.distance <= ACTIVE_RADIUS_M)) {
        record.state = "ACTIVE";
        record.last_used_ms = now;
        transitions.current += 1;
      } else if (record.state === "ACTIVE" && mode === "DYNAMIC" && record.distance > DEACTIVATE_RADIUS_M) {
        record.state = "CACHED";
        transitions.current += 1;
      }
      if (record.state === "READY" && record.distance > ACTIVE_RADIUS_M) record.state = "CACHED";
      if (record.state === "CACHED" && record.distance > RETENTION_RADIUS_M) {
        // Retain the loaded asset in memory and loader cache; the explicit state records that it is outside the warm ring.
      }
      if (record.state === "ACTIVE") { visible.add(record.tile_id); active.add(record.tile_id); }
      if (record.state === "PRELOADING") preloading += 1;
      if (record.state === "CACHED" || record.state === "READY") cached += 1;
      if (record.state === "ERROR") errors += 1;
      if (record.requested_count) { bytes += record.size_bytes; requests += record.requested_count; }
      if (record.requested_count > 1) repeated += record.requested_count - 1;
    });
    refs.activeTileIds.current = active;
    setVisibleIds((previous) => previous.size === visible.size && [...visible].every((id) => previous.has(id)) ? previous : visible);
    const summary: RuntimeSummary = {
      active: active.size,
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
    if (!initialReadySent.current && active.size > 0 && preloading === 0) {
      initialReadySent.current = true;
      onInitialReady();
    }
  });

  return <>{mountedIds.map((id) => {
    const record = records.get(id)!;
    return <TileAsset key={id} record={record} visible={visibleIds.has(id)} refs={refs} materials={materials} quality={quality} onReady={markReady} />;
  })}</>;
}
