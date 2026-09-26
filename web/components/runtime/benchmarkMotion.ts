import * as THREE from 'three';
import {groundSampler} from './GroundSampler';
export type WalkRoute={points:[number,number][];length_m:number};
export type BenchmarkMotionState={origin:THREE.Vector3|null;target:THREE.Vector3|null;routes:Record<string,WalkRoute>};
/** Debug-only deterministic routes. The shared clock is the strict stop gate. */
export function benchmarkMotion(camera:THREE.Camera,focus:THREE.Vector3,state:BenchmarkMotionState){
 const query=new URLSearchParams(window.location.search);const name=query.get('benchmark_route');const clock=window.__BGC_BENCHMARK_CLOCK__;
 if(!name||query.get('benchmark')!=='1'||!clock||performance.now()>=clock.end||window.__BGC_BENCHMARK__)return false;
 if(name==='tour')return false; // The real seven-stop Tour driver owns this route.
 const elapsed=Math.max(0,(performance.now()-clock.start)/1000);
 if(name.startsWith('walk-')){
  const route=state.routes[name];if(!route)return false;
  const distance=(elapsed*7)%(2*route.length_m);const forward=distance<=route.length_m;const d=forward?distance:2*route.length_m-distance;
  const index=Math.min(route.points.length-2,Math.floor(d/2));const t=(d-index*2)/2;const a=route.points[index],b=route.points[index+1];
  camera.position.set(THREE.MathUtils.lerp(a[0],b[0],t),0,THREE.MathUtils.lerp(a[1],b[1],t));camera.position.y=groundSampler.sample(camera.position.x,camera.position.z)+1.7;
  camera.lookAt(camera.position.x+(b[0]-a[0])*(forward?1:-1),camera.position.y,camera.position.z+(b[1]-a[1])*(forward?1:-1));focus.copy(camera.position);
 }else{
  if(!state.origin){state.origin=camera.position.clone();state.target=focus.clone();}
  const target=state.target!;const offset=state.origin.clone().sub(target);const angle=elapsed*.035;const x=offset.x*Math.cos(angle)-offset.z*Math.sin(angle),z=offset.x*Math.sin(angle)+offset.z*Math.cos(angle);
  camera.position.set(target.x+x,state.origin.y,target.z+z);camera.lookAt(target);focus.copy(target);
 }
 return true;
}
