import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const bytes = await readFile(resolve(process.argv[2] ?? "../exports/glb/tests/gpu-instancing.glb"));
const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
const gltf = await new GLTFLoader().parseAsync(data, "");
const meshes = [];
gltf.scene.traverse((object) => { if (object.isMesh) meshes.push(object); });
const instancedMeshes = meshes.filter((object) => object.isInstancedMesh);
const uniqueGeometries = new Set(meshes.map((object) => object.geometry.uuid));
if (meshes.length !== 3 || instancedMeshes.length !== 0 || uniqueGeometries.size !== 1) {
  throw new Error(`METADATA_ERROR: unexpected linked-duplicate import meshes=${meshes.length} instanced=${instancedMeshes.length} geometries=${uniqueGeometries.size}`);
}
console.log(JSON.stringify({ status: "PASS", outcome: "CORE_GLTF_SHARED_MESH_ONLY", meshObjects: 3, uniqueGeometries: 1, instancedMeshes: 0 }));
