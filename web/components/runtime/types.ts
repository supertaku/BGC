import type * as THREE from "three";

export type NavigationMode = "INSPECT" | "WALK" | "TOUR";
export type TileMode = "DYNAMIC" | "ALL_LOADED";
export type EnvironmentQuality = "LEGACY" | "LOW" | "FULL";
export type TileState = "UNREQUESTED" | "PRELOADING" | "READY" | "ACTIVE" | "CACHED" | "ERROR";

export type Viewpoint = {
  id: string;
  label: string;
  position: [number, number, number];
  target: [number, number, number];
};

export type WorldTile = {
  tile_id: string;
  url: string;
  center: [number, number];
  bounds: [number, number, number, number];
  size_bytes: number;
  triangles: number;
  meshes: number;
};

export type DetailedAsset = { entity_id: string; name: string; url: string; lod: "LOD1" };

export type WorldManifest = {
  world_id: string;
  title: string;
  asset?: { url: string; size_bytes: number; triangles: number; meshes: number; materials: number };
  tiles?: WorldTile[];
  detailed_assets?: DetailedAsset[];
  totals?: { glb_bytes: number; triangles: number; runtime_nodes: number; tiles: number };
  tile_loading?: "ALL_LOADED" | "DISTANCE_BASED";
  attribution: { text: string; url: string; license: string; license_url: string };
  viewpoints: Viewpoint[];
};

export type EntityRecord = {
  entity_id: string;
  name: string | null;
  aliases: string[];
  height_m: number | null;
  height_status: string;
  building_type: string;
  detailed_asset_id: string | null;
  tile_id: string;
  center: [number, number];
  bounds: [number, number, number, number];
};

export type Footprint = EntityRecord & { rings: [number, number][][] };
export type EnvironmentInstance = { id: string; position: [number, number]; grounding: "VERIFIED_GEOGRAPHIC" | "PROCEDURAL" };
export type NamedWaySegment = { id: string; name: string; aliases: string[]; kind: "ROAD" | "PATH"; class: string | null; width_m: number | null; points: [number, number][] };
export type CurrentStreet = Pick<NamedWaySegment, "id" | "name" | "kind">;
export type EnvironmentAssetType =
  | "TREE_GENERIC"
  | "STREET_LAMP_GENERIC"
  | "BENCH_GENERIC"
  | "BOLLARD_GENERIC"
  | "WASTE_BIN_GENERIC"
  | "SHELTER_GENERIC";
export type TileSidecar = {
  tile_id: string;
  footprints: Footprint[];
  environment: Partial<Record<EnvironmentAssetType, EnvironmentInstance[]>>;
  namedWays?: NamedWaySegment[];
};

export type InteractiveManifest = {
  schema_version: number;
  source_snapshot: string;
  source_status: string;
  boundary_status: string;
  boundary: [number, number][];
  tile_size_m: number;
  entities: EntityRecord[];
  tile_sidecar_url_template: string;
  environment_counts: Partial<Record<EnvironmentAssetType, number>>;
  procedural_environment_count: number;
  lod1_entity_ids: string[];
};

export type TileRuntimeRecord = WorldTile & {
  state: TileState;
  distance: number;
  last_used_ms: number;
  requested_count: number;
  model_ready: boolean;
  sidecar?: TileSidecar;
};

export type RuntimeSummary = {
  active: number;
  visible: number;
  visibleIds: string[];
  desired: number;
  ready: number;
  preloading: number;
  cached: number;
  errors: number;
  activeIds: string[];
  networkBytes: number;
  networkRequests: number;
  repeatedRequests: number;
  activeLod1: string[];
  camera: [number, number, number];
  transitions: number;
};

export type RuntimeMetrics = { fps: number; calls: number; triangles: number; geometries: number; textures: number };
export type BenchmarkReport = {
  status: "PASS";
  scene: string;
  quality: EnvironmentQuality;
  mode: TileMode;
  navigation: NavigationMode;
  sample_count: number;
  warmup_ms: number;
  duration_ms: number;
  load_duration_ms: number | null;
  active_environment_groups: number;
  transfer: {
    initial_bytes: number | null;
    streamed_bytes: number | null;
    initial_decoded_bytes: number | null;
    streamed_decoded_bytes: number | null;
    timing_supported: boolean;
  };
  mean_fps: number;
  median_fps: number;
  p1_low_fps: number;
  minimum_fps: number;
  maximum_fps: number;
  renderer: RuntimeMetrics;
  runtime: RuntimeSummary;
  environment: Record<string, string | number | null>;
};

export type RuntimeRefs = {
  focus: React.MutableRefObject<THREE.Vector3>;
  anchors: React.MutableRefObject<{ x: number; z: number; role: "PRIMARY" | "SECONDARY" }[]>;
  visibleTileIds: React.MutableRefObject<Set<string>>;
  tileRecords: React.MutableRefObject<Map<string, TileRuntimeRecord>>;
  tileScenes: React.MutableRefObject<Map<string, THREE.Object3D>>;
  activeTileIds: React.MutableRefObject<Set<string>>;
  sidecars: React.MutableRefObject<Map<string, TileSidecar>>;
};
