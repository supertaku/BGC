"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { useRef } from "react";
import type { BenchmarkReport, EnvironmentQuality, NavigationMode, RuntimeMetrics, RuntimeSummary, TileMode } from "./types";

export function PerformanceProbe({ tileMode, navigation, quality, runtime, loadDurationMs, environmentGroups, onSample, onBenchmark }: {
  tileMode: TileMode;
  navigation: NavigationMode;
  quality: EnvironmentQuality;
  runtime: RuntimeSummary;
  loadDurationMs: number | null;
  environmentGroups: number;
  onSample: (metrics: RuntimeMetrics) => void;
  onBenchmark: (report: BenchmarkReport) => void;
}) {
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
          status: "PASS",
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
          runtime,
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
  });
  return null;
}

declare global {
  interface Window {
    __BGC_STABILITY__?: import("./stability").StabilityState;
    __BGC_VIEWER_METRICS__?: RuntimeMetrics;
    __BGC_BENCHMARK__?: BenchmarkReport;
  }
}
