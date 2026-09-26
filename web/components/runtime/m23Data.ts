import type {WorldManifest,InteractiveManifest} from './types';
export type Vec3=[number,number,number];
export type GroundTriangle={points:[Vec3,Vec3,Vec3];priority:number;feature_id:string};
export type M23Instance={kind:string;material:string;position:Vec3;scale:Vec3;yaw:number;feature_id:string};
export type SignageAnchor={id:string;building_id:string;position:Vec3;rotation:Vec3;width_m:number;height_m:number;sign_type:string;text:string;source_id:string;grounding:string;rights_status:string;visibility_priority:number;facade?:string;physical_width_m?:number;physical_height_m?:number;display_text?:string;logo_asset?:string|null;logo_variant?:string|null;logo_uv?:[number,number,number,number];source_url?:string|null;source_type?:string;verified_visible?:boolean;current_as_of?:string|null;distance_class?:string};
export type ArtAnchor={id:string;title:string;artist:string;position:Vec3|null;rights_status:string;current_status:string;geometry_asset:string|null;texture_asset:string|null};
export type M23Package={schema_version:1;id:string;kind:string;bounds:[number,number,number,number];meshes:Record<string,{vertices:number[];indices:number[]}>;instances:M23Instance[];terrain:GroundTriangle[];signs:SignageAnchor[];art:ArtAnchor[];materials:Record<string,[string,number,number]>};
export type M23Entry={id:string;kind:string;bounds:[number,number,number,number];url:string;activation_m?:number;entity_id?:string;name?:string;height_m?:number;replaces?:string[];replacement_entity_ids?:string[];identity_visibility?:string;focus?:Vec3;walk_position?:Vec3};
export type M23Catalog={schema_version:1;packages:M23Entry[];materials:M23Package['materials']};
export function m23Enabled(){return typeof window!=='undefined'&&new URLSearchParams(window.location.search).get('detail')!=='0';}
const requests=new Map<string,Promise<M23Package>>();let catalog:Promise<M23Catalog>|null=null;
let previewPrepared=false;
export function m23Prepared(){return previewPrepared;}
async function get(url:string){const r=await fetch(url);if(!r.ok)throw new Error(`M23 ${r.status}: ${url}`);return r.json();}
export function loadM23Catalog():Promise<M23Catalog>{return catalog??=get('/world/detail/m23/catalog.json').then(d=>{if(d.schema_version!==1||!Array.isArray(d.packages))throw new Error('Invalid M23 catalog');return d as M23Catalog;});}
export function loadM23Package(entry:M23Entry){let request=requests.get(entry.id);if(!request){request=get(entry.url).then((d:M23Package)=>{if(d.schema_version!==1||d.id!==entry.id||!d.meshes||!Array.isArray(d.instances)||!Array.isArray(d.terrain))throw new Error(`Invalid M23 package ${entry.id}`);return d;});requests.set(entry.id,request);}return request;}
export function distanceToPackage(x:number,z:number,b:M23Entry['bounds']){return Math.hypot(Math.max(b[0]-x,0,x-b[2]),Math.max(b[1]-z,0,z-b[3]));}
export async function applyM23Preview(world:WorldManifest,data:InteractiveManifest):Promise<[WorldManifest,InteractiveManifest]>{
 if(!m23Enabled())return [world,data];
 try {
 const [cat,variants]=await Promise.all([loadM23Catalog(),get('/world/detail/m23r/tile-variants.json')]);
 const tiles=world.tiles?.map(t=>variants.tiles[t.tile_id]?{...t,...variants.tiles[t.tile_id]}:t);
 const entities=data.entities.map(e=>{const a=cat.packages.find(p=>p.entity_id===e.entity_id);return a?{...e,height_m:a.height_m??e.height_m}:e;});
 for(const entry of cat.packages){
  if(!entry.entity_id||entities.some(e=>e.entity_id===entry.entity_id))continue;
  const b=entry.bounds,x=(b[0]+b[2])/2,z=(b[1]+b[3])/2;
  const tile=world.tiles?.find(t=>x>=t.bounds[0]&&x<=t.bounds[2]&&-z>=t.bounds[1]&&-z<=t.bounds[3]);
  if(tile)entities.push({entity_id:entry.entity_id,name:entry.name??entry.id,aliases:[],height_m:entry.height_m??null,height_status:'MAPPED_PART_HEIGHT_WITH_RECORDED_CONFLICTS',building_type:'building',detailed_asset_id:null,tile_id:tile.tile_id,center:[x,z],bounds:b});
 }
 const viewpoints=cat.packages.filter(e=>!e.id.startsWith('street_')&&!e.id.startsWith('lite_')).map(e=>{const b=e.bounds,x=e.focus?.[0]??(b[0]+b[2])/2,z=e.focus?.[2]??(b[1]+b[3])/2;return {id:`m23-${e.id}`,label:`M23 · ${e.name??e.id.replaceAll('_',' ')}`,position:[x+95,Math.max(65,(e.height_m??20)*.65),z+110] as Vec3,target:[x,(e.height_m??0)*.3,z] as Vec3};});
 for(const id of ['high_street_central','track_30th','kasalikasan']){const e=cat.packages.find(p=>p.id===id);if(!e)continue;const x=e.focus?.[0]??(e.bounds[0]+e.bounds[2])/2,z=e.focus?.[2]??(e.bounds[1]+e.bounds[3])/2;viewpoints.push({id:`m23-walk-${id}`,label:`M23 Walk · ${id.replaceAll('_',' ')}`,position:e.walk_position??[x+10,2,z+15],target:[x,2,z]});}
 previewPrepared=true;
 return [{...world,tiles,viewpoints:[...world.viewpoints,...viewpoints]},{...data,entities}];
 } catch(error){console.warn('M23 preview unavailable; retaining base city.',error);previewPrepared=false;return [world,data];}
}
