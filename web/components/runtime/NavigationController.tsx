"use client";
/* eslint-disable react-hooks/immutability -- camera transforms and input vectors are intentionally updated in useFrame. */

import { OrbitControls, PointerLockControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import type { OrbitControls as OrbitControlsImpl, PointerLockControls as PointerLockControlsImpl } from "three-stdlib";
import * as THREE from "three";
import { pointInFootprint, pointInRing } from "./spatial";
import type { EntityRecord, NavigationMode, RuntimeRefs, Viewpoint } from "./types";

export type FocusRequest = { sequence: number; entity: EntityRecord } | null;

export function NavigationController({ mode, viewpoint, refs, focusRequest, tourStop, onBoundaryHit }: {
  mode: NavigationMode;
  viewpoint: Viewpoint;
  refs: RuntimeRefs;
  focusRequest: FocusRequest;
  tourStop: EntityRecord | null;
  onBoundaryHit: () => void;
}) {
  const { camera } = useThree();
  const orbit = useRef<OrbitControlsImpl>(null);
  const pointer = useRef<PointerLockControlsImpl>(null);
  const keys = useRef(new Set<string>());
  const savedInspect = useRef({ position: new THREE.Vector3(...viewpoint.position), target: new THREE.Vector3(...viewpoint.target) });
  const transition = useRef<{ fromPosition: THREE.Vector3; toPosition: THREE.Vector3; fromTarget: THREE.Vector3; toTarget: THREE.Vector3; elapsed: number; duration: number } | null>(null);
  const boundary = useMemo(() => refs.sidecars.current, [refs.sidecars]);
  const worldBoundary = useRef<[number, number][]>([]);
  const previousMode = useRef<NavigationMode>(mode);
  const direction = useMemo(() => new THREE.Vector3(), []);
  const candidate = useMemo(() => new THREE.Vector3(), []);

  useEffect(() => {
    const onDown = (event: KeyboardEvent) => keys.current.add(event.code);
    const onUp = (event: KeyboardEvent) => keys.current.delete(event.code);
    window.addEventListener("keydown", onDown);
    window.addEventListener("keyup", onUp);
    return () => {
      window.removeEventListener("keydown", onDown);
      window.removeEventListener("keyup", onUp);
    };
  }, []);

  useEffect(() => {
    fetch("/world/bgc-interactive.json")
      .then((response) => response.json())
      .then((data: { boundary: [number, number][] }) => { worldBoundary.current = data.boundary; })
      .catch(() => { worldBoundary.current = []; });
  }, []);

  useEffect(() => {
    if (mode !== "INSPECT") return;
    camera.position.set(...viewpoint.position);
    const target = new THREE.Vector3(...viewpoint.target);
    camera.lookAt(target);
    orbit.current?.target.copy(target);
    orbit.current?.update();
    refs.focus.current.copy(target);
  }, [camera, mode, refs.focus, viewpoint]);

  useEffect(() => {
    const previous = previousMode.current;
    if (mode === "WALK" && previous !== "WALK") {
      savedInspect.current.position.copy(camera.position);
      savedInspect.current.target.copy(orbit.current?.target ?? refs.focus.current);
      const start = camera.position.y < 100 && pointInRing(camera.position.x, camera.position.z, worldBoundary.current)
        ? new THREE.Vector3(camera.position.x, 1.7, camera.position.z)
        : new THREE.Vector3(-90, 1.7, 170);
      camera.position.copy(start);
      refs.focus.current.copy(start);
    } else if (previous === "WALK" && mode === "INSPECT") {
      camera.position.copy(savedInspect.current.position);
      orbit.current?.target.copy(savedInspect.current.target);
      orbit.current?.update();
      refs.focus.current.copy(savedInspect.current.target);
    }
    previousMode.current = mode;
  }, [camera, mode, refs.focus]);

  useEffect(() => {
    const entity = focusRequest?.entity ?? (mode === "TOUR" ? tourStop : null);
    if (!entity) return;
    const height = Math.max(20, entity.height_m ?? 20);
    const target = new THREE.Vector3(entity.center[0], Math.min(height * 0.45, 45), entity.center[1]);
    const position = new THREE.Vector3(entity.center[0] + Math.max(55, height * 0.55), Math.max(38, height * 0.72), entity.center[1] + Math.max(65, height * 0.62));
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    transition.current = {
      fromPosition: camera.position.clone(),
      toPosition: position,
      fromTarget: (orbit.current?.target ?? refs.focus.current).clone(),
      toTarget: target,
      elapsed: 0,
      duration: reduced ? 0.01 : mode === "TOUR" ? 2.8 : 1.2,
    };
  }, [camera, focusRequest, mode, refs.focus, tourStop]);

  useFrame((_, delta) => {
    if (transition.current) {
      const state = transition.current;
      state.elapsed += delta;
      const raw = Math.min(1, state.elapsed / state.duration);
      const eased = raw * raw * (3 - 2 * raw);
      camera.position.lerpVectors(state.fromPosition, state.toPosition, eased);
      const target = refs.focus.current.lerpVectors(state.fromTarget, state.toTarget, eased);
      camera.lookAt(target);
      orbit.current?.target.copy(target);
      orbit.current?.update();
      if (raw >= 1) transition.current = null;
      return;
    }

    if (mode === "INSPECT") {
      if (orbit.current) refs.focus.current.copy(orbit.current.target);
      return;
    }
    if (mode !== "WALK" || !pointer.current?.isLocked) return;
    direction.set(0, 0, 0);
    if (keys.current.has("KeyW") || keys.current.has("ArrowUp")) direction.z += 1;
    if (keys.current.has("KeyS") || keys.current.has("ArrowDown")) direction.z -= 1;
    if (keys.current.has("KeyA") || keys.current.has("ArrowLeft")) direction.x -= 1;
    if (keys.current.has("KeyD") || keys.current.has("ArrowRight")) direction.x += 1;
    if (direction.lengthSq() === 0) return;
    direction.normalize();
    const speed = keys.current.has("ShiftLeft") || keys.current.has("ShiftRight") ? 18 : 7;
    const forward = direction.z * speed * delta;
    const right = direction.x * speed * delta;
    candidate.copy(camera.position);
    const quaternion = camera.quaternion.clone();
    const flatForward = new THREE.Vector3(0, 0, -1).applyQuaternion(quaternion).setY(0).normalize();
    const flatRight = new THREE.Vector3(1, 0, 0).applyQuaternion(quaternion).setY(0).normalize();
    candidate.addScaledVector(flatForward, forward).addScaledVector(flatRight, right);
    const insideBoundary = !worldBoundary.current.length || pointInRing(candidate.x, candidate.z, worldBoundary.current);
    const footprints = [...refs.activeTileIds.current].flatMap((id) => boundary.get(id)?.footprints ?? []);
    const collides = footprints.some((footprint) => pointInFootprint(candidate.x, candidate.z, footprint, 0.65));
    if (insideBoundary && !collides) camera.position.copy(candidate);
    else onBoundaryHit();
    camera.position.y = 1.7;
    refs.focus.current.copy(camera.position);
  });

  return <>
    {mode === "INSPECT" ? <OrbitControls ref={orbit} makeDefault enableDamping dampingFactor={0.08} minDistance={8} maxDistance={5000} maxPolarAngle={Math.PI / 2.01} /> : null}
    <PointerLockControls ref={pointer} makeDefault={mode === "WALK"} selector="#walk-lock-button" />
  </>;
}
