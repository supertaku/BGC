"use client";

import { Stats } from "@react-three/drei";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { EnvironmentManager } from "./EnvironmentManager";
import { InteractionManager } from "./InteractionManager";
import { LandmarkLODManager } from "./LandmarkLODManager";
import { NavigationController, type FocusRequest } from "./NavigationController";
import { PerformanceProbe } from "./PerformanceProbe";
import { TileManager } from "./TileManager";
import type { BenchmarkReport, EntityRecord, EnvironmentQuality, Footprint, InteractiveManifest, NavigationMode, RuntimeMetrics, RuntimeRefs, RuntimeSummary, TileMode, Viewpoint, WorldManifest } from "./types";
import { createBGCVisualMaterials, disposeBGCVisualMaterials } from "./visualSystem";

export function WorldRuntime({ manifest, interactive, tileMode, navigation, environmentQuality, viewpoint, focusRequest, tourStop, selected, debug, runtime, onRuntime, onReady, onLodChange, onSelect, onMetrics, onBenchmark, onEnvironmentGroups, onBoundaryHit }: {
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
  onRuntime: (summary: RuntimeSummary) => void;
  onReady: () => void;
  onLodChange: (ids: string[]) => void;
  onSelect: (footprint: Footprint | null) => void;
  onMetrics: (metrics: RuntimeMetrics) => void;
  onBenchmark: (report: BenchmarkReport) => void;
  onEnvironmentGroups: (count: number) => void;
  onBoundaryHit: () => void;
}) {
  const focus = useRef(new THREE.Vector3(...viewpoint.target));
  const tileRecords = useRef(new Map());
  const tileScenes = useRef(new Map());
  const activeTileIds = useRef(new Set<string>());
  const sidecars = useRef(new Map());
  const refs = useMemo<RuntimeRefs>(() => ({ focus, tileRecords, tileScenes, activeTileIds, sidecars }), []);
  const visualMaterials = useMemo(() => createBGCVisualMaterials(), []);
  useEffect(() => () => disposeBGCVisualMaterials(visualMaterials), [visualMaterials]);

  return <>
    <TileManager tiles={manifest.tiles ?? []} mode={tileMode} refs={refs} materials={visualMaterials} quality={environmentQuality} onSummary={onRuntime} onInitialReady={onReady} />
    <LandmarkLODManager assets={manifest.detailed_assets ?? []} entities={interactive.entities} refs={refs} materials={visualMaterials} quality={environmentQuality} onActiveChange={onLodChange} />
    <EnvironmentManager activeIds={runtime.activeIds} quality={environmentQuality} refs={refs} materials={visualMaterials} onGroupCount={onEnvironmentGroups} />
    <NavigationController mode={navigation} viewpoint={viewpoint} refs={refs} focusRequest={focusRequest} tourStop={tourStop} onBoundaryHit={onBoundaryHit} />
    <InteractionManager mode={navigation} refs={refs} selected={selected} onSelect={onSelect} />
    <PerformanceProbe tileMode={tileMode} navigation={navigation} runtime={runtime} onSample={onMetrics} onBenchmark={onBenchmark} />
    {debug ? <Stats className="fps" /> : null}
  </>;
}
