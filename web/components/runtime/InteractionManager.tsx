"use client";

import { useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { findFootprintAt } from "./spatial";
import { isPrimarySelection } from "./stabilityLogic";
import type { Footprint, NavigationMode, RuntimeRefs } from "./types";

function SelectionOutline({ footprint }: { footprint: Footprint }) {
  const geometries = useMemo(() => footprint.rings.map((ring) => new THREE.BufferGeometry().setFromPoints(ring.map(([x, z]) => new THREE.Vector3(x, 0.35, z)))), [footprint]);
  useEffect(() => () => geometries.forEach((geometry) => geometry.dispose()), [geometries]);
  return <>{geometries.map((geometry, index) => (
    <lineLoop key={index} geometry={geometry}>
      <lineBasicMaterial color="#ffb23f" depthTest={false} transparent opacity={0.95} />
    </lineLoop>
  ))}</>;
}

export function InteractionManager({ mode, refs, selected, onSelect }: {
  mode: NavigationMode;
  refs: RuntimeRefs;
  selected: Footprint | null;
  onSelect: (footprint: Footprint | null) => void;
}) {
  const { camera, gl } = useThree();
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const pointer = useMemo(() => new THREE.Vector2(), []);
  const ground = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), []);
  const hit = useMemo(() => new THREE.Vector3(), []);
  const down = useRef<[number, number] | null>(null);

  useEffect(() => {
    const canvas = gl.domElement;
    const onPointerDown = (event: PointerEvent) => { down.current = isPrimarySelection(event.button, 0) ? [event.clientX, event.clientY] : null; };
    const onPointerUp = (event: PointerEvent) => {
      const start = down.current;
      down.current = null;
      if (mode !== "INSPECT" || !start || !isPrimarySelection(event.button, Math.hypot(event.clientX - start[0], event.clientY - start[1]))) return;
      const rect = canvas.getBoundingClientRect();
      pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      if (!raycaster.ray.intersectPlane(ground, hit)) return;
      const footprints = [...refs.activeTileIds.current].flatMap((id) => refs.sidecars.current.get(id)?.footprints ?? []);
      onSelect(findFootprintAt(hit.x, hit.z, footprints));
    };
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointerup", onPointerUp);
    return () => {
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointerup", onPointerUp);
    };
  }, [camera, gl.domElement, ground, hit, mode, onSelect, pointer, raycaster, refs.activeTileIds, refs.sidecars]);

  return selected ? <SelectionOutline footprint={selected} /> : null;
}
