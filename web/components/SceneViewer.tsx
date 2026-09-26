"use client";

import { Canvas } from "@react-three/fiber";
import { Component, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { ProductShell } from "./product/ProductShell";
import { placeSlugs, TOUR_SLUG } from "./product/placeState";
import { resolveUrlState } from "./product/urlState";
import { WorldRuntime } from "./runtime/WorldRuntime";
import { applyM23Preview } from "./runtime/m23Data";
import type { FocusRequest } from "./runtime/NavigationController";
import { ACTIVE_RADIUS_M, PRELOAD_RADIUS_M, RETENTION_RADIUS_M } from "./runtime/spatial";
import type { BenchmarkReport, CurrentStreet, EntityRecord, EnvironmentQuality, Footprint, InteractiveManifest, NavigationMode, RuntimeMetrics, RuntimeSummary, TileMode, WorldManifest } from "./runtime/types";
import { VisualEnvironment } from "./runtime/VisualEnvironment";
import { stability } from "./runtime/stability";

const EMPTY_RUNTIME: RuntimeSummary = {
  active: 0, visible: 0, visibleIds: [], desired: 0, ready: 0, preloading: 0, cached: 0, errors: 0, activeIds: [], networkBytes: 0,
  networkRequests: 0, repeatedRequests: 0, activeLod1: [], camera: [0, 0, 0], transitions: 0,
};

class ViewerErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: Error) { return { error: error.message || "Unknown WebGL viewer error" }; }
  render() {
    if (this.state.error) return <div className="viewer-error" role="alert"><strong>The city view could not open</strong><p>{this.state.error}</p><button onClick={() => window.location.reload()}>Retry</button></div>;
    return this.props.children;
  }
}

function formatBytes(bytes: number) {
  return bytes < 1_000_000 ? `${Math.round(bytes / 1000)} KB` : `${(bytes / 1_000_000).toFixed(2)} MB`;
}

export default function SceneViewer() {
  const [manifest, setManifest] = useState<WorldManifest | null>(null);
  const [interactive, setInteractive] = useState<InteractiveManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewpointIndex, setViewpointIndex] = useState(0);
  const [tileMode, setTileMode] = useState<TileMode>("DYNAMIC");
  const [navigation, setNavigation] = useState<NavigationMode>("INSPECT");
  // FULL failed the matched foreground p1 gate; keep it available for diagnostics only.
  const [environmentQuality, setEnvironmentQuality] = useState<EnvironmentQuality>("LOW");
  const [runtime, setRuntime] = useState<RuntimeSummary>(EMPTY_RUNTIME);
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  const [debug, setDebug] = useState(false);
  const [selected, setSelected] = useState<Footprint | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<EntityRecord | null>(null);
  const [currentStreet, setCurrentStreet] = useState<CurrentStreet | null>(null);
  const [focusRequest, setFocusRequest] = useState<FocusRequest>(null);
  const [tourIndex, setTourIndex] = useState(0);
  const [environmentGroups, setEnvironmentGroups] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const [stabilityRun, setStabilityRun] = useState<{ status: string; completed: number; total: number }>({ status: "IDLE", completed: 0, total: 0 });
  const startedAt = useRef(0);
  const focusSequence = useRef(0);
  const lodIds = useRef<string[]>([]);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const slugs = useMemo(() => placeSlugs(interactive?.entities ?? []), [interactive]);
  const issueFocus = useCallback((entity: EntityRecord) => {
    focusSequence.current += 1;
    setFocusRequest({ sequence: focusSequence.current, entity });
  }, []);

  useEffect(() => {
    if (debug) window.__BGC_STABILITY__ = stability;
    else delete window.__BGC_STABILITY__;
    return () => { delete window.__BGC_STABILITY__; };
  }, [debug]);

  useEffect(() => {
    if (!debug || loadedAt === null || !interactive || new URLSearchParams(window.location.search).get("stability_run") !== "1") return;
    const candidates = interactive.entities.filter((entity) => entity.name).sort((a, b) => (a.center[0] + a.center[1] * 0.5) - (b.center[0] + b.center[1] * 0.5));
    const targets = navigation === "TOUR"
      ? interactive.lod1_entity_ids.map((id) => interactive.entities.find((entity) => entity.detailed_asset_id === id)!)
      : Array.from({ length: 8 }, (_, index) => candidates[Math.round(index * (candidates.length - 1) / 7)]);
    if (targets.some((target) => !target)) return;
    const baseline = stability.focus_transition_completes;
    const started = performance.now();
    let issued = 1;
    issueFocus(targets[0]);
    const timer = window.setInterval(() => {
      const completed = stability.focus_transition_completes - baseline;
      setStabilityRun((current) => current.status === "IDLE" ? { status: "RUNNING", completed, total: targets.length } : current);
      if (completed >= targets.length) {
        setStabilityRun({ status: "COMPLETE", completed, total: targets.length });
        window.clearInterval(timer);
      } else if (performance.now() - started > 60000) {
        setStabilityRun({ status: "TIMEOUT", completed, total: targets.length });
        window.clearInterval(timer);
      } else if (completed >= issued && issued < targets.length) {
        if (navigation === "TOUR") setTourIndex(issued);
        issueFocus(targets[issued]);
        issued += 1;
        setStabilityRun({ status: "RUNNING", completed, total: targets.length });
      }
    }, 250);
    return () => window.clearInterval(timer);
  }, [debug, interactive, issueFocus, loadedAt, navigation]);

  const updateUrl = useCallback((patch: Record<string, string | null>, push = false) => {
    const url = new URL(window.location.href);
    for (const [key, value] of Object.entries(patch)) {
      if (value === null) url.searchParams.delete(key);
      else url.searchParams.set(key, value);
    }
    window.history[push ? "pushState" : "replaceState"]({}, "", url);
  }, []);
  const restoreUrl = useCallback((world: WorldManifest, data: InteractiveManifest) => {
    const params = new URLSearchParams(window.location.search);
    const state = resolveUrlState(params, data.entities, data.lod1_entity_ids);
    const view = world.viewpoints.findIndex((candidate) => candidate.id === params.get("view"));
    if (view >= 0) setViewpointIndex(view);
    setDebug(state.debug);
    setTileMode(state.tileMode);
    setEnvironmentQuality(state.quality);
    setSelected(null);
    setSelectedEntity(state.selectedEntity);
    setNavigation(state.navigation);
    if (state.navigation === "TOUR") setTourIndex(0);
    if (state.place && state.navigation !== "TOUR") issueFocus(state.place);
    else if (state.navigation === "TOUR" && !(state.debug && params.get("stability_run") === "1")) {
      const stop = data.entities.find((entity) => entity.detailed_asset_id === data.lod1_entity_ids[0]);
      if (stop) issueFocus(stop);
    }
    else setFocusRequest(null);
    if (state.invalidPlace) setNotice("That place link is unavailable in this dataset.");
    else if (state.invalidTour) setNotice("That tour link is unavailable.");
  }, [issueFocus]);

  useEffect(() => {
    startedAt.current = performance.now();
    Promise.all([
      fetch("/world/bgc-world.json").then((response) => { if (!response.ok) throw new Error(`World manifest HTTP ${response.status}`); return response.json() as Promise<WorldManifest>; }),
      fetch("/world/bgc-interactive.json").then((response) => { if (!response.ok) throw new Error(`Interaction manifest HTTP ${response.status}`); return response.json() as Promise<InteractiveManifest>; }),
    ]).then(([world, data]) => applyM23Preview(world,data)).then(([world, data]) => {
      setManifest(world);
      setInteractive(data);
      restoreUrl(world, data);
    }).catch((reason: Error) => setError(reason.message));
    return () => { if (noticeTimer.current) clearTimeout(noticeTimer.current); };
  }, [restoreUrl]);

  useEffect(() => {
    if (!manifest || !interactive) return;
    const onPop = () => restoreUrl(manifest, interactive);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [manifest, interactive, restoreUrl]);

  const tourStops = useMemo(() => interactive?.lod1_entity_ids
    .map((id) => interactive.entities.find((entity) => entity.detailed_asset_id === id))
    .filter((entity): entity is EntityRecord => Boolean(entity)) ?? [], [interactive]);

  const flashNotice = useCallback((message: string) => {
    setNotice(message);
    if (noticeTimer.current) clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(null), 1800);
  }, []);
  const handleRuntime = useCallback((summary: RuntimeSummary) => {
    setRuntime((current) => {
      const next = { ...summary, activeLod1: lodIds.current };
      return JSON.stringify(current) === JSON.stringify(next) ? current : next;
    });
  }, []);
  const handleLod = useCallback((ids: string[]) => {
    lodIds.current = ids;
    setRuntime((current) => ({ ...current, activeLod1: ids }));
  }, []);
  const handleReady = useCallback(() => setLoadedAt((current) => current ?? performance.now() - startedAt.current), []);
  const handleSelect = useCallback((footprint: Footprint | null) => {
    setSelected(footprint); setSelectedEntity(footprint);
    if (footprint) { setNavigation("INSPECT"); updateUrl({ place: slugs.get(footprint.entity_id) ?? null, mode: null, tour: null }, true); }
  }, [slugs, updateUrl]);
  const focusEntity = useCallback((entity: EntityRecord) => {
    setNavigation("INSPECT");
    setSelected(null);
    setSelectedEntity(entity);
    issueFocus(entity);
    updateUrl({ place: slugs.get(entity.entity_id) ?? null, mode: null, tour: null }, true);
  }, [issueFocus, slugs, updateUrl]);
  const startTour = useCallback(() => {
    if (!tourStops.length) return;
    setTourIndex(0);
    setSelectedEntity(tourStops[0]);
    setNavigation("TOUR");
    issueFocus(tourStops[0]);
    updateUrl({ tour: TOUR_SLUG, place: null, mode: null }, true);
  }, [issueFocus, tourStops, updateUrl]);
  const changeMode = useCallback((mode: NavigationMode) => {
    if (mode === "TOUR") startTour();
    else {
      if (navigation === "TOUR") { setSelected(null); setSelectedEntity(null); }
      setNavigation(mode);
      updateUrl({ mode: mode === "WALK" ? "walk" : null, tour: null, place: navigation === "TOUR" ? null : selectedEntity ? slugs.get(selectedEntity.entity_id) ?? null : null }, true);
    }
  }, [navigation, selectedEntity, slugs, startTour, updateUrl]);
  const changeTourStop = useCallback((index: number) => {
    const bounded = Math.max(0, Math.min(tourStops.length - 1, index));
    setTourIndex(bounded);
    setSelectedEntity(tourStops[bounded] ?? null);
    if (tourStops[bounded]) issueFocus(tourStops[bounded]);
  }, [issueFocus, tourStops]);
  const closePlace = useCallback(() => { setSelected(null); setSelectedEntity(null); updateUrl({ place: null }); }, [updateUrl]);
  const share = useCallback(async () => {
    const url = new URL(window.location.href);
    url.search = "";
    if (navigation === "TOUR") url.searchParams.set("tour", TOUR_SLUG);
    else { if (selectedEntity) url.searchParams.set("place", slugs.get(selectedEntity.entity_id) ?? ""); if (navigation === "WALK") url.searchParams.set("mode", "walk"); }
    if (navigator.share) {
      try { await navigator.share({ title: "BGC 3D", url: url.toString() }); return; }
      catch (reason) { if ((reason as DOMException).name === "AbortError") return; }
    }
    try { await navigator.clipboard.writeText(url.toString()); flashNotice("Link copied"); }
    catch { flashNotice("Could not share this link"); }
  }, [navigation, selectedEntity, slugs, flashNotice]);

  if (error) return <div className="viewer-error" role="alert"><strong>Could not load BGC 3D</strong><p>{error}</p><button onClick={() => window.location.reload()}>Retry</button></div>;
  if (!manifest || !interactive) return <div className="viewer-loading" aria-label="Loading BGC"><div className="loading-mark" /><p>Loading BGC 3D</p></div>;
  const viewpoint = manifest.viewpoints[viewpointIndex];
  const currentTourStop = navigation === "TOUR" ? tourStops[tourIndex] ?? null : null;

  return <section className="viewer" aria-label="BGC 3D city experience">
    <ViewerErrorBoundary>
      <Canvas key={environmentQuality} camera={{ position: viewpoint.position, fov: 48, near: 0.1, far: 20000 }} dpr={environmentQuality === "LEGACY" ? 1 : [1, 1.5]} shadows={environmentQuality === "FULL" ? "soft" : false} gl={{ antialias: true, powerPreference: "high-performance", toneMapping: THREE.ACESFilmicToneMapping }} onCreated={({ gl }) => { gl.toneMappingExposure = environmentQuality === "LEGACY" ? 1 : 1.08; gl.outputColorSpace = THREE.SRGBColorSpace; }}>
        <VisualEnvironment quality={environmentQuality} />
          <WorldRuntime manifest={manifest} interactive={interactive} tileMode={tileMode} navigation={navigation} environmentQuality={environmentQuality} viewpoint={viewpoint} focusRequest={focusRequest} tourStop={currentTourStop} selected={selected} debug={debug} runtime={runtime} loadDurationMs={loadedAt} environmentGroups={environmentGroups} onRuntime={handleRuntime} onReady={handleReady} onLodChange={handleLod} onSelect={handleSelect} onMetrics={setMetrics} onBenchmark={setBenchmark} onEnvironmentGroups={setEnvironmentGroups} onBoundaryHit={() => flashNotice("Movement constrained by a building or the project boundary")} onStreetChange={setCurrentStreet} />
      </Canvas>
    </ViewerErrorBoundary>

    <ProductShell interactive={interactive} navigation={navigation} currentStreet={currentStreet} selectedEntity={navigation === "TOUR" ? null : selectedEntity} tourStops={tourStops} tourIndex={tourIndex} ready={loadedAt !== null} onMode={changeMode} onSelectPlace={focusEntity} onClosePlace={closePlace} onTourStop={changeTourStop} onShare={share} onFocusPlace={() => selectedEntity && issueFocus(selectedEntity)} />
    {debug ? <><div className="quality-controls"><label>Tiles<select value={tileMode} onChange={(event) => setTileMode(event.target.value as TileMode)}><option value="DYNAMIC">Dynamic</option><option value="ALL_LOADED">All loaded</option></select></label><label>Environment<select value={environmentQuality} onChange={(event) => setEnvironmentQuality(event.target.value as EnvironmentQuality)}><option value="LEGACY">Legacy</option><option value="LOW">Low</option><option value="FULL">Full</option></select></label></div><nav className="viewpoint-controls" aria-label="Debug viewpoints">{manifest.viewpoints.map((candidate, index) => <button key={candidate.id} type="button" onClick={() => { setNavigation("INSPECT"); setViewpointIndex(index); setFocusRequest(null); }}>{candidate.label}</button>)}</nav></> : null}    {debug ? <aside className="metrics-panel" aria-live="polite" data-stability={JSON.stringify(stability)} data-runtime={JSON.stringify(runtime)} data-stability-run={JSON.stringify(stabilityRun)}><strong>{metrics ? `${metrics.fps} FPS` : "Sampling"}</strong><span>{tileMode} - {runtime.active} active - {runtime.visible} visible - {runtime.preloading} preloading - {runtime.cached} cached</span><span>{runtime.activeLod1.length} LOD1 - {environmentGroups} environment groups</span><span>{formatBytes(runtime.networkBytes)} - {runtime.networkRequests} requests - {runtime.repeatedRequests} repeats</span><span>{metrics ? `${metrics.calls} calls - ${metrics.triangles.toLocaleString()} triangles - ${metrics.geometries} geometries - ${metrics.textures} textures` : "Renderer metrics pending"}</span><span>Camera {runtime.camera.join(", ")}</span><span>Rings {ACTIVE_RADIUS_M} m - {PRELOAD_RADIUS_M} m - {RETENTION_RADIUS_M} m</span><span>{loadedAt === null ? "Loading initial tiles" : `Interactive in ${loadedAt.toFixed(0)} ms`}</span>{benchmark ? <span data-testid="benchmark-result" data-report={JSON.stringify(benchmark)}>Benchmark {benchmark.scene}: mean {benchmark.mean_fps}, median {benchmark.median_fps}, p1 {benchmark.p1_low_fps} FPS</span> : null}</aside> : null}
    {notice ? <div className="runtime-notice" role="status">{notice}</div> : null}
    <a className="attribution" href={manifest.attribution.url} target="_blank" rel="noreferrer">{manifest.attribution.text}</a>
  </section>;
}
