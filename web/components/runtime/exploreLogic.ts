import type {BoundsXZ} from './stabilityLogic';
export const EXPLORE_MAX_ALTITUDE=2800;
export const EXPLORE_MAX_PITCH=85*Math.PI/180;
export function flightSpeed(altitude:number){return Math.min(120,Math.max(10,10+altitude*.045));}
export function clampPitch(pitch:number){return Math.max(-EXPLORE_MAX_PITCH,Math.min(EXPLORE_MAX_PITCH,pitch));}
export function exploreFocus(position:number[],forward:number[],bounds:BoundsXZ):[number,number,number]{
 const rayDistance=forward[1]<-.025?-position[1]/forward[1]:Number.POSITIVE_INFINITY;
 const distance=Number.isFinite(rayDistance)?Math.min(12000,Math.max(0,rayDistance)):Math.min(600,300+position[1]*.3);
 return [Math.max(bounds[0]-350,Math.min(bounds[2]+350,position[0]+forward[0]*distance)),Math.max(0,position[1]+forward[1]*distance),Math.max(bounds[1]-350,Math.min(bounds[3]+350,position[2]+forward[2]*distance))];
}
