import type { EntityRecord } from "../runtime/types";

export const TOUR_SLUG = "bgc-landmarks";

export function slugify(value: string) {
  return value.normalize("NFKD").toLowerCase().replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "place";
}

export function placeSlugs(entities: EntityRecord[]) {
  const groups = new Map<string, EntityRecord[]>();
  for (const entity of entities) {
    if (!entity.name) continue;
    const base = slugify(entity.name);
    groups.set(base, [...(groups.get(base) ?? []), entity]);
  }
  const slugs = new Map<string, string>();
  for (const [base, group] of groups) {
    group.sort((a, b) => a.entity_id.localeCompare(b.entity_id));
    group.forEach((entity, index) => slugs.set(entity.entity_id, group.length === 1 ? base : `${base}-${index + 1}`));
  }
  return slugs;
}

function normalize(value: string) {
  return value.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim().replace(/\s+/g, " ");
}

export function searchPlaces(entities: EntityRecord[], input: string) {
  const query = normalize(input);
  if (!query) return [];
  return entities.flatMap((entity) => {
    if (!entity.name) return [];
    const name = normalize(entity.name);
    const aliases = entity.aliases.map(normalize);
    let rank = 99;
    if (name === query) rank = 0;
    else if (aliases.includes(query)) rank = 1;
    else if (name.startsWith(query)) rank = 2;
    else if (aliases.some((alias) => alias.startsWith(query))) rank = 3;
    else if (name.includes(query)) rank = 4;
    else if (aliases.some((alias) => alias.includes(query))) rank = 5;
    return rank === 99 ? [] : [{ entity, rank }];
  }).sort((a, b) => a.rank - b.rank || (a.entity.name ?? "").localeCompare(b.entity.name ?? "") || a.entity.entity_id.localeCompare(b.entity.entity_id)).slice(0, 12).map(({ entity }) => entity);
}

export function typeLabel(value: string) {
  if (!value || value === "yes" || value === "building") return "Building";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function heightLabel(entity: EntityRecord) {
  if (entity.height_m === null) return "Height unavailable";
  const value = `${Math.round(entity.height_m)} m`;
  if (entity.height_status === "VERIFIED_AUTHORITATIVE") return `Published height · ${value}`;
  if (entity.height_status.startsWith("VERIFIED_GEOGRAPHIC")) return `Mapped height · ${value}`;
  if (entity.height_status === "CONFLICTED") return `Height sources differ · ${value}`;
  if (entity.height_status === "PROCEDURAL") return `Approx. model height · ${value}`;
  return `Approx. height · ${value}`;
}
