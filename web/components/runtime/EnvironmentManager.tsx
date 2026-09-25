"use client";

import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { EnvironmentAssetType, EnvironmentInstance, EnvironmentQuality, RuntimeRefs } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";

type LibraryEntry = { geometry: THREE.BufferGeometry; material: THREE.Material | THREE.Material[]; elevation: number; scale: [number, number, number] };

function hash(id: string) {
  let value = 2166136261;
  for (let index = 0; index < id.length; index += 1) value = Math.imul(value ^ id.charCodeAt(index), 16777619);
  return value >>> 0;
}

function treeScale(id: string) { return .88 + (hash(id) % 25) / 100; }

function treeGeometry(variant: number) {
  const trunk = new THREE.CylinderGeometry(.25, .38, 2.4, 6).translate(0, 1.2, 0);
  const crown = variant === 0
    ? new THREE.ConeGeometry(2.15, 4.8, 7).translate(0, 4.4, 0)
    : variant === 1
      ? new THREE.DodecahedronGeometry(2.25, 0).scale(1, 1.25, 1).translate(0, 4.5, 0)
      : new THREE.SphereGeometry(2.15, 7, 5).scale(1.15, 1, .95).translate(0, 4.35, 0);
  // The polyhedral crown is non-indexed while cylinders and spheres are indexed.
  // Normalize before merging so all three tree variants remain valid geometries.
  const trunkNonIndexed = trunk.toNonIndexed();
  const crownNonIndexed = crown.index ? crown.toNonIndexed() : crown.clone();
  const geometry = mergeGeometries([trunkNonIndexed, crownNonIndexed], true);
  trunk.dispose();
  crown.dispose();
  trunkNonIndexed.dispose();
  crownNonIndexed.dispose();
  if (!geometry) throw new Error(`Failed to merge tree geometry variant ${variant}`);
  return geometry;
}

function InstanceGroup({ items, entry, castShadow, isTree }: { items: EnvironmentInstance[]; entry: LibraryEntry; castShadow: boolean; isTree: boolean }) {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  useLayoutEffect(() => {
    if (!mesh.current) return;
    items.forEach((item, index) => {
      const scale = isTree ? treeScale(item.id) : 1;
      dummy.position.set(item.position[0], entry.elevation * scale, item.position[1]);
      dummy.rotation.set(0, isTree ? (hash(item.id) % 360) * Math.PI / 180 : 0, 0);
      dummy.scale.set(entry.scale[0] * scale, entry.scale[1] * scale, entry.scale[2] * scale);
      dummy.updateMatrix();
      mesh.current!.setMatrixAt(index, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    mesh.current.computeBoundingSphere();
  }, [dummy, entry, items, isTree]);
  return <instancedMesh ref={mesh} args={[entry.geometry, entry.material, items.length]} dispose={null} castShadow={castShadow} receiveShadow={castShadow} />;
}

export function EnvironmentManager({ activeIds, quality, refs, materials, onGroupCount }: {
  activeIds: string[];
  quality: EnvironmentQuality;
  refs: RuntimeRefs;
  materials: BGCVisualMaterials;
  onGroupCount: (count: number) => void;
}) {
  const library = useMemo<Record<string, LibraryEntry>>(() => ({
    TREE_A: { geometry: treeGeometry(0), material: [materials.BGC_SOIL, materials.BGC_GRASS], elevation: 0, scale: [1, 1, 1] },
    TREE_B: { geometry: treeGeometry(1), material: [materials.BGC_SOIL, materials.BGC_GRASS], elevation: 0, scale: [.95, 1.05, .95] },
    TREE_C: { geometry: treeGeometry(2), material: [materials.BGC_SOIL, materials.BGC_GRASS], elevation: 0, scale: [1.05, .92, 1.05] },
    STREET_LAMP_GENERIC: { geometry: new THREE.CylinderGeometry(.11, .18, 5.8, 7), material: materials.BGC_METAL_DARK, elevation: 2.9, scale: [1, 1, 1] },
    BENCH_GENERIC: { geometry: new THREE.BoxGeometry(2.1, .45, .65), material: materials.BGC_STONE_WARM, elevation: .55, scale: [1, 1, 1] },
    BOLLARD_GENERIC: { geometry: new THREE.CylinderGeometry(.13, .18, .9, 7), material: materials.BGC_METAL_DARK, elevation: .45, scale: [1, 1, 1] },
    WASTE_BIN_GENERIC: { geometry: new THREE.CylinderGeometry(.34, .4, 1.05, 8), material: materials.BGC_METAL_DARK, elevation: .53, scale: [1, 1, 1] },
    SHELTER_GENERIC: { geometry: new THREE.BoxGeometry(3.8, 2.5, 1.5), material: materials.BGC_GLASS_LIGHT, elevation: 1.25, scale: [1, 1, 1] },
  }), [materials]);
  useEffect(() => () => Object.values(library).forEach((entry) => entry.geometry.dispose()), [library]);

  const groups = useMemo(() => {
    if (quality === "LEGACY") return [];
    const pooled = new Map<string, EnvironmentInstance[]>();
    const allowed = quality === "LOW" ? new Set<EnvironmentAssetType>(["TREE_GENERIC", "STREET_LAMP_GENERIC"]) : null;
    for (const tileId of activeIds) {
      const environment = refs.sidecars.current.get(tileId)?.environment ?? {};
      for (const [type, items] of Object.entries(environment) as [EnvironmentAssetType, EnvironmentInstance[]][]) {
        if (allowed && !allowed.has(type)) continue;
        for (const item of items) {
          const key = type === "TREE_GENERIC" ? `TREE_${String.fromCharCode(65 + hash(item.id) % 3)}` : type;
          const group = pooled.get(key) ?? [];
          group.push(item);
          pooled.set(key, group);
        }
      }
    }
    return [...pooled.entries()].filter(([, items]) => items.length).map(([key, items]) => ({ key, items, entry: library[key] }));
  }, [activeIds, library, quality, refs.sidecars]);
  useEffect(() => onGroupCount(groups.length), [groups.length, onGroupCount]);
  return <>{groups.map((group) => <InstanceGroup key={group.key} items={group.items} entry={group.entry} isTree={group.key.startsWith("TREE_")} castShadow={quality === "FULL" && group.key.startsWith("TREE_")} />)}</>;
}
