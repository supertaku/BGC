"use client";
/* eslint-disable react-hooks/immutability -- R3F camera, controls, and navigation refs update per frame. */

import { PointerLockControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useCallback, useEffect, useMemo, useRef } from "react";
import type { PointerLockControls as PointerLockControlsImpl } from "three-stdlib";
import * as THREE from "three";
import { pointInFootprint, pointInRing } from "./spatial";
import { acceptFocusSequence, fitCameraToBounds, fitCameraToEntity, resolveStreamAnchors, worldBounds } from "./stabilityLogic";
import {ExploreControls,type ExploreControlsHandle} from './ExploreControls';
import {EXPLORE_MAX_ALTITUDE} from './exploreLogic';
import {benchmarkMotion,type BenchmarkMotionState} from './benchmarkMotion';
import { stability } from "./stability";
import { groundSampler } from "./GroundSampler";
import type { EntityRecord, NavigationMode, RuntimeRefs, Viewpoint, WorldTile } from "./types";

export type FocusRequest = { sequence: number; entity: EntityRecord } | null;
type Transition = { fromPosition: THREE.Vector3; toPosition: THREE.Vector3; fromTarget: THREE.Vector3; toTarget: THREE.Vector3; elapsed: number; duration: number; sequence: number };

function WalkControls({ controlRef }: { controlRef: React.RefObject<PointerLockControlsImpl | null> }) {
  useEffect(() => {
    stability.pointer_lock_mounts += 1;
    const control = controlRef.current;
    return () => { control?.unlock(); stability.pointer_lock_unmounts += 1; };
  }, [controlRef]);
  return <PointerLockControls ref={controlRef} makeDefault selector="canvas" />;
}

export function NavigationController({ mode, viewpoint, bounds, refs, focusRequest, onBoundaryHit, debug }: {
  mode: NavigationMode;
  viewpoint: Viewpoint;
  bounds: WorldTile[];
  refs: RuntimeRefs;
  focusRequest: FocusRequest;
  onBoundaryHit: () => void;
  debug: boolean;
}) {
  const { camera, size, gl, events } = useThree();
  useEffect(()=>{const perspective=camera as THREE.PerspectiveCamera;perspective.near=mode==='WALK'?.08:.4;perspective.far=8000;perspective.updateProjectionMatrix();},[camera,mode]);
  const map = useRef<ExploreControlsHandle>(null);
  const pointer = useRef<PointerLockControlsImpl>(null);
  const keys = useRef(new Set<string>());
  const savedInspect = useRef({ position: new THREE.Vector3(...viewpoint.position), target: new THREE.Vector3(...viewpoint.target) });
  const transition = useRef<Transition | null>(null);
  const pending = useRef<FocusRequest>(null);
  const consumed = useRef<number | null>(null);
  const previousMode = useRef<NavigationMode>("INSPECT");
  const lastViewpoint = useRef<string | null>(null);
  const worldBoundary = useRef<[number, number][]>([]);
  const extent = useMemo(() => worldBounds(bounds), [bounds]);
  const direction = useMemo(() => new THREE.Vector3(), []);
  const benchmarkState=useRef<BenchmarkMotionState>({origin:null,target:null,routes:{}});
  useEffect(()=>{if(new URLSearchParams(window.location.search).get('benchmark_route')?.startsWith('walk-'))fetch('/world/detail/m23r/benchmark-routes.json').then(r=>r.json()).then(routes=>{benchmarkState.current.routes=routes;}).catch(()=>{});},[]);
  const candidate = useMemo(() => new THREE.Vector3(), []);
  const mapInteractionActive = useRef(false);
  const mapStart = useRef<{ camera: THREE.Vector3; target: THREE.Vector3; rotation:THREE.Quaternion } | null>(null);
  const onMapStart = useCallback(() => {
    mapInteractionActive.current = true;
    stability.map_control_starts++;
    mapStart.current = map.current ? { camera: camera.position.clone(), target: map.current.target.clone(),rotation:camera.quaternion.clone() } : null;
    if (transition.current) { transition.current = null; stability.focus_transition_cancels += 1; }
    pending.current = null;
  }, [camera]);
  const onMapChange = useCallback(() => {
    stability.map_control_changes++;
    const initial = mapStart.current;
    if (!initial || !map.current) return;
    const cameraDelta = camera.position.clone().sub(initial.camera);
    if (cameraDelta.lengthSq() > 0.0001 && Math.abs(cameraDelta.y)<.001 && camera.quaternion.angleTo(initial.rotation)<.0001) stability.map_pan_changes++;
    else if (camera.quaternion.angleTo(initial.rotation)>0.0001) stability.map_rotate_changes++;
  }, [camera]);
  const onMapEnd = useCallback(() => {
    mapInteractionActive.current = false;
    mapStart.current = null;
    stability.map_control_ends++;
  }, []);

  useEffect(() => {
    if (mode !== "INSPECT" || !debug) return;
    const canvas = gl.domElement;
    stability.map_dom_element = map.current?.domElement === canvas ? "CANVAS" : "OTHER";
    stability.map_events_connected = events.connected === canvas ? "CANVAS" : events.connected ? "OTHER" : "NONE";
    const start = { x: 0, y: 0 };
    const down = (event: PointerEvent) => {
      if (event.button === 0) stability.map_pointer_down_left++;
      if (event.button === 1) stability.map_pointer_down_middle++;
      if (event.button === 2) stability.map_pointer_down_right++;
      start.x = event.clientX; start.y = event.clientY;
      stability.map_pointer_type = event.pointerType;
      stability.map_pointer_start = [start.x, start.y];
    };
    const move = (event: PointerEvent) => {
      stability.map_pointer_moves++;
      stability.map_pointer_distance_px = Math.hypot(event.clientX - start.x, event.clientY - start.y);
    };
    const up = () => { stability.map_pointer_ups++; };
    const context = () => { stability.map_contextmenus++; };
    canvas.addEventListener("pointerdown", down);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("contextmenu", context);
    return () => {
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("contextmenu", context);
    };
  }, [debug, events.connected, gl.domElement, mode]);

  useEffect(() => {
    fetch("/world/bgc-interactive.json")
      .then((response) => response.json())
      .then((data: { boundary: [number, number][] }) => { worldBoundary.current = data.boundary; })
      .catch(() => { worldBoundary.current = []; });
  }, []);

  useEffect(() => {
    if (mode !== "WALK") return;
    const pressedKeys = keys.current;
    const onDown = (event: KeyboardEvent) => keys.current.add(event.code);
    const onUp = (event: KeyboardEvent) => keys.current.delete(event.code);
    window.addEventListener("keydown", onDown);
    window.addEventListener("keyup", onUp);
    return () => {
      window.removeEventListener("keydown", onDown);
      window.removeEventListener("keyup", onUp);
      pressedKeys.clear();
    };
  }, [mode]);

  useEffect(() => {
    if (mode !== "INSPECT" || lastViewpoint.current === viewpoint.id) return;
    lastViewpoint.current = viewpoint.id;
    const fit = viewpoint.id === "bgc-aerial-full"
      ? fitCameraToBounds(extent, (camera as THREE.PerspectiveCamera).fov, size.width / Math.max(1, size.height))
      : { position: viewpoint.position, target: viewpoint.target };
    camera.position.set(...fit.position);
    camera.position.y=Math.min(EXPLORE_MAX_ALTITUDE,camera.position.y);
    const target = new THREE.Vector3(...fit.target);
    camera.lookAt(target);
    map.current?.target.copy(target);
    map.current?.update();
    refs.focus.current.copy(target);
  }, [camera, extent, mode, refs.focus, size.height, size.width, viewpoint]);

  useEffect(() => {
    const previous = previousMode.current;
    if (mode === "WALK" && previous !== "WALK") {
      savedInspect.current.position.copy(camera.position);
      savedInspect.current.target.copy(map.current?.target ?? refs.focus.current);
      const start = camera.position.y < 100 && pointInRing(camera.position.x, camera.position.z, worldBoundary.current)
        ? new THREE.Vector3(camera.position.x, 1.7, camera.position.z)
        : new THREE.Vector3(-90, 1.7, 170);
      camera.position.copy(start);
      refs.focus.current.copy(start);
    } else if (previous === "WALK" && mode === "INSPECT") {
      camera.position.copy(savedInspect.current.position);
      camera.lookAt(savedInspect.current.target);
      map.current?.target.copy(savedInspect.current.target);
      map.current?.update();
      refs.focus.current.copy(savedInspect.current.target);
    } else if (previous === "TOUR" && mode === "INSPECT") {
      map.current?.target.copy(refs.focus.current);
      map.current?.update();
    }
    if (mode !== previous && transition.current) { stability.focus_transition_cancels += 1; transition.current = null; }
    if (mode === "WALK") pending.current = null;
    if (mode !== "WALK") keys.current.clear();
    previousMode.current = mode;
  }, [camera, mode, refs.focus]);

  useEffect(() => {
    const accepted = acceptFocusSequence(consumed.current, focusRequest?.sequence ?? null);
    if (!focusRequest || accepted === null) return;
    consumed.current = accepted;
    stability.focus_request_count += 1;
    if (transition.current) { stability.focus_transition_cancels += 1; transition.current = null; }
    pending.current = focusRequest;
  }, [focusRequest]);

  useFrame((_, delta) => {
    const benchmarkQuery=new URLSearchParams(window.location.search);
    if(benchmarkQuery.get('benchmark')==='1'&&benchmarkQuery.get('benchmark_route')==='tour'&&window.__BGC_BENCHMARK_CLOCK__&&performance.now()>=window.__BGC_BENCHMARK_CLOCK__.end){transition.current=null;pending.current=null;return;}
    if (!mapInteractionActive.current && pending.current && !transition.current) {
      const request = pending.current;
      const targetRecord = refs.tileRecords.current.get(request.entity.tile_id);
      if (targetRecord?.state === "ERROR") pending.current = null;
      else if (targetRecord?.model_ready) {
        const fit = fitCameraToEntity(request.entity.bounds, request.entity.height_m, (camera as THREE.PerspectiveCamera).fov, size.width / Math.max(1, size.height));
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        transition.current = {
          sequence: request.sequence,
          fromPosition: camera.position.clone(),
          toPosition: new THREE.Vector3(fit.position[0],Math.min(EXPLORE_MAX_ALTITUDE,fit.position[1]),fit.position[2]),
          fromTarget: (map.current?.target ?? refs.focus.current).clone(),
          toTarget: new THREE.Vector3(...fit.target),
          elapsed: 0,
          duration: reduced ? 0.01 : mode === "TOUR" ? 2.8 : 1.2,
        };
        stability.focus_transition_starts += 1;
        pending.current = null;
      }
    }

    if (transition.current && !mapInteractionActive.current) {
      const state = transition.current;
      state.elapsed += delta;
      const raw = Math.min(1, state.elapsed / state.duration);
      const eased = raw * raw * (3 - 2 * raw);
      camera.position.lerpVectors(state.fromPosition, state.toPosition, eased);
      const target = refs.focus.current.lerpVectors(state.fromTarget, state.toTarget, eased);
      camera.lookAt(target);
      map.current?.target.copy(target);
      map.current?.update();
      if (raw >= 1) { transition.current = null; stability.focus_transition_completes += 1; }
    } else if (mode === "INSPECT") {
      if (map.current) {
        const target = map.current.target;
        refs.focus.current.copy(target);
      }
    } else if (mode === "WALK") {
      const scriptedWalk = new URLSearchParams(window.location.search).get("benchmark_walk") === "1" && !!window.__BGC_BENCHMARK_CLOCK__ && performance.now() < window.__BGC_BENCHMARK_CLOCK__.end && !window.__BGC_BENCHMARK__;
      if (pointer.current?.isLocked || scriptedWalk) {
        direction.set(0, 0, 0);
        if (scriptedWalk || keys.current.has("KeyW") || keys.current.has("ArrowUp")) direction.z += 1;
        if (keys.current.has("KeyS") || keys.current.has("ArrowDown")) direction.z -= 1;
        if (keys.current.has("KeyA") || keys.current.has("ArrowLeft")) direction.x -= 1;
        if (keys.current.has("KeyD") || keys.current.has("ArrowRight")) direction.x += 1;
        if (direction.lengthSq() > 0) {
          direction.normalize();
          const speed = keys.current.has("ShiftLeft") || keys.current.has("ShiftRight") ? 18 : 7;
          candidate.copy(camera.position);
          const flatForward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion).setY(0).normalize();
          const flatRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).setY(0).normalize();
          candidate.addScaledVector(flatForward, direction.z * speed * delta).addScaledVector(flatRight, direction.x * speed * delta);
          const insideBoundary = !worldBoundary.current.length || pointInRing(candidate.x, candidate.z, worldBoundary.current);
          const footprints = [...refs.activeTileIds.current].flatMap((id) => refs.sidecars.current.get(id)?.footprints ?? []);
          const collides = footprints.some((footprint) => pointInFootprint(candidate.x, candidate.z, footprint, 0.65));
          if (insideBoundary && !collides) camera.position.copy(candidate);
          else onBoundaryHit();
          camera.position.y = groundSampler.sample(camera.position.x,camera.position.z) + 1.7;
          refs.focus.current.copy(camera.position);
        }
      }
    }
    if(mode === "WALK") camera.position.y = groundSampler.sample(camera.position.x,camera.position.z) + 1.7;
    if(benchmarkMotion(camera,refs.focus.current,benchmarkState.current))map.current?.target.copy(refs.focus.current);
    const priority = pending.current?.entity.center ?? (transition.current ? [transition.current.toTarget.x, transition.current.toTarget.z] as [number, number] : null);
    refs.anchors.current = resolveStreamAnchors(mode, [refs.focus.current.x, refs.focus.current.z], [camera.position.x, camera.position.z], priority);
  });

  return <>
    {mode === "INSPECT" ? <ExploreControls controlRef={map} bounds={extent} onStart={onMapStart} onChange={onMapChange} onEnd={onMapEnd}/> : null}
    {mode === "WALK" ? <WalkControls controlRef={pointer} /> : null}
  </>;
}
