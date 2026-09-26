import assert from 'node:assert/strict';
import fs from 'node:fs';
import {GroundSampler} from '../components/runtime/GroundSampler.ts';
import {distanceToPackage,loadM23Package} from '../components/runtime/m23Data.ts';
const ground=new GroundSampler();
const tri={points:[[0,0,0],[10,2,0],[0,0,10]],priority:1,feature_id:'ramp'};
ground.register('ramp',[tri]);assert.equal(ground.sample(5,2),1);assert.equal(ground.sample(20,0),0);
assert(Number.isNaN(ground.sample(20,0,Number.NaN)));assert.equal(ground.sample(5,2,Number.NaN),1);
ground.register('detail',[{...tri,points:tri.points.map(([x,y,z])=>[x,y+2,z]),priority:2}]);assert.equal(ground.sample(5,2),3);
ground.remove('detail');assert.equal(ground.sample(5,2),1);ground.remove('ramp');assert.equal(ground.sample(5,2),0);
const central=JSON.parse(fs.readFileSync(new URL('../public/world/detail/m23/high_street_central.json',import.meta.url)));
ground.register('central',central.terrain);
for(const t of central.terrain){const x=t.points.reduce((s,p)=>s+p[0],0)/3,z=t.points.reduce((s,p)=>s+p[2],0)/3;assert(Number.isFinite(ground.sample(x,z)));}
assert.equal(distanceToPackage(5,5,[0,0,10,10]),0);assert.equal(distanceToPackage(13,14,[0,0,10,10]),5);
let requests=0;globalThis.fetch=async()=>{requests++;return {ok:true,json:async()=>central};};
const entry={id:central.id,url:'/test'};assert.equal(await loadM23Package(entry),await loadM23Package(entry));assert.equal(requests,1);
console.log('M23 ground interpolation/precedence/unload, real terrain, bounds and request deduplication PASS');
