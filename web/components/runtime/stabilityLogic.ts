import { ACTIVE_RADIUS_M, DEACTIVATE_RADIUS_M, PRELOAD_RADIUS_M, distanceToTileBounds } from "./spatial.ts";
import type { WorldTile } from "./types.ts";

export type StreamAnchor = { x: number; z: number; role: "PRIMARY" | "SECONDARY" };
export type BoundsXZ = [number, number, number, number];

export function worldBounds(tiles: WorldTile[]): BoundsXZ {
  if (!tiles.length) throw new Error("World has no tiles");
  return [Math.min(...tiles.map((t) => t.bounds[0])), -Math.max(...tiles.map((t) => t.bounds[3])), Math.max(...tiles.map((t) => t.bounds[2])), -Math.min(...tiles.map((t) => t.bounds[1]))];
}

export function clampMapTarget(x: number, z: number, bounds: BoundsXZ, padding = 350): [number, number] {
  return [Math.max(bounds[0] - padding, Math.min(bounds[2] + padding, x)), Math.max(bounds[1] - padding, Math.min(bounds[3] + padding, z))];
}

export function resolveStreamAnchors(mode: "INSPECT" | "WALK" | "TOUR", target: [number, number], camera: [number, number], priority?: [number, number] | null): StreamAnchor[] {
  if (mode === "WALK") return [{ x: camera[0], z: camera[1], role: "PRIMARY" }];
  const primary = priority ?? target;
  const anchors: StreamAnchor[] = [{ x: primary[0], z: primary[1], role: "PRIMARY" }];
  if (Math.hypot(primary[0] - camera[0], primary[1] - camera[1]) < 650) anchors.push({ x: camera[0], z: camera[1], role: "SECONDARY" });
  return anchors;
}

export function streamDistance(tile: WorldTile, anchors: StreamAnchor[]) {
  return Math.min(...anchors.map((anchor) => distanceToTileBounds(anchor.x, anchor.z, tile)));
}

export function computeDesiredTiles(tiles: WorldTile[], anchors: StreamAnchor[]) {
  return new Set(tiles.filter((tile) => streamDistance(tile, anchors) <= ACTIVE_RADIUS_M).map((tile) => tile.tile_id));
}

export function shouldRequestTile(distance: number) { return distance <= PRELOAD_RADIUS_M; }
export function shouldKeepActive(distance: number) { return distance <= DEACTIVATE_RADIUS_M; }

export function resolveVisibleTileSet(desired: Set<string>, ready: Set<string>, previous: Set<string>, allLoaded = false) {
  const candidates = new Set([...ready].filter((id) => allLoaded || desired.has(id)));
  return candidates.size ? candidates : new Set(previous);
}

export function shouldShowLOD1(desired: boolean, ready: boolean) { return desired && ready; }
export function shouldShowLOD2(desired: boolean, ready: boolean) { return !shouldShowLOD1(desired, ready); }
export function acceptFocusSequence(previous: number | null, next: number | null) { return next !== null && next !== previous ? next : null; }
export function isPrimarySelection(button: number, distancePx: number) { return button === 0 && distancePx <= 5; }

export function fitCameraToBounds(bounds: BoundsXZ, verticalFovDeg: number, aspect: number, azimuth = 0, pitch = 1.05, margin = 1.16) {
  const [minX, minZ, maxX, maxZ] = bounds;
  const target: [number, number, number] = [(minX + maxX) / 2, 100, (minZ + maxZ) / 2];
  const direction: [number, number, number] = [Math.cos(pitch) * Math.cos(azimuth), Math.sin(pitch), Math.cos(pitch) * Math.sin(azimuth)];
  const distance = fitDistance(bounds, 0, 250, target, direction, verticalFovDeg, aspect, margin);
  const position: [number, number, number] = [target[0] + distance * direction[0], target[1] + distance * direction[1], target[2] + distance * direction[2]];
  return { position, target, distance };
}

export function fitCameraToEntity(bounds: BoundsXZ, height: number | null, verticalFovDeg: number, aspect: number, margin = 1.25) {
  const h = Math.max(12, height ?? 20);
  const target: [number, number, number] = [(bounds[0] + bounds[2]) / 2, h / 2, (bounds[1] + bounds[3]) / 2];
  const direction = normalized([0.58, 0.55, 0.60]);
  const distance = Math.max(30, fitDistance(bounds, 0, h, target, direction, verticalFovDeg, aspect, margin));
  const position: [number, number, number] = [target[0] + distance * direction[0], target[1] + distance * direction[1], target[2] + distance * direction[2]];
  return { position, target, distance };
}

function normalized(v: [number, number, number]): [number, number, number] {
  const length = Math.hypot(...v);
  return [v[0] / length, v[1] / length, v[2] / length];
}

function fitDistance(bounds: BoundsXZ, minY: number, maxY: number, target: [number, number, number], direction: [number, number, number], verticalFovDeg: number, aspect: number, margin: number) {
  const right = normalized([-direction[2], 0, direction[0]]);
  const up: [number, number, number] = [right[1] * direction[2] - right[2] * direction[1], right[2] * direction[0] - right[0] * direction[2], right[0] * direction[1] - right[1] * direction[0]];
  const tanV = Math.tan(verticalFovDeg * Math.PI / 360);
  const tanH = tanV * Math.max(aspect, 0.1);
  let required = 0;
  for (const x of [bounds[0], bounds[2]]) for (const y of [minY, maxY]) for (const z of [bounds[1], bounds[3]]) {
    const point: [number, number, number] = [x - target[0], y - target[1], z - target[2]];
    const dot = (a: [number, number, number], b: [number, number, number]) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    required = Math.max(required, dot(point, direction) + Math.max(Math.abs(dot(point, right)) / tanH, Math.abs(dot(point, up)) / tanV));
  }
  return Math.max(1, required * margin);
}
