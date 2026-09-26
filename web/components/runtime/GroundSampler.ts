import type {GroundTriangle} from './m23Data';
type Indexed=GroundTriangle&{bounds:[number,number,number,number]};
/** Loaded detail > local patch > unchanged flat base. No scene-wide raycast. */
export class GroundSampler{
 private zones=new Map<string,Indexed[]>();
 private revision=0;private listeners=new Set<()=>void>();
 subscribe=(listener:()=>void)=>{this.listeners.add(listener);return ()=>{this.listeners.delete(listener);};};
 snapshot=()=>this.revision;
 private changed(){this.revision++;this.listeners.forEach(fn=>fn());}
 register(id:string,triangles:GroundTriangle[]){if(!triangles.length)return;this.zones.set(id,triangles.map(t=>({...t,bounds:[Math.min(...t.points.map(p=>p[0])),Math.min(...t.points.map(p=>p[2])),Math.max(...t.points.map(p=>p[0])),Math.max(...t.points.map(p=>p[2]))]})));this.changed();}
 remove(id:string){if(this.zones.delete(id))this.changed();}
 sample(x:number,z:number,base=0){let height=base,priority=-1;for(const ts of this.zones.values())for(const t of ts){const b=t.bounds;if(x<b[0]-.001||x>b[2]+.001||z<b[1]-.001||z>b[3]+.001)continue;const [a,c,d]=t.points;const det=(c[2]-d[2])*(a[0]-d[0])+(d[0]-c[0])*(a[2]-d[2]);if(Math.abs(det)<1e-9)continue;const u=((c[2]-d[2])*(x-d[0])+(d[0]-c[0])*(z-d[2]))/det;const v=((d[2]-a[2])*(x-d[0])+(a[0]-d[0])*(z-d[2]))/det;const w=1-u-v;if(u<-.0001||v<-.0001||w<-.0001)continue;const h=u*a[1]+v*c[1]+w*d[1];if(t.priority>priority){height=h;priority=t.priority;}else if(t.priority===priority)height=Math.max(height,h);}return height;}
}
export const groundSampler=new GroundSampler();
