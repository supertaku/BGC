"use client";

import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { EnvironmentQuality } from "./types";

const SKY = "#a9bdc6";

export function VisualEnvironment({ quality }: { quality: EnvironmentQuality }) {
  const sun = useRef<THREE.DirectionalLight>(null);
  useFrame(({ camera }) => {
    if (!sun.current || quality !== "FULL") return;
    const x = Math.round(camera.position.x / 25) * 25;
    const z = Math.round(camera.position.z / 25) * 25;
    sun.current.position.set(x + 105, 205, z + 75);
    sun.current.target.position.set(x, 0, z);
    sun.current.target.updateMatrixWorld();
  });
  return <>
    <color attach="background" args={[quality === "LEGACY" ? "#8196a2" : SKY]} />
    {quality !== "LEGACY" ? <fog attach="fog" args={[SKY, 900, 3400]} /> : null}
    <hemisphereLight args={quality === "LEGACY" ? ["#d9eeff", "#31412c", 1.5] : ["#e1f1f5", "#53604c", 1.38]} />
    <directionalLight
      ref={sun}
      position={quality === "LEGACY" ? [120, 220, 80] : [105, 205, 75]}
      intensity={quality === "LEGACY" ? 2.4 : 2.15}
      color={quality === "LEGACY" ? "#ffffff" : "#fff0d6"}
      castShadow={quality === "FULL"}
      shadow-mapSize-width={1024}
      shadow-mapSize-height={1024}
      shadow-camera-near={20}
      shadow-camera-far={480}
      shadow-camera-left={-180}
      shadow-camera-right={180}
      shadow-camera-top={180}
      shadow-camera-bottom={-180}
      shadow-bias={-0.00015}
      shadow-normalBias={0.035}
    />
  </>;
}
