"use client";

import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { Component, Suspense, useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import { useEffect } from "react";
import type { DetailedAsset, EntityRecord, EnvironmentQuality, RuntimeRefs } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";
import { harmonizeScene } from "./visualSystem";
import { stability } from "./stability";

class LandmarkErrorBoundary extends Component<{ children: ReactNode; onError: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onError(); }
  render() { return this.state.failed ? null : this.props.children; }
}

function LandmarkAsset({ asset, visible, materials, quality, onReady }: { asset: DetailedAsset; visible: boolean; materials: BGCVisualMaterials; quality: EnvironmentQuality; onReady: (id: string) => void }) {
  const gltf = useGLTF(asset.url);
  useEffect(() => { harmonizeScene(gltf.scene, materials, quality, true); onReady(asset.entity_id); }, [gltf.scene, materials, quality, asset.entity_id, onReady]);
  return <primitive object={gltf.scene} visible={visible} />;
}

export function LandmarkLODManager({ assets, entities, refs, materials, quality, priorityAssetId, onActiveChange }: {
  assets: DetailedAsset[];
  entities: EntityRecord[];
  refs: RuntimeRefs;
  onActiveChange: (ids: string[]) => void;
  materials: BGCVisualMaterials;
  quality: EnvironmentQuality;
  priorityAssetId?: string | null;
}) {
  const entityByLod = useMemo(() => new Map(entities.filter((entity) => entity.detailed_asset_id).map((entity) => [entity.detailed_asset_id!, entity])), [entities]);
  const [mounted, setMounted] = useState<Set<string>>(new Set());
  const [active, setActive] = useState<Set<string>>(new Set());
  const [ready, setReady] = useState<Set<string>>(new Set());
  const readyIds = useRef(new Set<string>());
  const failed = useRef(new Set<string>());
  const gapIds = useRef(new Set<string>());
  const lastEvaluation = useRef(0);

  // eslint-disable-next-line react-hooks/preserve-manual-memoization -- tileScenes is a stable mutable scene registry.
  const setLod2Visible = useCallback((entityId: string, visible: boolean) => {
    let seen = 0;
    refs.tileScenes.current.forEach((scene) => scene.traverse((object) => {
      if (object.userData.detailed_asset_id === entityId) { object.visible = visible; seen += 1; }
    }));
    return seen;
  }, [refs.tileScenes]);

  const markReady = useCallback((id: string) => {
    if (readyIds.current.has(id)) return;
    readyIds.current.add(id);
    setReady(new Set(readyIds.current));
    stability.lod1_ready_count += 1;
  }, []);

  useEffect(() => {
    for (const asset of assets) setLod2Visible(asset.entity_id, !active.has(asset.entity_id));
  }, [active, assets, refs.tileScenes, setLod2Visible]);

  useEffect(() => {
    if (!priorityAssetId) return;
    const asset = assets.find((item) => item.entity_id === priorityAssetId);
    if (!asset || mounted.has(asset.entity_id) || failed.current.has(asset.entity_id)) return;
    useGLTF.preload(asset.url);
    stability.lod1_requests += 1;
    setMounted((current) => new Set([...current, asset.entity_id]));
  }, [assets, mounted, priorityAssetId]);

  useFrame(() => {
    const now = performance.now();
    if (now - lastEvaluation.current < 150) return;
    lastEvaluation.current = now;
    const nextMounted = new Set(mounted);
    const nextActive = new Set(active);
    for (const asset of assets) {
      const entity = entityByLod.get(asset.entity_id);
      if (!entity) continue;
      const ownerVisible = refs.visibleTileIds.current.has(entity.tile_id);
      if (ownerVisible && !nextMounted.has(asset.entity_id) && !failed.current.has(asset.entity_id)) {
        useGLTF.preload(asset.url);
        stability.lod1_requests += 1;
        nextMounted.add(asset.entity_id);
      }
      if (ownerVisible && ready.has(asset.entity_id) && !failed.current.has(asset.entity_id)) nextActive.add(asset.entity_id);
      else nextActive.delete(asset.entity_id);
    }
    const mountedChanged = nextMounted.size !== mounted.size;
    const activeChanged = nextActive.size !== active.size || [...nextActive].some((id) => !active.has(id));
    if (mountedChanged) setMounted(nextMounted);
    // Reapply when a newly loaded tile contributes a generic mesh after the LOD activated.
    assets.forEach((asset) => {
      const genericVisible = !(active.has(asset.entity_id) && nextActive.has(asset.entity_id));
      const seen = setLod2Visible(asset.entity_id, genericVisible);
      const entity = entityByLod.get(asset.entity_id);
      const gap = Boolean(entity && refs.visibleTileIds.current.has(entity.tile_id) && seen > 0 && !genericVisible && !(active.has(asset.entity_id) && ready.has(asset.entity_id)));
      if (gap && !gapIds.current.has(asset.entity_id)) { gapIds.current.add(asset.entity_id); stability.lod_handoff_gap_events += 1; }
      else if (!gap) gapIds.current.delete(asset.entity_id);
    });
    if (activeChanged) {
      setActive(nextActive);
      onActiveChange([...nextActive].sort());
    }
  });

  return <>{assets.filter((asset) => mounted.has(asset.entity_id)).map((asset) => (
    <LandmarkErrorBoundary key={asset.entity_id} onError={() => { failed.current.add(asset.entity_id); setLod2Visible(asset.entity_id, true); }}><Suspense fallback={null}><LandmarkAsset asset={asset} visible={active.has(asset.entity_id)} materials={materials} quality={quality} onReady={markReady} /></Suspense></LandmarkErrorBoundary>
  ))}</>;
}
