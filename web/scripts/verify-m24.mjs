import assert from 'node:assert/strict';
import {clampPitch,flightSpeed,exploreFocus,EXPLORE_MAX_PITCH} from '../components/runtime/exploreLogic.ts';
import {GRAPHICS_CONFIG,resolveGraphicsPreset} from '../components/runtime/graphicsConfig.ts';
assert.equal(resolveGraphicsPreset(null,null),'balanced');
assert.equal(resolveGraphicsPreset('quality','performance'),'quality');
assert.equal(resolveGraphicsPreset('invalid','performance'),'performance');
assert.equal(resolveGraphicsPreset(null,'invalid'),'balanced');
for(const profile of Object.values(GRAPHICS_CONFIG)) {
 assert.ok(profile.identity && profile.terrain && profile.majorSigns);
 assert.ok(profile.dpr[0]<=profile.dpr[1]);
}
assert.ok(GRAPHICS_CONFIG.performance.nearDetailM<GRAPHICS_CONFIG.quality.nearDetailM);
assert.equal(clampPitch(100),EXPLORE_MAX_PITCH);
assert.equal(clampPitch(-100),-EXPLORE_MAX_PITCH);
assert.equal(clampPitch(.2),.2);
assert.equal(flightSpeed(-100),10);
assert.equal(flightSpeed(10000),120);
assert.ok(flightSpeed(500)>flightSpeed(5));
assert.deepEqual(exploreFocus([0,10,0],[0,-1,0],[-100,-100,100,100]),[0,0,0]);
assert.deepEqual(exploreFocus([1000,1000,0],[-1,-1,0],[-2000,-2000,2000,2000]),[0,0,0]);
assert.ok(exploreFocus([0,100,0],[1,0,0],[-100,-100,100,100]).every(Number.isFinite));
assert.ok(exploreFocus([0,1000,0],[1,0,0],[-100,-100,100,100])[0]<=450);
console.log('M24 profile precedence, identity invariants, pitch/speed/focus bounds PASS');
