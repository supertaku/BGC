import type { EntityRecord, EnvironmentQuality, NavigationMode, TileMode } from "../runtime/types";
import { placeSlugs, TOUR_SLUG } from "./placeState.ts";

export function resolveUrlState(params: URLSearchParams, entities: EntityRecord[], lod1Ids: string[]) {
  const slugMap = placeSlugs(entities);
  const place = entities.find((entity) => slugMap.get(entity.entity_id) === params.get("place")) ?? null;
  const stops = lod1Ids.map((id) => entities.find((entity) => entity.detailed_asset_id === id)).filter((entity): entity is EntityRecord => Boolean(entity));
  const debug = params.get("debug") === "1";
  const requestedNavigation = params.get("navigation")?.toUpperCase();
  const explicitNavigation = requestedNavigation === "INSPECT" || requestedNavigation === "WALK" || requestedNavigation === "TOUR"
    ? requestedNavigation as NavigationMode : null;
  const tourValid = params.get("tour") === TOUR_SLUG && stops.length > 0;
  const navigation: NavigationMode = debug && explicitNavigation ? explicitNavigation
    : tourValid ? "TOUR"
    : params.get("mode") === "walk" ? "WALK"
    : explicitNavigation && params.get("benchmark") === "1" ? explicitNavigation
    : "INSPECT";
  const requestedQuality = params.get("quality")?.toUpperCase();
  const quality: EnvironmentQuality = debug && (requestedQuality === "LEGACY" || requestedQuality === "LOW" || (requestedQuality === "FULL" && params.get("benchmark") === "1"))
    ? requestedQuality : "LOW";
  const tileMode: TileMode = debug && params.get("tiles") === "all" ? "ALL_LOADED" : "DYNAMIC";
  return {
    debug, navigation, quality, tileMode, place,
    selectedEntity: navigation === "TOUR" ? stops[0] ?? null : place,
    invalidPlace: params.has("place") && !place,
    invalidTour: params.has("tour") && !tourValid,
  };
}
