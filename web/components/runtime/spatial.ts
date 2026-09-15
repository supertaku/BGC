import type { Footprint, WorldTile } from "./types";

export const ACTIVE_RADIUS_M = 500;
export const DEACTIVATE_RADIUS_M = 650;
export const PRELOAD_RADIUS_M = 750;
export const RETENTION_RADIUS_M = 1000;
export const LOD1_ACTIVATE_RADIUS_M = 180;
export const LOD1_DEACTIVATE_RADIUS_M = 230;
export const LOD1_PRELOAD_RADIUS_M = 360;

export function distanceToTileBounds(x: number, z: number, tile: WorldTile) {
  const [minX, minNorth, maxX, maxNorth] = tile.bounds;
  const minZ = -maxNorth;
  const maxZ = -minNorth;
  const dx = Math.max(minX - x, 0, x - maxX);
  const dz = Math.max(minZ - z, 0, z - maxZ);
  return Math.hypot(dx, dz);
}

export function pointInRing(x: number, z: number, ring: [number, number][]) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i];
    const [xj, zj] = ring[j];
    const crosses = zi > z !== zj > z && x < ((xj - xi) * (z - zi)) / (zj - zi || Number.EPSILON) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

export function pointInFootprint(x: number, z: number, footprint: Footprint, margin = 0) {
  const [minX, minZ, maxX, maxZ] = footprint.bounds;
  if (x < minX - margin || x > maxX + margin || z < minZ - margin || z > maxZ + margin) return false;
  return footprint.rings.some((ring) => pointInRing(x, z, ring));
}

export function findFootprintAt(x: number, z: number, footprints: Footprint[]) {
  return footprints
    .filter((footprint) => pointInFootprint(x, z, footprint))
    .sort((a, b) => (a.bounds[2] - a.bounds[0]) * (a.bounds[3] - a.bounds[1]) - (b.bounds[2] - b.bounds[0]) * (b.bounds[3] - b.bounds[1]))[0] ?? null;
}
