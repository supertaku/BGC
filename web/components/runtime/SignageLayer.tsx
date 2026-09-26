import {useEffect,useMemo,useRef,useState} from 'react';
import {useFrame} from '@react-three/fiber';
import * as THREE from 'three';
import type {SignageAnchor} from './m23Data';
import {useGraphics} from './GraphicsContext';

const textures=new Map<string,THREE.Texture>();
const requests=new Map<string,Promise<THREE.Texture>>();
function textTexture(anchor:SignageAnchor){
 const key=`${anchor.sign_type}:${anchor.display_text??anchor.text}`;const cached=textures.get(key);if(cached)return cached;
 const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d')!;ctx.fillStyle=anchor.sign_type==='PARK_SIGN'?'#c6a448':'#263a3f';ctx.fillRect(0,0,512,128);ctx.fillStyle='#eee9dc';ctx.textAlign='center';ctx.textBaseline='middle';const title=anchor.display_text??anchor.text;ctx.font=`500 ${Math.min(60,800/Math.max(title.length/2,1))}px sans-serif`;ctx.fillText(title,256,64,480);const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;textures.set(key,texture);return texture;
}
function logoTexture(anchor:SignageAnchor){
 const key=anchor.logo_asset!+JSON.stringify(anchor.logo_uv??null);let request=requests.get(key);
 if(!request){request=new THREE.TextureLoader().loadAsync(anchor.logo_asset!).then(texture=>{texture.colorSpace=THREE.SRGBColorSpace;if(anchor.logo_uv){const [x,y,w,h]=anchor.logo_uv;texture.offset.set(x,y);texture.repeat.set(w,h);}textures.set(key,texture);return texture;});requests.set(key,request);}return request;
}
export function disposeSignageTextures(){textures.forEach(texture=>texture.dispose());textures.clear();requests.clear();}
export function Sign({anchor,billboard=false}:{anchor:SignageAnchor;billboard?:boolean}){
 const graphics=useGraphics();
 const fallback=useMemo(()=>textTexture(anchor),[anchor]);const [logo,setLogo]=useState<THREE.Texture|null>(null);const mesh=useRef<THREE.Mesh>(null);
 useEffect(()=>{if(!anchor.logo_asset)return;let live=true;logoTexture(anchor).then(t=>{if(live)setLogo(t);}).catch(()=>{/* Verified text remains available if the logo fails. */});return()=>{live=false;};},[anchor]);
 useFrame(({camera})=>{if(!mesh.current)return;const distance=camera.position.distanceTo(mesh.current.position);mesh.current.visible=anchor.distance_class==='PERSISTENT_IDENTITY'||distance<graphics.nearDetailM;if(billboard)mesh.current.quaternion.copy(camera.quaternion);});
 return <mesh ref={mesh} position={anchor.position} rotation={anchor.rotation}><planeGeometry args={[anchor.physical_width_m??anchor.width_m,anchor.physical_height_m??anchor.height_m]}/><meshBasicMaterial map={logo??fallback} side={THREE.DoubleSide} alphaTest={.5}/></mesh>;
}
