import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { placeSlugs, searchPlaces } from "../components/product/placeState.ts";

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
console.log(`Product state: ${slugs.size} unique place links, ${data.lod1_entity_ids.length} tour stops, search cases PASS`);
