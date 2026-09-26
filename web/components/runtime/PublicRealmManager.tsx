"use client";

import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import detail from "./visual-detail.json";
import type { EnvironmentQuality } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";

type Ring = [number, number][];
type Surface = { outer: Ring; holes: Ring[] };
type Instance = { id: string; position: [number, number]; grounding: string };
type Tile = { surfaces: Record<string, Surface[]>; instances: Record<string, Instance[]> };
const tiles = detail.tiles as unknown as Record<string, Tile>;

function shapeGeometry(surface: Surface, elevation: number): THREE.BufferGeometry {
  const shape = new THREE.Shape();
  surface.outer.forEach(([x, z], index) => index ? shape.lineTo(x, z) : shape.moveTo(x, z));
  for (const ring of surface.holes) {
    const hole = new THREE.Path();
    ring.forEach(([x, z], index) => index ? hole.lineTo(x, z) : hole.moveTo(x, z));
    shape.holes.push(hole);
  }
  const geometry = new THREE.ShapeGeometry(shape);
  geometry.rotateX(-Math.PI / 2);
  geometry.translate(0, elevation, 0);
  return geometry;
}

function mergedSurfaces(surfaces: Surface[], elevation: number) {
  const parts = surfaces.map((surface) => shapeGeometry(surface, elevation));
  if (!parts.length) return null;
  // ShapeGeometry is indexed; merge once per tile and material to bound draw calls.
  const merged = mergeGeometries(parts);
  parts.forEach((part) => part.dispose());
  return merged;
}

function furnitureGeometry(type: string): THREE.BufferGeometry {
  if (type === "TREE_CLUSTER") {
    const trunk = new THREE.CylinderGeometry(.19, .28, 2.2, 6).translate(0, 1.1, 0).toNonIndexed();
    const canopy = new THREE.IcosahedronGeometry(1.85, 0).scale(1, 1.15, 1).translate(0, 3.5, 0).toNonIndexed();
    const merged = mergeGeometries([trunk, canopy], true);
    trunk.dispose(); canopy.dispose();
    if (!merged) throw new Error("Unable to build tree geometry");
    return merged;
  }
  if (type === "PLANTER_RECT") return new THREE.BoxGeometry(2.8, .45, 1.15).translate(0, .225, 0);
  if (type === "BENCH_LINEAR") return new THREE.BoxGeometry(2, .32, .6).translate(0, .48, 0);
  return new THREE.CylinderGeometry(.09, .15, 5, 6).translate(0, 2.5, 0);
}

function InstanceBatch({ items, geometry, material }: { items: Instance[]; geometry: THREE.BufferGeometry; material: THREE.Material | THREE.Material[] }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const object = new THREE.Object3D();
    items.forEach((item, index) => {
      object.position.set(item.position[0], 0, item.position[1]);
      object.rotation.y = (item.id.length % 7) * Math.PI / 7;
      object.updateMatrix();
      ref.current!.setMatrixAt(index, object.matrix);
    });
    ref.current.instanceMatrix.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [items]);
  return <instancedMesh ref={ref} args={[geometry, material, items.length]} dispose={null} />;
}

type Props = { activeIds: string[]; quality: EnvironmentQuality; materials: BGCVisualMaterials };

function PublicRealmLayer({ activeIds, quality, materials }: Props) {
  const diagnostic = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("detail") : null;
  const disabled = diagnostic === "0";
  const detailTileKey = quality === "LEGACY" || disabled ? "" : activeIds.filter((id) => id in tiles).join("|");
  const selected = useMemo(() => detailTileKey ? detailTileKey.split("|").map((id) => [id, tiles[id]] as const) : [], [detailTileKey]);
  const selectedIds = new Set(selected.map(([id]) => id));
  const surfaces = useMemo(() => Object.entries(tiles).flatMap(([id, tile]) => Object.entries(tile.surfaces).map(([type, polygons]) => ({ id, type, geometry: mergedSurfaces(polygons, type === "ZEBRA_CROSSING" ? .047 : .035) })).filter((entry) => entry.geometry)), []);
  useEffect(() => () => surfaces.forEach((surface) => surface.geometry?.dispose()), [surfaces]);
  const library = useMemo(() => ({
    TREE_CLUSTER: furnitureGeometry("TREE_CLUSTER"),
    PLANTER_RECT: furnitureGeometry("PLANTER_RECT"),
    BENCH_LINEAR: furnitureGeometry("BENCH_LINEAR"),
    LIGHT_POLE_STANDARD: furnitureGeometry("LIGHT_POLE_STANDARD"),
  }), []);
  useEffect(() => () => Object.values(library).forEach((geometry) => geometry.dispose()), [library]);
  const instances = useMemo(() => {
    const groups: Record<string, Instance[]> = {};
    for (const [, tile] of selected) for (const [type, items] of Object.entries(tile.instances)) (groups[type] ??= []).push(...items);
    return groups;
  }, [selected]);
  const surfaceMaterial: Record<string, THREE.Material> = {
    PAVING_BORDER: materials.BGC_STONE_WARM,
    ZEBRA_CROSSING: materials.BGC_CONCRETE_LIGHT,
    PARK_EDGE: materials.BGC_STONE_WARM,
  };
  const furnitureMaterial: Record<string, THREE.Material | THREE.Material[]> = {
    TREE_CLUSTER: [materials.BGC_SOIL, materials.BGC_GRASS],
    PLANTER_RECT: materials.BGC_STONE_WARM,
    BENCH_LINEAR: materials.BGC_STONE_WARM,
    LIGHT_POLE_STANDARD: materials.BGC_METAL_DARK,
  };
  return <>
    {diagnostic !== "instances" ? surfaces.filter(({ id }) => selectedIds.has(id)).map(({ id, type, geometry }, index) => <mesh key={`${id}:${type}:${index}`} geometry={geometry!} material={surfaceMaterial[type]} />) : null}
    {diagnostic !== "surfaces" ? Object.entries(instances).map(([type, items]) => <InstanceBatch key={type} items={items} geometry={library[type as keyof typeof library]} material={furnitureMaterial[type]} />) : null}
  </>;
}

// Promotion is deliberately separate from implementation. Walking measurements
// are currently unstable; the production LOW baseline must remain unchanged.
export function PublicRealmManager(props: Props) {
  const mode = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("detail") : null;
  if (props.quality === "LEGACY" || !["1", "surfaces", "instances"].includes(mode ?? "")) return null;
  return <PublicRealmLayer {...props} />;
}
