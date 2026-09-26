export type BaseSurface="GROUND"|"ROAD"|"OPEN_SPACE"|"PATH";
type Provenance={id:string;source_id:string;category:string;grounding:string;base_surface:BaseSurface};
export type Surface=Provenance & {outer:[number,number][];holes:[number,number][][];elevation_offset_m:number};
export type Instance=Provenance & {position:[number,number];yaw_rad:number};
export type Tile={surfaces:Record<string,Surface[]>;instances:Record<string,Instance[]>};
export type DetailPackage={schema_version:2;tiles:Record<string,Tile>};
export function validateDetail(value:unknown):DetailPackage {
 const data=value as DetailPackage;
 if(!data || data.schema_version!==2 || !data.tiles || typeof data.tiles!=="object")throw new Error("Unsupported detail schema");
 const ids=new Set<string>();
 for(const tile of Object.values(data.tiles)) {
  if(!tile.surfaces||!tile.instances)throw new Error("Invalid detail tile");
  for(const [category,items] of Object.entries({...tile.surfaces,...tile.instances})) {
   if(!["PAVING_BORDER","PARK_EDGE","ZEBRA_CROSSING","TREE_CLUSTER","BENCH_LINEAR","PLANTER_RECT","LIGHT_POLE_STANDARD"].includes(category)||!Array.isArray(items))throw new Error("Invalid detail records");
   for(const item of items) {
    if(!item.id||ids.has(item.id)||!item.source_id||item.category!==category||!["VERIFIED_GEOGRAPHIC","INFERRED","ESTIMATED"].includes(item.grounding)||!["GROUND","ROAD","OPEN_SPACE","PATH"].includes(item.base_surface))throw new Error("Invalid detail provenance");
    ids.add(item.id);
    if("position" in item) {
     if(item.position.length!==2||!item.position.every(Number.isFinite)||!Number.isFinite(item.yaw_rad))throw new Error("Invalid detail transform");
    } else {
     if(!Array.isArray(item.outer)||item.outer.length<3||!Array.isArray(item.holes)||!([item.outer,...item.holes].every(r=>r.length>=3&&r.every(p=>p.length===2&&p.every(Number.isFinite))))||!(item.elevation_offset_m>0&&item.elevation_offset_m<=.02))throw new Error("Invalid detail surface");
    }
   }
  }
 }
 return data;
}
let cached:Promise<DetailPackage>|undefined;
export function loadDetail():Promise<DetailPackage> {
 return cached??=fetch("/world/detail/high-street-public-realm.json").then(r=>{if(!r.ok)throw new Error(`Detail HTTP ${r.status}`); return r.json();}).then(validateDetail);
}
