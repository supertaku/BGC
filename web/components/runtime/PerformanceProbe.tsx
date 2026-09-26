"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { useRef } from "react";
import type { BenchmarkReport, EnvironmentQuality, NavigationMode, RuntimeMetrics, RuntimeSummary, RuntimeRefs, TileMode } from "./types";

export function PerformanceProbe({ refs, tileMode, navigation, quality, runtime, loadDurationMs, environmentGroups, onSample, onBenchmark }: {
  refs: RuntimeRefs;
  tileMode: TileMode;
  navigation: NavigationMode;
  quality: EnvironmentQuality;
  runtime: RuntimeSummary;
  loadDurationMs: number | null;
  environmentGroups: number;
  onSample: (metrics: RuntimeMetrics) => void;
  onBenchmark: (report: BenchmarkReport) => void;
}) {
  const { gl, camera } = useThree();
  const sample = useRef({ started: null as number | null, frames: 0 });
  const benchmark = useRef({ started: null as number | null, previous: null as number | null, frameTimes: [] as number[], finished: false, invalid: new Set<string>(), viewport:"", dpr:0, camera:null as number[]|null });
  useFrame(() => {
    const now = performance.now();
    if (loadDurationMs !== null && runtime.visible > 0 && new URLSearchParams(window.location.search).get("benchmark") === "1" && !benchmark.current.finished) {
      const state = benchmark.current;
      if(document.hidden || !document.hasFocus()) state.invalid.add("BACKGROUND_OR_UNFOCUSED");
      if(state.previous !== null && now-state.previous >= 900) state.invalid.add("THROTTLED_FRAME");
      if (state.started === null) { state.started = now; state.viewport=`${window.innerWidth}x${window.innerHeight}`; state.dpr=window.devicePixelRatio; state.camera=[camera.position.x,camera.position.y,camera.position.z]; window.__BGC_BENCHMARK_CLOCK__ = {start: now, end: now + 20000}; }
      if (state.previous !== null && now - state.started >= 5000) state.frameTimes.push(now - state.previous);
      state.previous = now;
      if (now - state.started >= 20000 && state.frameTimes.length) {
        if(state.viewport!==`${window.innerWidth}x${window.innerHeight}` || state.dpr!==window.devicePixelRatio)state.invalid.add("VIEWPORT_OR_DPR_CHANGED");
        if(runtime.errors)state.invalid.add("RUNTIME_ERROR");
        if(navigation==="WALK" && state.camera && Math.hypot(camera.position.x-state.camera[0],camera.position.z-state.camera[2])<100)state.invalid.add("WALK_PATH_INCOMPLETE");
        const fps = state.frameTimes.map((delta) => 1000 / delta).sort((a, b) => a - b);
        const mean = fps.reduce((total, value) => total + value, 0) / fps.length;
        const context = gl.getContext();
        const debugInfo = context.getExtension("WEBGL_debug_renderer_info");
        const resources = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
        const assets = resources.filter((entry) => {
          const path = new URL(entry.name).pathname;
          return path.startsWith("/models/") || path.startsWith("/world/");
        });
        const initial = loadDurationMs === null ? [] : assets.filter((entry) => entry.startTime <= loadDurationMs);
        const streamed = loadDurationMs === null ? [] : assets.filter((entry) => entry.startTime > loadDurationMs);
        const sum = (entries: PerformanceResourceTiming[], field: "transferSize" | "decodedBodySize") =>
          entries.reduce((total, entry) => total + entry[field], 0);
        const report: BenchmarkReport = {
          status: state.invalid.size ? "INVALID" : "PASS",
          invalid_reasons: [...state.invalid],
          detail: {...(window.__BGC_DETAIL__ ?? {tiles:0,instances:0}), requests: resources.filter(r=>new URL(r.name).pathname === "/world/detail/high-street-public-realm.json").length},
          scene: new URLSearchParams(window.location.search).get("view") ?? "overview",
          quality,
          mode: tileMode,
          navigation,
          sample_count: fps.length,
          warmup_ms: 5000,
          duration_ms: 15000,
          load_duration_ms: loadDurationMs,
          active_environment_groups: environmentGroups,
          transfer: {
            initial_bytes: loadDurationMs === null ? null : sum(initial, "transferSize"),
            streamed_bytes: loadDurationMs === null ? null : sum(streamed, "transferSize"),
            initial_decoded_bytes: loadDurationMs === null ? null : sum(initial, "decodedBodySize"),
            streamed_decoded_bytes: loadDurationMs === null ? null : sum(streamed, "decodedBodySize"),
            timing_supported: loadDurationMs !== null,
          },
          mean_fps: Number(mean.toFixed(2)),
          median_fps: Number(fps[Math.floor(fps.length / 2)].toFixed(2)),
          p1_low_fps: Number(fps[Math.max(0, Math.floor(fps.length * 0.01))].toFixed(2)),
          minimum_fps: Number(fps[0].toFixed(2)),
          maximum_fps: Number(fps[fps.length - 1].toFixed(2)),
          renderer: { fps: Math.round(mean), calls: gl.info.render.calls, triangles: gl.info.render.triangles, geometries: gl.info.memory.geometries, textures: gl.info.memory.textures },
          runtime: {...runtime, camera:[camera.position.x,camera.position.y,camera.position.z],active:refs.activeTileIds.current.size,activeIds:[...refs.activeTileIds.current],visible:refs.visibleTileIds.current.size,visibleIds:[...refs.visibleTileIds.current]},
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
    const metrics = { fps: Math.round((sample.current.frames * 1000) / elapsed), calls: gl.info.render.calls, triangles: gl.info.render.triangles, geometries: gl.info.memory.geometries, textures: gl.info.memory.textures };
    onSample(metrics);
    window.__BGC_VIEWER_METRICS__ = metrics;
    sample.current = { started: now, frames: 0 };
  }, -2);
  return null;
}

declare global {
  interface Window {
    __BGC_BENCHMARK_CLOCK__?: {start:number;end:number};
    __BGC_STABILITY__?: import("./stability").StabilityState;
    __BGC_VIEWER_METRICS__?: RuntimeMetrics;
    __BGC_BENCHMARK__?: BenchmarkReport;
  }
}
