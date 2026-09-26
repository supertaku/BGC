"use client";
import {memo,useCallback,useEffect,useLayoutEffect,useMemo,useRef,useState,useSyncExternalStore} from 'react';
import {useFrame,useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {groundSampler} from './GroundSampler';
import {distanceToPackage,loadM23Catalog,loadM23Package,m23Enabled,m23Prepared,type M23Catalog,type M23Instance,type M23Package} from './m23Data';
import {Sign,disposeSignageTextures} from './SignageLayer';
import {ArtLayer} from './ArtLayer';
import {useGraphics} from './GraphicsContext';
import type {EnvironmentQuality,RuntimeRefs} from './types';

function instanceGeometry(kind:string){if(kind==='sphere')return new THREE.SphereGeometry(1,8,5);if(kind==='cylinder')return new THREE.CylinderGeometry(1,1,1,10);if(kind==='cone')return new THREE.ConeGeometry(1,1,10);return new THREE.BoxGeometry(1,1,1);}
function Instances({items,material,bounds,identity=false,terrainFilter=false}:{items:M23Instance[];material:THREE.Material;bounds:M23Package['bounds'];identity?:boolean;terrainFilter?:boolean}){
 const mesh=useRef<THREE.InstancedMesh>(null);const geometry=useMemo(()=>instanceGeometry(items[0].kind),[items]);
 const graphics=useGraphics();
 const terrainRevision=useSyncExternalStore(groundSampler.subscribe,groundSampler.snapshot,()=>0);
 useEffect(()=>()=>geometry.dispose(),[geometry]);
 useLayoutEffect(()=>{const dummy=new THREE.Object3D();items.forEach((i,n)=>{dummy.position.set(...i.position);dummy.scale.set(...i.scale);let seed=2166136261;for(const character of i.feature_id)seed=Math.imul(seed^character.charCodeAt(0),16777619);const fraction=(seed>>>0)%1000/1000;const density=identity?1:/TREE_|PALM_|SHRUB|FOLIAGE|GROUNDCOVER/.test(i.feature_id)?graphics.vegetationDensity:graphics.microDensity;if(fraction>=density||terrainFilter&&Number.isFinite(groundSampler.sample(i.position[0],i.position[2],Number.NaN)))dummy.scale.setScalar(0);dummy.rotation.set(0,i.yaw,0);dummy.updateMatrix();mesh.current!.setMatrixAt(n,dummy.matrix);});mesh.current!.instanceMatrix.needsUpdate=true;mesh.current!.computeBoundingSphere();},[items,terrainFilter,terrainRevision,graphics,identity]);
 useFrame(({camera})=>{if(mesh.current)mesh.current.visible=identity||distanceToPackage(camera.position.x,camera.position.z,bounds)<graphics.nearDetailM;});
 return <instancedMesh ref={mesh} args={[geometry,material,items.length]} dispose={null}/>;
}
function PackageIdentity({data,visible}:{data:M23Package;visible:boolean}){
 useEffect(()=>{if(visible)groundSampler.register(data.id,data.terrain);return ()=>groundSampler.remove(data.id);},[data,visible]);
 return <>{data.signs.map(s=><Sign key={s.id} anchor={s}/>) }<ArtLayer items={data.art}/></>;
}
const DetailPackage=memo(function DetailPackage({data,visible,materials,onReady}:{data:M23Package;visible:boolean;materials:Record<string,THREE.MeshStandardMaterial>;onReady:(id:string,ready:boolean)=>void}){
 const graphics=useGraphics();
 const meshes=useMemo(()=>{
  return Object.entries(data.meshes).map(([mat,m])=>{const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(m.vertices,3));geometry.setIndex(m.indices);geometry.computeVertexNormals();geometry.computeBoundingSphere();return {mat,geometry};});
 },[data]);
 const groups=useMemo(()=>{const groups=new Map<string,M23Instance[]>();for(const i of data.instances){const identity=data.kind==='landmark'&&!/TREE_|PALM_|SHRUB|FOLIAGE|GROUNDCOVER|BENCH|BIN|PLANTER/.test(i.feature_id);const k=`${identity?'identity':'near'}:${i.kind}:${i.material}`;const a=groups.get(k)??[];a.push(i);groups.set(k,a);}return [...groups.entries()];},[data]);
 useEffect(()=>()=>meshes.forEach(m=>m.geometry.dispose()),[meshes]);
 useLayoutEffect(()=>{onReady(data.id,true);return ()=>onReady(data.id,false);},[data.id,onReady]);
 return <group name={`M23 ${data.id}`} visible={visible}>{meshes.map(m=><mesh key={m.mat} geometry={m.geometry} material={materials[m.mat]} dispose={null} receiveShadow={graphics.shadows} castShadow={graphics.shadows&&data.kind==='landmark'}/>)}{groups.map(([key,items])=><Instances key={key} items={items} material={materials[items[0].material]} bounds={data.bounds} identity={key.startsWith("identity:")} terrainFilter={data.id.startsWith('street_')}/>)}<PackageIdentity data={data} visible={visible}/></group>;
});
function Loaded({refs}:{refs:RuntimeRefs}){
 const {camera}=useThree();
 const graphics=useGraphics();
 const [catalog,setCatalog]=useState<M23Catalog|null>(null);const [desired,setDesired]=useState<string[]>([]);const [loaded,setLoaded]=useState<Record<string,M23Package>>({});
 const failures=useRef(new Set<string>());const tick=useRef(0);const active=useRef(new Set<string>());const mounted=useRef(new Set<string>());const pending=useRef(new Set<string>());
 const onReady=useCallback((id:string,ready:boolean)=>{if(ready)mounted.current.add(id);else mounted.current.delete(id);},[]);
 const materials=useMemo(()=>Object.fromEntries(Object.entries(catalog?.materials??{}).map(([name,[color,roughness,metalness]])=>[name,new THREE.MeshStandardMaterial({name:`M23_${name}`,color,roughness,metalness,side:THREE.FrontSide})])),[catalog]);
 useEffect(()=>()=>Object.values(materials).forEach(m=>m.dispose()),[materials]);
 // eslint-disable-next-line react-hooks/immutability -- Updating a shared Three.js material uniform does not replace cached geometry.
 useEffect(()=>{if(materials.WATER)materials.WATER.roughness=graphics.waterRoughness;},[materials,graphics]);
 useEffect(()=>()=>disposeSignageTextures(),[]);
 useEffect(()=>{let live=true;loadM23Catalog().then(c=>{if(live)setCatalog(c);}).catch(console.error);return ()=>{live=false;};},[]);
 useFrame(()=>{if(!catalog||performance.now()-tick.current<250)return;tick.current=performance.now();
  const owners=new Set<string>();refs.tileScenes.current.forEach(scene=>{if(scene.visible)scene.traverse(o=>{const id=o.userData.detailed_asset_id as string|undefined;if(id?.startsWith('m23:'))owners.add(id.slice(4));});});
  const next=catalog.packages.filter(e=>e.kind==='landmark'?owners.has(e.id):camera.position.y<650&&refs.anchors.current.some(a=>distanceToPackage(a.x,a.z,e.bounds)<(e.activation_m??150)+(active.current.has(e.id)?40:0))).map(e=>e.id).sort();
  if(next.join('|')!==desired.join('|'))setDesired(next);
  // React has committed the replacement before its fallback can be hidden.
  const ready=new Set(next.filter(id=>mounted.current.has(id)&&desired.includes(id)));active.current=ready;
  refs.tileScenes.current.forEach(scene=>scene.traverse(o=>{const id=o.userData.detailed_asset_id as string|undefined;if(id?.startsWith('m23:'))o.visible=!ready.has(id.slice(4));}));
  window.__BGC_M23__={active:[...ready],requests:Object.keys(loaded).length,failures:[...failures.current],instances:[...ready].reduce((n,id)=>n+loaded[id].instances.length,0)};
 });
 useEffect(()=>{if(!catalog)return;for(const id of desired){if(loaded[id]||pending.current.has(id)||failures.current.has(id))continue;pending.current.add(id);const entry=catalog.packages.find(e=>e.id===id)!;loadM23Package(entry).then(data=>setLoaded(prev=>({...prev,[id]:data}))).catch(error=>{failures.current.add(id);console.error(error);}).finally(()=>pending.current.delete(id));}},[catalog,desired,loaded]);
 useEffect(()=>()=>{refs.tileScenes.current.forEach(scene=>scene.traverse(o=>{if(String(o.userData.detailed_asset_id).startsWith('m23:'))o.visible=true;}));},[refs.tileScenes]);
 return <>{Object.values(loaded).map(data=><DetailPackage key={data.id} data={data} visible={desired.includes(data.id)} materials={materials} onReady={onReady}/>)}</>;
}
export function M23Manager({refs,quality}:{refs:RuntimeRefs;quality:EnvironmentQuality}){return m23Enabled()&&m23Prepared()&&quality!=='LEGACY'?<Loaded refs={refs}/>:null;}
declare global{interface Window{__BGC_M23__?:{active:string[];requests:number;failures:string[];instances:number}}}

