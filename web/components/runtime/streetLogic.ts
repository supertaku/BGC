import type { NamedWaySegment } from "./types.ts";

export type NearestWay = { way: NamedWaySegment; distance_m: number };

export function distancePointToSegment2D(point: [number, number], a: [number, number], b: [number, number]): number {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const lengthSq = dx * dx + dz * dz;
  const t = lengthSq ? Math.max(0, Math.min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dz) / lengthSq)) : 0;
  return Math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dz);
}

export function distancePointToPolyline(point: [number, number], points: [number, number][]): number {
  let distance = Infinity;
  for (let i = 1; i < points.length; i++) distance = Math.min(distance, distancePointToSegment2D(point, points[i - 1], points[i]));
  return distance;
}

export function entryRadius(way: NamedWaySegment): number {
  return Math.min(30, Math.max(way.kind === "ROAD" ? 14 : 8, (way.width_m ?? 0) / 2 + (way.kind === "ROAD" ? 8 : 6)));
}

export function findNearestNamedWay(point: [number, number], candidates: NamedWaySegment[]): NearestWay | null {
  let best: NearestWay | null = null;
  for (const way of candidates) {
    const distance_m = distancePointToPolyline(point, way.points);
    if (distance_m > entryRadius(way)) continue;
    if (!best || distance_m < best.distance_m || (distance_m === best.distance_m && way.id < best.way.id)) best = { way, distance_m };
  }
  return best;
}

export function chooseStableWay(point: [number, number], candidates: NamedWaySegment[], currentId: string | null): NearestWay | null {
  const best = findNearestNamedWay(point, candidates);
  if (!currentId) return best;
  const current = candidates.filter((way) => way.id === currentId)
    .map((way) => ({ way, distance_m: distancePointToPolyline(point, way.points) }))
    .sort((a, b) => a.distance_m - b.distance_m)[0];
  if (!current || current.distance_m > entryRadius(current.way) + 5) return best;
  if (!best || best.way.id === currentId || current.distance_m - best.distance_m < 4) return current;
  return best;
}
