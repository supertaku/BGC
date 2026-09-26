/* eslint-disable react-hooks/immutability -- Imperative camera controls own pointer state and Three.js transforms. */
import {useEffect,useLayoutEffect,useMemo,useRef} from 'react';
import {useFrame,useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {groundSampler} from './GroundSampler';
import {clampPitch,exploreFocus,flightSpeed,EXPLORE_MAX_ALTITUDE} from './exploreLogic';
import type {BoundsXZ} from './stabilityLogic';
export type ExploreControlsHandle={target:THREE.Vector3;domElement:HTMLCanvasElement;update:()=>void};
type Props={controlRef:React.RefObject<ExploreControlsHandle|null>;bounds:BoundsXZ;onStart:()=>void;onChange:()=>void;onEnd:()=>void};
export function ExploreControls({controlRef,bounds,onStart,onChange,onEnd}:Props){
 const {camera,gl}=useThree();const state=useRef({pointer:null as number|null,button:-1,x:0,y:0,keys:new Set<string>()});
 const direction=useMemo(()=>new THREE.Vector3(),[]);const right=useMemo(()=>new THREE.Vector3(),[]);const rotation=useMemo(()=>new THREE.Euler(0,0,0,'YXZ'),[]);
 const handle=useMemo(()=>({target:new THREE.Vector3(),domElement:gl.domElement,update:()=>camera.lookAt(handle.target)}),[camera,gl.domElement]);
 const updateFocus=()=>{camera.getWorldDirection(direction);handle.target.set(...exploreFocus(camera.position.toArray(),direction.toArray(),bounds));};
 const constrain=()=>{camera.position.x=THREE.MathUtils.clamp(camera.position.x,bounds[0]-350,bounds[2]+350);camera.position.z=THREE.MathUtils.clamp(camera.position.z,bounds[1]-350,bounds[3]+350);camera.position.y=THREE.MathUtils.clamp(camera.position.y,groundSampler.sample(camera.position.x,camera.position.z)+1.1,EXPLORE_MAX_ALTITUDE);};
 useLayoutEffect(()=>{controlRef.current=handle;return()=>{controlRef.current=null;};},[controlRef,handle]);
 useEffect(()=>{
  const canvas=gl.domElement;const current=state.current;const originalTabIndex=canvas.getAttribute('tabindex');canvas.tabIndex=0;
  const blocked=()=>document.activeElement instanceof HTMLElement&&!!document.activeElement.closest('input,textarea,select,[contenteditable="true"],.product-panel,[role="dialog"]');
  const release=()=>{const id=current.pointer;current.pointer=null;current.button=-1;current.keys.clear();if(id!==null){if(canvas.hasPointerCapture(id))canvas.releasePointerCapture(id);onEnd();}};
  const down=(event:PointerEvent)=>{if(event.button!==0&&event.button!==2)return;event.preventDefault();release();canvas.focus({preventScroll:true});current.pointer=event.pointerId;current.button=event.button;current.x=event.clientX;current.y=event.clientY;canvas.setPointerCapture(event.pointerId);onStart();};
  const move=(event:PointerEvent)=>{if(current.pointer!==event.pointerId)return;if(!event.buttons||blocked()){release();return;}const dx=event.clientX-current.x,dy=event.clientY-current.y;current.x=event.clientX;current.y=event.clientY;
   if(current.button===2){rotation.setFromQuaternion(camera.quaternion,'YXZ');rotation.y-=dx*.0025;rotation.x=clampPitch(rotation.x-dy*.0025);rotation.z=0;camera.quaternion.setFromEuler(rotation);}
   else {camera.getWorldDirection(direction).setY(0).normalize();right.crossVectors(direction,camera.up).normalize();const scale=Math.max(.025,camera.position.y*.0018);camera.position.addScaledVector(right,-dx*scale).addScaledVector(direction,dy*scale);constrain();}
   updateFocus();onChange();
  };
  const wheel=(event:WheelEvent)=>{if(blocked())return;event.preventDefault();onStart();camera.getWorldDirection(direction);const pixels=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?canvas.clientHeight:1);camera.position.addScaledVector(direction,-THREE.MathUtils.clamp(pixels,-500,500)*Math.max(.025,camera.position.y*.0018));constrain();updateFocus();onChange();onEnd();};
  const keydown=(event:KeyboardEvent)=>{if(current.button!==2||blocked()||!['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight'].includes(event.code))return;event.preventDefault();current.keys.add(event.code);};
  const keyup=(event:KeyboardEvent)=>current.keys.delete(event.code);
  const focus=()=>{if(blocked())release();};const context=(event:MouseEvent)=>event.preventDefault();
  canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('lostpointercapture',release);canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('contextmenu',context);
  window.addEventListener('keydown',keydown);window.addEventListener('keyup',keyup);window.addEventListener('blur',release);document.addEventListener('focusin',focus);
  return()=>{release();canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',release);canvas.removeEventListener('pointercancel',release);canvas.removeEventListener('lostpointercapture',release);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('contextmenu',context);window.removeEventListener('keydown',keydown);window.removeEventListener('keyup',keyup);window.removeEventListener('blur',release);document.removeEventListener('focusin',focus);if(originalTabIndex===null)canvas.removeAttribute('tabindex');else canvas.setAttribute('tabindex',originalTabIndex);};
 // Callbacks are current imperative controller operations; a render does not
 // reset a held pointer, accumulated orientation, or a Search transaction.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[camera,gl.domElement,bounds,onStart,onChange,onEnd]);
 useFrame((_,delta)=>{
  const current=state.current;
  if(current.button===2&&current.keys.size){const x=Number(current.keys.has('KeyD'))-Number(current.keys.has('KeyA'));const z=Number(current.keys.has('KeyW'))-Number(current.keys.has('KeyS'));const length=Math.hypot(x,z);
   if(length){camera.getWorldDirection(direction).setY(0).normalize();right.crossVectors(direction,camera.up).normalize();const speed=flightSpeed(camera.position.y)*(current.keys.has('ShiftLeft')||current.keys.has('ShiftRight')?2:1)*Math.min(delta,.05);camera.position.addScaledVector(direction,z/length*speed).addScaledVector(right,x/length*speed);constrain();onChange();}
  }
  updateFocus();
 },-1);
 return null;
}
