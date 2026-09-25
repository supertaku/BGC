"use client";

import { Canvas } from "@react-three/fiber";
import { Component, type ReactNode, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { WorldRuntime } from "./runtime/WorldRuntime";
import type { FocusRequest } from "./runtime/NavigationController";
import { ACTIVE_RADIUS_M, PRELOAD_RADIUS_M, RETENTION_RADIUS_M } from "./runtime/spatial";
import type { BenchmarkReport, EntityRecord, EnvironmentQuality, Footprint, InteractiveManifest, NavigationMode, RuntimeMetrics, RuntimeSummary, TileMode, WorldManifest } from "./runtime/types";
import { VisualEnvironment } from "./runtime/VisualEnvironment";

const EMPTY_RUNTIME: RuntimeSummary = {
  active: 0, preloading: 0, cached: 0, errors: 0, activeIds: [], networkBytes: 0,
  networkRequests: 0, repeatedRequests: 0, activeLod1: [], camera: [0, 0, 0], transitions: 0,
};

class ViewerErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: Error) { return { error: error.message || "Unknown WebGL viewer error" }; }
  render() {
    if (this.state.error) return <div className="viewer-error" role="alert"><strong>Viewer failed to load</strong><span>{this.state.error}</span></div>;
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
  // FULL remains opt-in until identical foreground scenarios establish its shadow cost.
  const [environmentQuality, setEnvironmentQuality] = useState<EnvironmentQuality>("LOW");
  const [runtime, setRuntime] = useState<RuntimeSummary>(EMPTY_RUNTIME);
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  const [debug, setDebug] = useState(false);
  const [selected, setSelected] = useState<Footprint | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<EntityRecord | null>(null);
  const [focusRequest, setFocusRequest] = useState<FocusRequest>(null);
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [tourIndex, setTourIndex] = useState(0);
  const [environmentGroups, setEnvironmentGroups] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const startedAt = useRef(0);
  const lodIds = useRef<string[]>([]);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    startedAt.current = performance.now();
    Promise.all([
      fetch("/world/bgc-world.json").then((response) => { if (!response.ok) throw new Error(`World manifest HTTP ${response.status}`); return response.json() as Promise<WorldManifest>; }),
      fetch("/world/bgc-interactive.json").then((response) => { if (!response.ok) throw new Error(`Interaction manifest HTTP ${response.status}`); return response.json() as Promise<InteractiveManifest>; }),
    ]).then(([world, data]) => {
      setManifest(world);
      setInteractive(data);
      const params = new URLSearchParams(window.location.search);
      const requested = params.get("view");
      const index = world.viewpoints.findIndex((candidate) => candidate.id === requested);
      if (index >= 0) setViewpointIndex(index);
      if (params.get("tiles") === "all") setTileMode("ALL_LOADED");
      if (params.get("debug") === "1") setDebug(true);
    }).catch((reason: Error) => setError(reason.message));
    return () => { if (noticeTimer.current) clearTimeout(noticeTimer.current); };
  }, []);

  const tourStops = useMemo(() => interactive?.lod1_entity_ids
    .map((id) => interactive.entities.find((entity) => entity.detailed_asset_id === id))
    .filter((entity): entity is EntityRecord => Boolean(entity)) ?? [], [interactive]);
  const results = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    if (!query || !interactive) return [];
    return interactive.entities.filter((entity) => [entity.name, ...entity.aliases].some((value) => value?.toLocaleLowerCase().includes(query))).slice(0, 8);
  }, [interactive, search]);

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
  const handleSelect = useCallback((footprint: Footprint | null) => { setSelected(footprint); setSelectedEntity(footprint); }, []);
  const focusEntity = useCallback((entity: EntityRecord) => {
    setNavigation("INSPECT");
    setSelected(null);
    setSelectedEntity(entity);
    setFocusRequest({ sequence: performance.now(), entity });
    setSearchOpen(false);
    setSearch("");
  }, []);
  const startTour = useCallback(() => {
    if (!tourStops.length) return;
    setTourIndex(0);
    setSelectedEntity(tourStops[0]);
    setNavigation("TOUR");
  }, [tourStops]);
  const changeTourStop = useCallback((index: number) => {
    const bounded = Math.max(0, Math.min(tourStops.length - 1, index));
    setTourIndex(bounded);
    setSelectedEntity(tourStops[bounded] ?? null);
  }, [tourStops]);

  if (error) return <div className="viewer-error" role="alert"><strong>Viewer failed to load</strong><span>{error}</span></div>;
  if (!manifest || !interactive) return <div className="viewer-loading" aria-label="Loading BGC"><div className="loading-mark" /><p>Preparing BGC</p></div>;
  const viewpoint = manifest.viewpoints[viewpointIndex];
  const currentTourStop = navigation === "TOUR" ? tourStops[tourIndex] ?? null : null;

  return <section className="viewer" aria-label="Interactive real-data BGC viewer">
    <ViewerErrorBoundary>
      <Canvas camera={{ position: viewpoint.position, fov: 48, near: 0.1, far: 6000 }} dpr={[1, 1.5]} shadows={environmentQuality === "FULL" ? "soft" : false} gl={{ antialias: true, powerPreference: "high-performance", toneMapping: THREE.ACESFilmicToneMapping }} onCreated={({ gl }) => { gl.toneMappingExposure = 1.08; gl.outputColorSpace = THREE.SRGBColorSpace; }}>
        <VisualEnvironment quality={environmentQuality} />
        <Suspense fallback={null}>
          <WorldRuntime manifest={manifest} interactive={interactive} tileMode={tileMode} navigation={navigation} environmentQuality={environmentQuality} viewpoint={viewpoint} focusRequest={focusRequest} tourStop={currentTourStop} selected={selected} debug={debug} runtime={runtime} onRuntime={handleRuntime} onReady={handleReady} onLodChange={handleLod} onSelect={handleSelect} onMetrics={setMetrics} onBenchmark={setBenchmark} onEnvironmentGroups={setEnvironmentGroups} onBoundaryHit={() => flashNotice("Movement constrained by a building or the project boundary")} />
        </Suspense>
      </Canvas>
    </ViewerErrorBoundary>

    <header className="viewer-header"><div><span className="brand-mark">BGC</span><span className="brand-subtitle">Interactive city model</span></div><button className="quiet-button" type="button" onClick={() => setDebug((value) => !value)} aria-pressed={debug}>Diagnostics</button></header>
    <div className="primary-controls" role="toolbar" aria-label="Navigation controls">
      <button type="button" className={navigation === "INSPECT" ? "active" : ""} onClick={() => setNavigation("INSPECT")}>Inspect</button>
      <button id="walk-lock-button" type="button" className={navigation === "WALK" ? "active" : ""} onClick={() => setNavigation("WALK")}>Walk</button>
      <button type="button" className={navigation === "TOUR" ? "active" : ""} onClick={startTour}>Tour</button>
      <button type="button" className={searchOpen ? "active" : ""} onClick={() => setSearchOpen((value) => !value)} aria-expanded={searchOpen}>Search</button>
    </div>

    {searchOpen ? <div className="search-panel"><label htmlFor="building-search">Find a named building</label><input id="building-search" autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Try Central Square" /><div className="search-results">
      {!search ? <p>Search across {interactive.entities.length.toLocaleString()} named features and aliases.</p> : null}
      {search && !results.length ? <p>No matching building in the project data.</p> : null}
      {results.map((entity) => <button key={entity.entity_id} type="button" onClick={() => focusEntity(entity)}><strong>{entity.name}</strong><span>{entity.building_type} - {entity.height_m ?? "unknown"} m</span></button>)}
    </div></div> : null}

    <nav className="viewpoint-controls" aria-label="Saved inspection viewpoints">{manifest.viewpoints.map((candidate, index) => <button key={candidate.id} type="button" className={index === viewpointIndex && navigation === "INSPECT" ? "active" : ""} onClick={() => { setNavigation("INSPECT"); setViewpointIndex(index); setFocusRequest(null); }}>{candidate.label.replace("BGC ", "")}</button>)}</nav>
    {navigation === "WALK" ? <aside className="walk-help"><strong>Walk mode</strong><span>Click the scene to capture the mouse</span><span>WASD to move, Shift to move faster, Esc to release</span></aside> : null}
    {navigation === "TOUR" && currentTourStop ? <aside className="tour-panel" aria-live="polite"><span>Stop {tourIndex + 1} of {tourStops.length}</span><strong>{currentTourStop.name}</strong><div><button type="button" disabled={tourIndex === 0} onClick={() => changeTourStop(tourIndex - 1)}>Previous</button><button type="button" disabled={tourIndex === tourStops.length - 1} onClick={() => changeTourStop(tourIndex + 1)}>Next</button><button type="button" onClick={() => setNavigation("INSPECT")}>Exit tour</button></div></aside> : null}
    {selectedEntity ? <aside className="selection-panel"><button className="panel-close" type="button" aria-label="Close building details" onClick={() => { setSelected(null); setSelectedEntity(null); }}>Close</button><span>{selectedEntity.detailed_asset_id ? "LOD1 available" : "LOD2 massing"}</span><h2>{selectedEntity.name ?? "Unnamed building"}</h2><dl><div><dt>Entity</dt><dd>{selectedEntity.entity_id}</dd></div><div><dt>Height</dt><dd>{selectedEntity.height_m === null ? "Unknown" : `${selectedEntity.height_m} m`}</dd></div><div><dt>Evidence</dt><dd>{selectedEntity.height_status.replaceAll("_", " ")}</dd></div><div><dt>Type</dt><dd>{selectedEntity.building_type}</dd></div></dl></aside> : null}
    <div className="quality-controls"><label>Tiles<select value={tileMode} onChange={(event) => setTileMode(event.target.value as TileMode)}><option value="DYNAMIC">Dynamic</option><option value="ALL_LOADED">All loaded</option></select></label><label>Environment<select value={environmentQuality} onChange={(event) => setEnvironmentQuality(event.target.value as EnvironmentQuality)}><option value="OFF">Off</option><option value="LOW">Low</option><option value="FULL">Full</option></select></label></div>

    {debug ? <aside className="metrics-panel" aria-live="polite"><strong>{metrics ? `${metrics.fps} FPS` : "Sampling"}</strong><span>{tileMode} - {runtime.active} active - {runtime.preloading} preloading - {runtime.cached} cached</span><span>{runtime.activeLod1.length} LOD1 - {environmentGroups} environment groups</span><span>{formatBytes(runtime.networkBytes)} - {runtime.networkRequests} requests - {runtime.repeatedRequests} repeats</span><span>{metrics ? `${metrics.calls} calls - ${metrics.triangles.toLocaleString()} triangles - ${metrics.geometries} geometries - ${metrics.textures} textures` : "Renderer metrics pending"}</span><span>Camera {runtime.camera.join(", ")}</span><span>Rings {ACTIVE_RADIUS_M} m - {PRELOAD_RADIUS_M} m - {RETENTION_RADIUS_M} m</span><span>{loadedAt === null ? "Loading initial tiles" : `Interactive in ${loadedAt.toFixed(0)} ms`}</span>{benchmark ? <span data-testid="benchmark-result" data-report={JSON.stringify(benchmark)}>Benchmark {benchmark.scene}: mean {benchmark.mean_fps}, median {benchmark.median_fps}, p1 {benchmark.p1_low_fps} FPS</span> : null}</aside> : null}
    {notice ? <div className="runtime-notice" role="status">{notice}</div> : null}
    <a className="attribution" href={manifest.attribution.url} target="_blank" rel="noreferrer">{manifest.attribution.text}</a>
  </section>;
}
