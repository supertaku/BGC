import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateDetail, loadDetail} from '../components/runtime/publicRealmData.ts';
const data=JSON.parse(fs.readFileSync(new URL('../public/world/detail/high-street-public-realm.json',import.meta.url)));
validateDetail(data);
for(const mutate of [d=>d.schema_version=1,d=>Object.values(d.tiles)[0].surfaces.PAVING_BORDER[0].source_id='',d=>Object.values(d.tiles)[0].surfaces.PAVING_BORDER[0].elevation_offset_m=-1]) {
 const invalid=structuredClone(data);mutate(invalid);assert.throws(()=>validateDetail(invalid));
}
const instance=Object.values(data.tiles).flatMap(t=>Object.values(t.instances).flat())[0];
for(const value of [NaN,Infinity,undefined]) {
 const invalid=structuredClone(data);
 Object.values(invalid.tiles).flatMap(t=>Object.values(t.instances).flat()).find(i=>i.id===instance.id).yaw_rad=value;
 assert.throws(()=>validateDetail(invalid));
}
let requests=0;globalThis.fetch=async()=>{requests++;return {ok:true,json:async()=>data};};
assert.equal(requests,0);
assert.equal(await loadDetail(),await loadDetail());assert.equal(requests,1);
console.log('Detail schema, finite fields, elevation bounds, provenance, lazy cache PASS');
