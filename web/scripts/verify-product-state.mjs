import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { placeSlugs, searchPlaces } from "../components/product/placeState.ts";
import { resolveUrlState } from "../components/product/urlState.ts";
import { acceptFocusSequence, clampMapTarget, computeDesiredTiles, fitCameraToBounds, fitCameraToEntity, isPrimarySelection, resolveStreamAnchors, resolveVisibleTileSet, shouldShowLOD1, shouldShowLOD2, streamDistance, worldBounds } from "../components/runtime/stabilityLogic.ts";

const data = JSON.parse(readFileSync(new URL("../public/world/bgc-interactive.json", import.meta.url), "utf8"));
const slugs = placeSlugs(data.entities);
assert.equal(data.entities.length, 263);
assert.equal(slugs.size, data.entities.filter((entity) => entity.name).length);
assert.equal(new Set(slugs.values()).size, slugs.size, "duplicate names need unique URLs");
const central = searchPlaces(data.entities, "CeNtRaL   Square");
assert.equal(central[0]?.name, "Central Square");
assert.equal(slugs.get(central[0].entity_id), "central-square");
assert.equal(searchPlaces(data.entities, "SNR")[0]?.name, "S&R Membership Shopping");
assert.equal(searchPlaces(data.entities, "central")[0]?.name, "Central Square");
assert.equal(searchPlaces(data.entities, "square")[0]?.name, "Central Square");
assert.deepEqual(searchPlaces(data.entities, "no such named place 999"), []);
for (const id of data.lod1_entity_ids) assert(data.entities.some((entity) => entity.detailed_asset_id === id), `Tour stop ${id} is missing`);
const state = (query) => resolveUrlState(new URLSearchParams(query), data.entities, data.lod1_entity_ids);
assert.equal(state("debug=1&navigation=WALK").navigation, "WALK");
assert.equal(state("debug=1&navigation=INSPECT&tour=bgc-landmarks").navigation, "INSPECT");
assert.equal(state("mode=walk").navigation, "WALK");
assert.equal(state("tour=bgc-landmarks").navigation, "TOUR");
assert.equal(state("tour=invalid").navigation, "INSPECT");
assert.equal(state("tour=invalid").invalidTour, true);
assert.equal(state("place=central-square").selectedEntity?.name, "Central Square");
assert.equal(state("place=central-square&mode=walk").navigation, "WALK");
assert.equal(state("place=central-square&mode=walk").selectedEntity?.name, "Central Square");
assert.equal(state("benchmark=1&navigation=WALK&benchmark_walk=1").navigation, "WALK");
assert.equal(state("debug=1&quality=FULL").quality, "LOW");
assert.equal(state("debug=1&quality=FULL&benchmark=1").quality, "FULL");
console.log(`Product state: ${slugs.size} unique place links, ${data.lod1_entity_ids.length} tour stops, search cases PASS`);

const world = JSON.parse(readFileSync(new URL("../public/world/bgc-world.json", import.meta.url), "utf8"));
const bounds = worldBounds(world.tiles);
assert.deepEqual(clampMapTarget(0, 0, bounds), [0, 0]);
assert.equal(clampMapTarget(bounds[0] - 1000, 0, bounds)[0], bounds[0] - 350);
assert.equal(clampMapTarget(bounds[2] + 1000, 0, bounds)[0], bounds[2] + 350);
assert.equal(clampMapTarget(0, bounds[1] - 1000, bounds)[1], bounds[1] - 350);
assert.equal(clampMapTarget(0, bounds[3] + 1000, bounds)[1], bounds[3] + 350);
assert.deepEqual(clampMapTarget(bounds[2] + 1000, bounds[3] + 1000, bounds), [bounds[2] + 350, bounds[3] + 350]);
for (const aspect of [2, 1, 0.5]) {
  const fit = fitCameraToBounds(bounds, 48, aspect);
  assert(Number.isFinite(fit.distance) && fit.distance > 0);
  assert(fit.position.every(Number.isFinite));
  const direction = fit.position.map((value, index) => (value - fit.target[index]) / fit.distance);
  const right = [-direction[2], 0, direction[0]];
  const up = [-right[2] * direction[1], right[2] * direction[0] - right[0] * direction[2], right[0] * direction[1]];
  const dot = (a, b) => a.reduce((sum, value, index) => sum + value * b[index], 0);
  for (const x of [bounds[0], bounds[2]]) for (const y of [0, 250]) for (const z of [bounds[1], bounds[3]]) {
    const corner = [x - fit.target[0], y - fit.target[1], z - fit.target[2]];
    const depth = fit.distance - dot(corner, direction);
    assert(depth > 0);
    assert(Math.abs(dot(corner, up)) / depth <= Math.tan(48 * Math.PI / 360));
    assert(Math.abs(dot(corner, right)) / depth <= Math.tan(48 * Math.PI / 360) * aspect);
  }
}
assert(fitCameraToBounds([-10, -10, 10, 10], 48, 1).distance > 0);
const examples = [
  [[0, 0, 12, 12], 12], [[0, 0, 120, 70], 18], [[0, 0, 40, 40], 80],
  [[0, 0, 45, 45], 220], [[0, 0, 160, 120], 200],
];
const fits = examples.map(([entityBounds, height]) => fitCameraToEntity(entityBounds, height, 48, 16 / 9));
assert(fits.every((fit) => Number.isFinite(fit.distance) && fit.distance > 0));
assert(fits[4].distance > fits[0].distance);
assert.deepEqual(resolveStreamAnchors("WALK", [0, 0], [500, 500]), [{ x: 500, z: 500, role: "PRIMARY" }]);
assert.equal(resolveStreamAnchors("INSPECT", [0, 0], [2000, 2000]).length, 1);
assert.equal(resolveStreamAnchors("INSPECT", [0, 0], [100, 100]).length, 2);
assert.equal(resolveStreamAnchors("TOUR", [0, 0], [100, 100], [300, 300])[0].x, 300);
assert.equal(isPrimarySelection(2, 0), false);
assert.equal(isPrimarySelection(0, 6), false);
assert.equal(isPrimarySelection(0, 4), true);
assert.equal(acceptFocusSequence(null, 1), 1);
assert.equal(acceptFocusSequence(1, 1), null);
assert.equal(acceptFocusSequence(1, 2), 2);
for (const id of data.lod1_entity_ids) {
  assert(world.detailed_assets.some((asset) => asset.entity_id === id));
  assert.equal(shouldShowLOD1(true, false), false, id);
  assert.equal(shouldShowLOD2(true, false), true, id);
  assert.equal(shouldShowLOD1(true, true), true, id);
  assert.equal(shouldShowLOD2(true, true), false, id);
  assert.equal(shouldShowLOD2(false, true), true, id);
}
const waypoints = [
  [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
  [0, bounds[1]], [0, bounds[3]], [bounds[0], 0], [bounds[2], 0], [0, 0],
];
const requested = new Set();
const ready = new Set();
let visible = new Set();
let zeroVisibleEvents = 0;
for (const [x, z] of waypoints) {
  const anchors = resolveStreamAnchors("INSPECT", [x, z], [x, z]);
  const desired = computeDesiredTiles(world.tiles, anchors);
  assert(desired.size > 0);
  for (const tile of world.tiles) if (streamDistance(tile, anchors) <= 750) requested.add(tile.tile_id);
  visible = resolveVisibleTileSet(desired, ready, visible);
  if (ready.size && !visible.size) zeroVisibleEvents++;
  for (const id of requested) ready.add(id);
  visible = resolveVisibleTileSet(desired, ready, visible);
  if (!visible.size) zeroVisibleEvents++;
}
assert.equal(zeroVisibleEvents, 0);
assert(requested.size < world.tiles.length, "streaming must not request every tile");
assert.equal(resolveVisibleTileSet(new Set(["new"]), new Set(["old"]), new Set(["old"])).has("old"), true);
assert.equal(resolveVisibleTileSet(new Set(["new"]), new Set(["new", "old"]), new Set(["old"])).has("old"), false);
console.log(`M19D pure runtime checks: ${world.tiles.length} tiles, ${requested.size} requested, ${zeroVisibleEvents} simulated zero-visible events, ${data.lod1_entity_ids.length} LOD handoffs PASS`);
