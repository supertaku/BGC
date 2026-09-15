import * as THREE from "three";
import type { EnvironmentQuality } from "./types";

export const BGC_MATERIAL_NAMES = [
  "BGC_GLASS_DARK", "BGC_GLASS_LIGHT", "BGC_CONCRETE_LIGHT", "BGC_CONCRETE_DARK",
  "BGC_STONE_WARM", "BGC_METAL_DARK", "BGC_METAL_LIGHT", "BGC_ASPHALT",
  "BGC_SIDEWALK", "BGC_GRASS", "BGC_SOIL",
] as const;

export type BGCMaterialName = typeof BGC_MATERIAL_NAMES[number];
export type BGCVisualMaterials = Record<BGCMaterialName, THREE.MeshStandardMaterial>;

function material(name: BGCMaterialName, color: string, roughness: number, metalness = 0) {
  const result = new THREE.MeshStandardMaterial({ name, color, roughness, metalness });
  result.dithering = true;
  return result;
}

export function createBGCVisualMaterials(): BGCVisualMaterials {
  return {
    BGC_GLASS_DARK: material("BGC_GLASS_DARK", "#17333d", .24, .08),
    BGC_GLASS_LIGHT: material("BGC_GLASS_LIGHT", "#507683", .31, .04),
    BGC_CONCRETE_LIGHT: material("BGC_CONCRETE_LIGHT", "#b8b7ae", .78),
    BGC_CONCRETE_DARK: material("BGC_CONCRETE_DARK", "#626968", .82),
    BGC_STONE_WARM: material("BGC_STONE_WARM", "#a98f70", .73),
    BGC_METAL_DARK: material("BGC_METAL_DARK", "#30383a", .34, .72),
    BGC_METAL_LIGHT: material("BGC_METAL_LIGHT", "#929a99", .39, .62),
    BGC_ASPHALT: material("BGC_ASPHALT", "#343b40", .96),
    BGC_SIDEWALK: material("BGC_SIDEWALK", "#aaa698", .91),
    BGC_GRASS: material("BGC_GRASS", "#526d4a", .96),
    BGC_SOIL: material("BGC_SOIL", "#596052", .98),
  };
}

function familyFor(sourceName: string): BGCMaterialName {
  const name = sourceName.toLocaleLowerCase();
  if (name.includes("road")) return "BGC_ASPHALT";
  if (name.includes("path") || name.includes("sidewalk")) return "BGC_SIDEWALK";
  if (name.includes("open") || name.includes("grass")) return "BGC_GRASS";
  if (name.includes("ground") || name.includes("roof")) return "BGC_SOIL";
  if (name.includes("storefront") || name.includes("light_glass")) return "BGC_GLASS_LIGHT";
  if (name.includes("glass") || name.includes("office")) return "BGC_GLASS_DARK";
  if (name.includes("dark_metal")) return "BGC_METAL_DARK";
  if (name.includes("metal")) return "BGC_METAL_LIGHT";
  if (name.includes("warm") || name.includes("retail")) return "BGC_STONE_WARM";
  if (name.includes("residential") || name.includes("light_neutral")) return "BGC_CONCRETE_LIGHT";
  return "BGC_CONCRETE_DARK";
}

export function harmonizeScene(root: THREE.Object3D, materials: BGCVisualMaterials, quality: EnvironmentQuality, landmark = false) {
  root.traverse((object) => {
    if (!(object instanceof THREE.Mesh)) return;
    const source = Array.isArray(object.material) ? object.material[0]?.name ?? "" : object.material?.name ?? "";
    object.material = materials[familyFor(source)];
    object.castShadow = quality === "FULL" && landmark;
    object.receiveShadow = quality === "FULL";
    object.frustumCulled = true;
  });
}

export function disposeBGCVisualMaterials(materials: BGCVisualMaterials) {
  BGC_MATERIAL_NAMES.forEach((name) => materials[name].dispose());
}
