"use client";
import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {useFrame,useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {GroundSampler,groundSampler} from './GroundSampler';
import {distanceToPackage,loadM23Catalog,loadM23Package,m23Enabled,m23Prepared,type M23Catalog,type M23Instance,type M23Package,type SignageAnchor} from './m23Data';
import type {EnvironmentQuality,RuntimeRefs} from './types';

function instanceGeometry(kind:string){if(kind==='sphere')return new THREE.SphereGeometry(1,8,5);if(kind==='cylinder')return new THREE.CylinderGeometry(1,1,1,10);if(kind==='cone')return new THREE.ConeGeometry(1,1,10);return new THREE.BoxGeometry(1,1,1);}
function Instances({items,material}:{items:M23Instance[];material:THREE.Material}){
 const mesh=useRef<THREE.InstancedMesh>(null);const geometry=useMemo(()=>instanceGeometry(items[0].kind),[items]);
 useEffect(()=>()=>geometry.dispose(),[geometry]);
 useLayoutEffect(()=>{const dummy=new THREE.Object3D();items.forEach((i,n)=>{dummy.position.set(...i.position);dummy.scale.set(...i.scale);dummy.rotation.set(0,i.yaw,0);dummy.updateMatrix();mesh.current!.setMatrixAt(n,dummy.matrix);});mesh.current!.instanceMatrix.needsUpdate=true;mesh.current!.computeBoundingSphere();},[items]);
 return <instancedMesh ref={mesh} args={[geometry,material,items.length]} dispose={null}/>;
}
function Sign({anchor}:{anchor:SignageAnchor}){
 const texture=useMemo(()=>{const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d')!;ctx.fillStyle=anchor.sign_type==='PARK_SIGN'?'#c6a448':'#263a3f';ctx.fillRect(0,0,512,128);ctx.fillStyle='#eee9dc';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`500 ${Math.min(60,800/Math.max(anchor.text.length/2,1))}px sans-serif`;ctx.fillText(anchor.text,256,64,480);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;},[anchor]);
 useEffect(()=>()=>texture.dispose(),[texture]);
 return <mesh position={anchor.position} rotation={anchor.rotation}><planeGeometry args={[anchor.width_m,anchor.height_m]}/><meshBasicMaterial map={texture} side={THREE.DoubleSide}/></mesh>;
}
function PackageIdentity({data}:{data:M23Package}){
 useEffect(()=>{groundSampler.register(data.id,data.terrain);return ()=>groundSampler.remove(data.id);},[data]);
 return <>{data.signs.slice(0,3).map(s=><Sign key={s.id} anchor={s}/>)}</>;
}
function DetailBatches({packages,materials}:{packages:M23Package[];materials:Record<string,THREE.MeshStandardMaterial>}){
 const meshes=useMemo(()=>{
  const merged=new Map<string,{vertices:number[];indices:number[]}>();
  for(const data of packages)for(const [mat,m] of Object.entries(data.meshes)){const target=merged.get(mat)??{vertices:[],indices:[]};const offset=target.vertices.length/3;for(const v of m.vertices)target.vertices.push(v);for(const i of m.indices)target.indices.push(offset+i);merged.set(mat,target);}
  return [...merged.entries()].map(([mat,m])=>{const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(m.vertices,3));geometry.setIndex(m.indices);geometry.computeVertexNormals();geometry.computeBoundingSphere();return {mat,geometry};});
 },[packages]);
 const groups=useMemo(()=>{const terrain=new GroundSampler();for(const data of packages)terrain.register(data.id,data.terrain);const groups=new Map<string,M23Instance[]>();for(const data of packages)for(const i of data.instances){if(data.id.startsWith('street_')&&Number.isFinite(terrain.sample(i.position[0],i.position[2],Number.NaN)))continue;const k=`${i.kind}:${i.material}`;const a=groups.get(k)??[];a.push(i);groups.set(k,a);}return [...groups.entries()];},[packages]);
 useEffect(()=>()=>meshes.forEach(m=>m.geometry.dispose()),[meshes]);
 return <group name="M23 spatial detail">{meshes.map(m=><mesh key={m.mat} geometry={m.geometry} material={materials[m.mat]} dispose={null}/>)}{groups.map(([key,items])=><Instances key={key} items={items} material={materials[items[0].material]}/>)}{packages.map(data=><PackageIdentity key={data.id} data={data}/>)}</group>;
}
function Loaded({refs}:{refs:RuntimeRefs}){
 const {camera}=useThree();
 const [catalog,setCatalog]=useState<M23Catalog|null>(null);const [desired,setDesired]=useState<string[]>([]);const [loaded,setLoaded]=useState<Record<string,M23Package>>({});
 const failures=useRef(new Set<string>());const tick=useRef(0);const active=useRef(new Set<string>());
 const materials=useMemo(()=>Object.fromEntries(Object.entries(catalog?.materials??{}).map(([name,[color,roughness,metalness]])=>[name,new THREE.MeshStandardMaterial({name:`M23_${name}`,color,roughness,metalness,side:THREE.DoubleSide})])),[catalog]);
 useEffect(()=>()=>Object.values(materials).forEach(m=>m.dispose()),[materials]);
 useEffect(()=>{let live=true;loadM23Catalog().then(c=>{if(live)setCatalog(c);}).catch(console.error);return ()=>{live=false;};},[]);
 useFrame(()=>{if(!catalog||performance.now()-tick.current<250)return;tick.current=performance.now();const next=catalog.packages.filter(e=>camera.position.y<650 && refs.anchors.current.some(a=>distanceToPackage(a.x,a.z,e.bounds)<(e.activation_m??150)+(active.current.has(e.id)?40:0))).map(e=>e.id).sort();if(next.join('|')!==desired.join('|'))setDesired(next);const ready=new Set(next.filter(id=>loaded[id]&&desired.includes(id)));active.current=ready;refs.tileScenes.current.forEach(scene=>scene.traverse(o=>{const id=o.userData.detailed_asset_id as string|undefined;if(id?.startsWith('m23:'))o.visible=!ready.has(id.slice(4));}));window.__BGC_M23__={active:[...ready],requests:Object.keys(loaded).length,failures:[...failures.current],instances:[...ready].reduce((n,id)=>n+loaded[id].instances.length,0)};});
 useEffect(()=>{if(!catalog)return;let live=true;for(const id of desired){if(loaded[id]||failures.current.has(id))continue;const entry=catalog.packages.find(e=>e.id===id)!;loadM23Package(entry).then(data=>{if(live)setLoaded(prev=>({...prev,[id]:data}));}).catch(error=>{failures.current.add(id);console.error(error);});}return ()=>{live=false;};},[catalog,desired,loaded]);
 useEffect(()=>()=>{refs.tileScenes.current.forEach(scene=>scene.traverse(o=>{if(String(o.userData.detailed_asset_id).startsWith('m23:'))o.visible=true;}));},[refs.tileScenes]);
 const visiblePackages=useMemo(()=>desired.filter(id=>loaded[id]).map(id=>loaded[id]),[desired,loaded]);
 return <DetailBatches packages={visiblePackages} materials={materials}/>;
}
export function M23Manager({refs,quality}:{refs:RuntimeRefs;quality:EnvironmentQuality}){return m23Enabled()&&m23Prepared()&&quality!=='LEGACY'?<Loaded refs={refs}/>:null;}
declare global{interface Window{__BGC_M23__?:{active:string[];requests:number;failures:string[];instances:number}}}

