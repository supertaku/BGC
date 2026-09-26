"use client";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import heights from "./surface-heights.generated.json";
import type { Surface, Tile } from "./publicRealmData";
import type { BGCVisualMaterials } from "./visualSystem";
function shapeGeometry(surface: Surface): THREE.BufferGeometry {
  const elevation = heights[`${surface.base_surface}_TOP`] + surface.elevation_offset_m;
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

function mergedSurfaces(surfaces: Surface[]) {
  const parts = surfaces.map((surface) => shapeGeometry(surface));
  if (!parts.length) return null;
  // ShapeGeometry is indexed; merge once per tile and material to bound draw calls.
  const merged = mergeGeometries(parts);
  parts.forEach((part) => part.dispose());
  return merged;
}

export function SurfaceDetailLayer({ tiles, materials }: {tiles: Tile[]; materials: BGCVisualMaterials}) {
 const surfaces=useMemo(()=>tiles.flatMap(tile=>Object.entries(tile.surfaces).map(([type,items])=>({type,geometry:mergedSurfaces(items)}))),[tiles]);
 useEffect(()=>()=>surfaces.forEach(s=>s.geometry?.dispose()),[surfaces]);
 const mapping: Record<string,THREE.Material>={PAVING_BORDER:materials.BGC_STONE_WARM,PARK_EDGE:materials.BGC_STONE_WARM,ZEBRA_CROSSING:materials.BGC_CONCRETE_LIGHT};
 return <>{surfaces.map((s,i)=><mesh key={i} geometry={s.geometry!} material={mapping[s.type]} dispose={null}/>)}</>;
}
