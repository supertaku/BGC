export type GraphicsPreset='performance'|'balanced'|'quality';
export type GraphicsConfig={preset:GraphicsPreset;dpr:[number,number];shadows:boolean;nearDetailM:number;microDensity:number;vegetationDensity:number;artDistanceM:number;waterRoughness:number;identity:true;terrain:true;majorSigns:true};
export const GRAPHICS_STORAGE_KEY='bgc.graphics.v1';
export const GRAPHICS_CONFIG:Record<GraphicsPreset,GraphicsConfig>={
 performance:{preset:'performance',dpr:[1,1],shadows:false,nearDetailM:90,microDensity:.3,vegetationDensity:.65,artDistanceM:90,waterRoughness:.5,identity:true,terrain:true,majorSigns:true},
 balanced:{preset:'balanced',dpr:[1,1.5],shadows:false,nearDetailM:170,microDensity:.7,vegetationDensity:.85,artDistanceM:150,waterRoughness:.28,identity:true,terrain:true,majorSigns:true},
 quality:{preset:'quality',dpr:[1.25,2],shadows:true,nearDetailM:240,microDensity:1,vegetationDensity:1,artDistanceM:220,waterRoughness:.16,identity:true,terrain:true,majorSigns:true},
};
export function isGraphicsPreset(value:unknown):value is GraphicsPreset{return value==='performance'||value==='balanced'||value==='quality';}
export function resolveGraphicsPreset(urlValue:string|null,storedValue:string|null):GraphicsPreset{return isGraphicsPreset(urlValue)?urlValue:isGraphicsPreset(storedValue)?storedValue:'balanced';}
