"use client";

import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useCallback, useMemo, useRef, useState } from "react";
import { LOD1_ACTIVATE_RADIUS_M, LOD1_DEACTIVATE_RADIUS_M, LOD1_PRELOAD_RADIUS_M } from "./spatial";
import { useEffect } from "react";
import type { DetailedAsset, EntityRecord, EnvironmentQuality, RuntimeRefs } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";
import { harmonizeScene } from "./visualSystem";

function LandmarkAsset({ asset, visible, materials, quality }: { asset: DetailedAsset; visible: boolean; materials: BGCVisualMaterials; quality: EnvironmentQuality }) {
  const gltf = useGLTF(asset.url);
  useEffect(() => harmonizeScene(gltf.scene, materials, quality, true), [gltf.scene, materials, quality]);
  return <primitive object={gltf.scene} visible={visible} />;
}

export function LandmarkLODManager({ assets, entities, refs, materials, quality, onActiveChange }: {
  assets: DetailedAsset[];
  entities: EntityRecord[];
  refs: RuntimeRefs;
  onActiveChange: (ids: string[]) => void;
  materials: BGCVisualMaterials;
  quality: EnvironmentQuality;
}) {
  const entityByLod = useMemo(() => new Map(entities.filter((entity) => entity.detailed_asset_id).map((entity) => [entity.detailed_asset_id!, entity])), [entities]);
  const [mounted, setMounted] = useState<Set<string>>(new Set());
  const [active, setActive] = useState<Set<string>>(new Set());
  const lastEvaluation = useRef(0);

  const setLod2Visible = useCallback((entityId: string, visible: boolean) => {
    refs.tileScenes.current.forEach((scene) => scene.traverse((object) => {
      if (object.userData.detailed_asset_id === entityId) object.visible = visible;
    }));
  }, [refs.tileScenes]);

  useFrame(() => {
    const now = performance.now();
    if (now - lastEvaluation.current < 150) return;
    lastEvaluation.current = now;
    const nextMounted = new Set(mounted);
    const nextActive = new Set(active);
    for (const asset of assets) {
      const entity = entityByLod.get(asset.entity_id);
      if (!entity) continue;
      const distance = Math.hypot(refs.focus.current.x - entity.center[0], refs.focus.current.z - entity.center[1]);
      if (distance <= LOD1_PRELOAD_RADIUS_M && !nextMounted.has(asset.entity_id)) {
        useGLTF.preload(asset.url);
        nextMounted.add(asset.entity_id);
      }
      if (distance <= LOD1_ACTIVATE_RADIUS_M) nextActive.add(asset.entity_id);
      else if (distance > LOD1_DEACTIVATE_RADIUS_M) nextActive.delete(asset.entity_id);
    }
    const mountedChanged = nextMounted.size !== mounted.size;
    const activeChanged = nextActive.size !== active.size || [...nextActive].some((id) => !active.has(id));
    if (mountedChanged) setMounted(nextMounted);
    assets.forEach((asset) => setLod2Visible(asset.entity_id, !nextActive.has(asset.entity_id)));
    if (activeChanged) {
      setActive(nextActive);
      onActiveChange([...nextActive].sort());
    }
  });

  return <>{assets.filter((asset) => mounted.has(asset.entity_id)).map((asset) => (
    <LandmarkAsset key={asset.entity_id} asset={asset} visible={active.has(asset.entity_id)} materials={materials} quality={quality} />
  ))}</>;
}
