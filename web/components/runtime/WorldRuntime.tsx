"use client";

import { Stats } from "@react-three/drei";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { EnvironmentManager } from "./EnvironmentManager";
import { InteractionManager } from "./InteractionManager";
import { LandmarkLODManager } from "./LandmarkLODManager";
import { NavigationController, type FocusRequest } from "./NavigationController";
import { PerformanceProbe } from "./PerformanceProbe";
import { PublicRealmManager } from "./PublicRealmManager";
import { StreetLocator } from "./StreetLocator";
import { TileManager } from "./TileManager";
import type { BenchmarkReport, CurrentStreet, EntityRecord, EnvironmentQuality, Footprint, InteractiveManifest, NavigationMode, RuntimeMetrics, RuntimeRefs, RuntimeSummary, TileMode, Viewpoint, WorldManifest } from "./types";
import { createBGCVisualMaterials, disposeBGCVisualMaterials } from "./visualSystem";

export function WorldRuntime({ manifest, interactive, tileMode, navigation, environmentQuality, viewpoint, focusRequest, tourStop, selected, debug, runtime, loadDurationMs, environmentGroups, onRuntime, onReady, onLodChange, onSelect, onMetrics, onBenchmark, onEnvironmentGroups, onBoundaryHit, onStreetChange }: {
  manifest: WorldManifest;
  interactive: InteractiveManifest;
  tileMode: TileMode;
  navigation: NavigationMode;
  environmentQuality: EnvironmentQuality;
  viewpoint: Viewpoint;
  focusRequest: FocusRequest;
  tourStop: EntityRecord | null;
  selected: Footprint | null;
  debug: boolean;
  runtime: RuntimeSummary;
  loadDurationMs: number | null;
  environmentGroups: number;
  onRuntime: (summary: RuntimeSummary) => void;
  onReady: () => void;
  onLodChange: (ids: string[]) => void;
  onSelect: (footprint: Footprint | null) => void;
  onMetrics: (metrics: RuntimeMetrics) => void;
  onBenchmark: (report: BenchmarkReport) => void;
  onEnvironmentGroups: (count: number) => void;
  onBoundaryHit: () => void;
  onStreetChange: (street: CurrentStreet | null) => void;
}) {
  const focus = useRef(new THREE.Vector3(...viewpoint.target));
  const tileRecords = useRef(new Map());
  const tileScenes = useRef(new Map());
  const activeTileIds = useRef(new Set<string>());
  const visibleTileIds = useRef(new Set<string>());
  const anchors = useRef([{ x: viewpoint.target[0], z: viewpoint.target[2], role: "PRIMARY" as const }]);
  const sidecars = useRef(new Map());
  const refs = useMemo<RuntimeRefs>(() => ({ focus, anchors, tileRecords, tileScenes, activeTileIds, visibleTileIds, sidecars }), []);
  const visualMaterials = useMemo(() => createBGCVisualMaterials(), []);
  useEffect(() => () => disposeBGCVisualMaterials(visualMaterials), [visualMaterials]);

  return <>
    <TileManager tiles={manifest.tiles ?? []} mode={tileMode} refs={refs} materials={visualMaterials} quality={environmentQuality} priorityTileId={focusRequest?.entity.tile_id ?? (navigation === "TOUR" ? tourStop?.tile_id : null)} navigation={navigation} onSummary={onRuntime} onInitialReady={onReady} />
    <LandmarkLODManager assets={manifest.detailed_assets ?? []} entities={interactive.entities} refs={refs} materials={visualMaterials} quality={environmentQuality} priorityAssetId={focusRequest?.entity.detailed_asset_id ?? (navigation === "TOUR" ? tourStop?.detailed_asset_id : null)} onActiveChange={onLodChange} />
    <EnvironmentManager activeIds={runtime.activeIds} quality={environmentQuality} refs={refs} materials={visualMaterials} onGroupCount={onEnvironmentGroups} />
    <PublicRealmManager activeIds={runtime.visibleIds} quality={environmentQuality} materials={visualMaterials} />
    <NavigationController mode={navigation} viewpoint={viewpoint} bounds={manifest.tiles ?? []} refs={refs} focusRequest={focusRequest} onBoundaryHit={onBoundaryHit} debug={debug} />
    <StreetLocator mode={navigation} refs={refs} onStreetChange={onStreetChange} />
    <InteractionManager mode={navigation} refs={refs} selected={selected} onSelect={onSelect} />
    <PerformanceProbe tileMode={tileMode} navigation={navigation} quality={environmentQuality} runtime={runtime} loadDurationMs={loadDurationMs} environmentGroups={environmentGroups} onSample={onMetrics} onBenchmark={onBenchmark} />
    {debug ? <Stats className="fps" /> : null}
  </>;
}
