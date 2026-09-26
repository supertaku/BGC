import { readFile, stat } from "node:fs/promises";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const publicRoot = resolve(webRoot, "public");
const deploymentExtensions = new Set([
  ".glb",
  ".json",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".svg",
]);

const entrypoints = [
  "/world/bgc-world.json",
  "/world/bgc-interactive.json",
  "/world/detail/high-street-public-realm.json",
  "/world/detail/m23/catalog.json",
  "/world/detail/m23/tile-variants.json",
  "/world/detail/m23r/tile-variants.json",
  "/world/detail/m23r/benchmark-routes.json",
];

const pending = entrypoints.map((url) => ({ url, referencedBy: "runtime entrypoint" }));
const checked = new Map();
const missing = [];
const invalidJson = [];

function localAssetUrl(value) {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) return null;
  if (value.includes("{") || value.includes("}")) return null;
  const path = value.split(/[?#]/, 1)[0];
  const extension = path.slice(path.lastIndexOf(".")).toLowerCase();
  return deploymentExtensions.has(extension) ? path : null;
}

function collectAssetUrls(value, output) {
  if (typeof value === "string") {
    const url = localAssetUrl(value);
    if (url) output.add(url);
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectAssetUrls(item, output);
    return;
  }
  if (value && typeof value === "object") {
    for (const item of Object.values(value)) collectAssetUrls(item, output);
  }
}

function publicPathFor(url) {
  const path = resolve(publicRoot, `.${url}`);
  if (path !== publicRoot && !path.startsWith(`${publicRoot}${sep}`)) {
    throw new Error(`Asset URL escapes web/public: ${url}`);
  }
  return path;
}

while (pending.length > 0) {
  const item = pending.shift();
  if (checked.has(item.url)) continue;

  const expectedPath = publicPathFor(item.url);
  try {
    const file = await stat(expectedPath);
    if (!file.isFile()) throw new Error("not a file");
    checked.set(item.url, expectedPath);
  } catch {
    missing.push({ ...item, expectedPath });
    continue;
  }

  if (!item.url.endsWith(".json")) continue;

  let manifest;
  try {
    manifest = JSON.parse(await readFile(expectedPath, "utf8"));
  } catch (error) {
    invalidJson.push({ ...item, expectedPath, error });
    continue;
  }

  const references = new Set();
  collectAssetUrls(manifest, references);

  if (item.url === "/world/bgc-world.json" && Array.isArray(manifest.tiles)) {
    for (const tile of manifest.tiles) {
      if (typeof tile.tile_id === "string") references.add(`/world/tiles/${tile.tile_id}.json`);
    }
  }

  for (const url of references) pending.push({ url, referencedBy: item.url });
}

if (missing.length || invalidJson.length) {
  for (const item of missing) {
    console.error([
      "Missing deployment asset:",
      `  URL: ${item.url}`,
      `  Referenced by: ${item.referencedBy}`,
      `  Expected: ${relative(webRoot, item.expectedPath)}`,
    ].join("\n"));
  }
  for (const item of invalidJson) {
    console.error([
      "Invalid deployment manifest:",
      `  URL: ${item.url}`,
      `  Referenced by: ${item.referencedBy}`,
      `  Expected: ${relative(webRoot, item.expectedPath)}`,
      `  Error: ${item.error.message}`,
    ].join("\n"));
  }
  console.error(`Deployment asset verification failed: ${missing.length} missing, ${invalidJson.length} invalid JSON.`);
  process.exitCode = 1;
} else {
  const counts = { glb: 0, json: 0, image: 0 };
  for (const url of checked.keys()) {
    if (url.endsWith(".glb")) counts.glb += 1;
    else if (url.endsWith(".json")) counts.json += 1;
    else counts.image += 1;
  }
  console.log(`Deployment assets verified: ${checked.size} files (${counts.glb} GLB, ${counts.json} JSON, ${counts.image} image).`);
}
