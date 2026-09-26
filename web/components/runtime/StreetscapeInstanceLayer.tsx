"use client";
import { useEffect, useMemo, useRef, useLayoutEffect } from "react";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import heights from "./surface-heights.generated.json";
import type { Instance, Tile } from "./publicRealmData";
import type { BGCVisualMaterials } from "./visualSystem";
function furnitureGeometry(type: string): THREE.BufferGeometry {
  if (type === "TREE_CLUSTER") {
    const trunk = new THREE.CylinderGeometry(.19, .28, 2.2, 6).translate(0, 1.1, 0).toNonIndexed();
    const canopy = new THREE.IcosahedronGeometry(1.85, 0).scale(1, 1.15, 1).translate(0, 3.5, 0);
    const merged = mergeGeometries([trunk, canopy], true);
    trunk.dispose(); canopy.dispose();
    if (!merged) throw new Error("Unable to build tree geometry");
    return merged;
  }
  const box = (x:number,y:number,z:number,px:number,py:number,pz:number) => new THREE.BoxGeometry(x,y,z).translate(px,py,pz);
  const parts = type === "BENCH_LINEAR" ? [box(2,.12,.6,0,.48,0),box(2,.45,.1,0,.78,.25),box(.12,.42,.5,-.75,.21,0),box(.12,.42,.5,.75,.21,0)]
    : type === "PLANTER_RECT" ? [box(2.8,.45,.12,0,.225,-.515),box(2.8,.45,.12,0,.225,.515),box(.12,.45,.91,-1.34,.225,0),box(.12,.45,.91,1.34,.225,0),box(2.56,.08,.91,0,.34,0)]
    : [new THREE.CylinderGeometry(.09,.15,5,6).translate(0,2.5,0),box(.6,.15,.3,.2,5,0)];
  const rim = type === "PLANTER_RECT" ? mergeGeometries(parts.slice(0,4)) : null;
  const merged = rim ? mergeGeometries([rim,parts[4]],true) : mergeGeometries(parts);
  rim?.dispose();
  parts.forEach(p=>p.dispose());
  if (!merged) throw new Error("Unable to build furniture");
  return merged;
}

function InstanceBatch({ items, geometry, material }: { items: Instance[]; geometry: THREE.BufferGeometry; material: THREE.Material | THREE.Material[] }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const object = new THREE.Object3D();
    items.forEach((item, index) => {
      object.position.set(item.position[0], heights[`${item.base_surface}_TOP`], item.position[1]);
      object.rotation.y = item.yaw_rad;
      const variant = item.id.charCodeAt(item.id.length - 1) % 3;
      object.scale.set(1, 1, 1);
      if (item.category === "TREE_CLUSTER") object.scale.set(...([[1,1,1],[.85,1.25,.85],[1.15,.9,1.15]][variant] as [number,number,number]));
      object.updateMatrix();
      ref.current!.setMatrixAt(index, object.matrix);
    });
    ref.current.instanceMatrix.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [items]);
  return <instancedMesh ref={ref} args={[geometry, material, items.length]} dispose={null} />;
}

export function StreetscapeInstanceLayer({tiles,materials}:{tiles:Tile[];materials:BGCVisualMaterials}) {
 const library=useMemo(()=>Object.fromEntries(["TREE_CLUSTER","BENCH_LINEAR","PLANTER_RECT","LIGHT_POLE_STANDARD"].map(t=>[t,furnitureGeometry(t)])),[]);
 useEffect(()=>()=>Object.values(library).forEach(g=>g.dispose()),[library]);
 const groups=useMemo(()=>{const result:Record<string,Instance[]>={}; for(const tile of tiles) for(const [type,items] of Object.entries(tile.instances)) (result[type]??=[]).push(...items); return result;},[tiles]);
 const mapping:Record<string,THREE.Material|THREE.Material[]>={TREE_CLUSTER:[materials.BGC_SOIL,materials.BGC_GRASS],BENCH_LINEAR:materials.BGC_STONE_WARM,PLANTER_RECT:[materials.BGC_STONE_WARM,materials.BGC_SOIL],LIGHT_POLE_STANDARD:materials.BGC_METAL_DARK};
 return <>{Object.entries(groups).map(([type,items])=><InstanceBatch key={type} items={items} geometry={library[type]} material={mapping[type]}/>)}</>;
}
