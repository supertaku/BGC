import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const input = resolve(process.argv[2] ?? "../exports/glb/buildings/bgc_building_0014_lod1.glb");
const bytes = await readFile(input);
const arrayBuffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
const gltf = await new GLTFLoader().parseAsync(arrayBuffer, "");
const records = [];
gltf.scene.traverse((object) => {
  if (object.userData.entity_id && object.userData.component_id) records.push({ name: object.name, ...object.userData });
});
if (!records.length) throw new Error("METADATA_ERROR: no glTF extras reached Three.js userData");
for (const record of records) {
  for (const key of ["entity_id", "component_id", "component_type", "evidence_status", "observation_ids", "reconstruction_fidelity"]) {
    if (record[key] === undefined) throw new Error(`METADATA_ERROR: ${record.name} missing ${key}`);
  }
}
if (new Set(records.map((item) => item.entity_id)).size !== 1) throw new Error("METADATA_ERROR: multiple entity IDs");
console.log(JSON.stringify({ status: "PASS", entity_id: records[0].entity_id, nodes_with_metadata: records.length }));
