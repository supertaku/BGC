"use client";

import { Component, ReactNode, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html, OrbitControls, Stats, useGLTF } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import * as THREE from "three";

type Viewpoint = {
  id: string;
  label: string;
  position: [number, number, number];
  target: [number, number, number];
};

type WorldManifest = {
  world_id: string;
  title: string;
  asset?: { url: string; size_bytes: number; triangles: number; meshes: number; materials: number };
  tiles?: { tile_id: string; url: string; center: [number, number]; bounds: [number, number, number, number]; size_bytes: number; triangles: number; meshes: number }[];
  detailed_assets?: { entity_id: string; name: string; url: string; lod: "LOD1" }[];
  totals?: { glb_bytes: number; triangles: number; runtime_nodes: number; tiles: number };
  tile_loading?: "ALL_LOADED" | "DISTANCE_BASED";
  attribution: { text: string; url: string; license: string; license_url: string };
  viewpoints: Viewpoint[];
};

type RuntimeMetrics = { fps: number; calls: number; triangles: number; geometries: number; textures: number };
type BenchmarkReport = {
  status: "PASS";
  scene: string;
  sample_count: number;
  warmup_ms: number;
  duration_ms: number;
  mean_fps: number;
  median_fps: number;
  p1_low_fps: number;
  minimum_fps: number;
  maximum_fps: number;
  renderer: RuntimeMetrics;
  environment: Record<string, string | number | null>;
};

function Model({ id, url, onReady, hideDetailedLod2 = false }: { id: string; url: string; onReady: (id: string) => void; hideDetailedLod2?: boolean }) {
  const gltf = useGLTF(url);
  useEffect(() => {
    const metadata: Record<string, unknown>[] = [];
    gltf.scene.traverse((object) => {
      if (object.userData.entity_id || object.userData.entity_ids) metadata.push({ name: object.name, ...object.userData });
      if (hideDetailedLod2 && object.userData.detailed_asset_id) object.visible = false;
    });
    window.__BGC_GLTF_METADATA__ = [...(window.__BGC_GLTF_METADATA__ ?? []), ...metadata];
    onReady(id);
  }, [gltf, hideDetailedLod2, id, onReady]);
  return <primitive object={gltf.scene} />;
}

function LoadingState() {
  return <Html center className="canvas-message">Loading BGC…</Html>;
}

function CameraRig({ viewpoint }: { viewpoint: Viewpoint }) {
  const { camera } = useThree();
  const controls = useRef<OrbitControlsImpl>(null);
  useEffect(() => {
    camera.position.set(...viewpoint.position);
    camera.lookAt(...viewpoint.target);
    camera.updateProjectionMatrix();
    controls.current?.target.set(...viewpoint.target);
    controls.current?.update();
  }, [camera, viewpoint]);
  return (
    <OrbitControls
      ref={controls}
      makeDefault
      target={viewpoint.target}
      enableDamping
      minDistance={8}
      maxDistance={5000}
      maxPolarAngle={Math.PI / 2.01}
    />
  );
}

function PerformanceProbe({ onSample, onBenchmark }: { onSample: (metrics: RuntimeMetrics) => void; onBenchmark: (report: BenchmarkReport) => void }) {
  const { gl } = useThree();
  const sample = useRef({ started: null as number | null, frames: 0 });
  const benchmark = useRef({ started: null as number | null, previous: null as number | null, frameTimes: [] as number[], finished: false });
  useFrame(() => {
    const now = performance.now();
    if (new URLSearchParams(window.location.search).get("benchmark") === "1" && !benchmark.current.finished) {
      const state = benchmark.current;
      if (state.started === null) state.started = now;
      if (state.previous !== null && now - state.started >= 5000) state.frameTimes.push(now - state.previous);
      state.previous = now;
      if (now - state.started >= 20000 && state.frameTimes.length) {
        const fps = state.frameTimes.map((delta) => 1000 / delta).sort((a, b) => a - b);
        const mean = fps.reduce((total, value) => total + value, 0) / fps.length;
        const median = fps[Math.floor(fps.length / 2)];
        const p1 = fps[Math.max(0, Math.floor(fps.length * 0.01))];
        const context = gl.getContext();
        const debugInfo = context.getExtension("WEBGL_debug_renderer_info");
        const report: BenchmarkReport = {
          status: "PASS",
          scene: new URLSearchParams(window.location.search).get("view") ?? "overview",
          sample_count: fps.length,
          warmup_ms: 5000,
          duration_ms: 15000,
          mean_fps: Number(mean.toFixed(2)),
          median_fps: Number(median.toFixed(2)),
          p1_low_fps: Number(p1.toFixed(2)),
          minimum_fps: Number(fps[0].toFixed(2)),
          maximum_fps: Number(fps[fps.length - 1].toFixed(2)),
          renderer: {
            fps: Math.round(mean), calls: gl.info.render.calls, triangles: gl.info.render.triangles,
            geometries: gl.info.memory.geometries, textures: gl.info.memory.textures,
          },
          environment: {
            user_agent: navigator.userAgent,
            logical_cpu_count: navigator.hardwareConcurrency ?? null,
            device_memory_gb: (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? null,
            viewport: `${window.innerWidth}x${window.innerHeight}`,
            device_pixel_ratio: window.devicePixelRatio,
            gpu: debugInfo ? String(context.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)) : "unavailable",
          },
        };
        window.__BGC_BENCHMARK__ = report;
        onBenchmark(report);
        state.finished = true;
      }
    }
    if (sample.current.started === null) {
      sample.current = { started: now, frames: 0 };
      return;
    }
    sample.current.frames += 1;
    const elapsed = now - sample.current.started;
    if (elapsed < 1000) return;
    const metrics = {
      fps: Math.round((sample.current.frames * 1000) / elapsed),
      calls: gl.info.render.calls,
      triangles: gl.info.render.triangles,
      geometries: gl.info.memory.geometries,
      textures: gl.info.memory.textures,
    };
    onSample(metrics);
    window.__BGC_VIEWER_METRICS__ = metrics;
    sample.current = { started: now, frames: 0 };
  });
  return null;
}

declare global {
  interface Window {
    __BGC_VIEWER_METRICS__?: RuntimeMetrics;
    __BGC_BENCHMARK__?: BenchmarkReport;
    __BGC_GLTF_METADATA__?: Record<string, unknown>[];
  }
}

class ViewerErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };

  static getDerivedStateFromError(error: Error) {
    return { error: error.message || "Unknown WebGL viewer error" };
  }

  render() {
    if (this.state.error) {
      return <div className="viewer-error" role="alert"><strong>Viewer failed to load.</strong><span>{this.state.error}</span></div>;
    }
    return this.props.children;
  }
}

export default function SceneViewer() {
  const [manifest, setManifest] = useState<WorldManifest | null>(null);
  const [manifestError, setManifestError] = useState<string | null>(null);
  const [viewpointIndex, setViewpointIndex] = useState(0);
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const startedAt = useRef<number | null>(null);
  const readyModels = useRef(new Set<string>());
  const expectedModels = (manifest?.asset ? 1 : (manifest?.tiles?.length ?? 0)) + (manifest?.detailed_assets?.length ?? 0);
  const handleModelReady = useCallback((id: string) => {
    readyModels.current.add(id);
    if (readyModels.current.size >= expectedModels) {
      setLoadedAt((current) => current ?? performance.now() - (startedAt.current ?? performance.now()));
    }
  }, [expectedModels]);

  useEffect(() => {
    startedAt.current = performance.now();
    fetch("/world/bgc-world.json")
      .then((response) => {
        if (!response.ok) throw new Error(`Manifest request failed: HTTP ${response.status}`);
        return response.json() as Promise<WorldManifest>;
      })
      .then((data) => {
        setManifest(data);
        const requested = new URLSearchParams(window.location.search).get("view");
        const requestedIndex = data.viewpoints.findIndex((candidate) => candidate.id === requested);
        if (requestedIndex >= 0) setViewpointIndex(requestedIndex);
      })
      .catch((error: Error) => setManifestError(error.message));
  }, []);

  if (manifestError) return <div className="viewer-error" role="alert"><strong>Viewer failed to load.</strong><span>{manifestError}</span></div>;
  if (!manifest) return <div className="viewer-loading">Loading world manifest…</div>;
  const viewpoint = manifest.viewpoints[viewpointIndex];

  return (
    <section className="viewer" aria-label="Interactive real-data BGC pilot viewer">
      <ViewerErrorBoundary>
        <Canvas
          camera={{ position: viewpoint.position, fov: 48, near: 0.1, far: 6000 }}
          dpr={1}
          gl={{ antialias: true, powerPreference: "high-performance", toneMapping: THREE.ACESFilmicToneMapping }}
        >
          <color attach="background" args={["#8196a2"]} />
          <hemisphereLight args={["#d9eeff", "#31412c", 1.5]} />
          <directionalLight position={[120, 220, 80]} intensity={2.4} />
          <Suspense fallback={<LoadingState />}>
            {manifest.asset ? <Model id="legacy-world" url={manifest.asset.url} onReady={handleModelReady} /> : null}
            {manifest.tiles?.map((tile) => <Model key={tile.tile_id} id={tile.tile_id} url={tile.url} onReady={handleModelReady} hideDetailedLod2 />)}
            {manifest.detailed_assets?.map((asset) => <Model key={asset.entity_id} id={asset.entity_id} url={asset.url} onReady={handleModelReady} />)}
          </Suspense>
          <CameraRig viewpoint={viewpoint} />
          <PerformanceProbe onSample={setMetrics} onBenchmark={setBenchmark} />
          <Stats className="fps" />
        </Canvas>
      </ViewerErrorBoundary>
      <nav className="viewpoint-controls" aria-label="Saved inspection viewpoints">
        {manifest.viewpoints.map((candidate, index) => (
          <button key={candidate.id} type="button" className={index === viewpointIndex ? "active" : ""} onClick={() => setViewpointIndex(index)}>
            {candidate.label}
          </button>
        ))}
      </nav>
      <aside className="metrics-panel" aria-live="polite">
        <span>{metrics ? `${metrics.fps} FPS` : "Sampling FPS…"}</span>
        <span>{metrics ? `${metrics.calls} calls · ${metrics.triangles.toLocaleString()} triangles` : `${(manifest.asset?.triangles ?? manifest.totals?.triangles ?? 0).toLocaleString()} asset triangles`}</span>
        <span>{loadedAt === null ? "Loading GLB…" : `Loaded in ${loadedAt.toFixed(0)} ms`}</span>
        {benchmark ? <span
          data-testid="benchmark-result"
          data-report={JSON.stringify(benchmark)}
        >Benchmark {benchmark.scene}: mean {benchmark.mean_fps} · median {benchmark.median_fps} · p1 {benchmark.p1_low_fps} FPS · {benchmark.renderer.calls} calls</span> : null}
      </aside>
      <a className="attribution" href={manifest.attribution.url} target="_blank" rel="noreferrer">{manifest.attribution.text}</a>
    </section>
  );
}
