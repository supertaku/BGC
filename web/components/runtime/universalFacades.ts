import * as THREE from 'three';

/** Shared PBR shader; facade designs are procedural, never photographic claims. */
export function createUniversalFacadeMaterial(){
 const material=new THREE.MeshStandardMaterial({name:'BGC_UNIVERSAL_FACADE',color:'white',roughness:.58,metalness:.08,side:THREE.FrontSide});
 material.onBeforeCompile=shader=>{
  shader.vertexShader=`attribute vec4 _bgc_facade;
varying vec4 vFacade;
varying vec3 vFacadePosition;
varying vec3 vFacadeNormal;
${shader.vertexShader}`.replace('#include <begin_vertex>',`#include <begin_vertex>
vFacade=_bgc_facade;vFacadePosition=position;vFacadeNormal=normal;`);
  shader.fragmentShader=`varying vec4 vFacade;
varying vec3 vFacadePosition;
varying vec3 vFacadeNormal;
float facadeBand(float value,float width){float aa=max(fwidth(value),.002);return 1.-smoothstep(width-aa,width+aa,abs(fract(value+.5)-.5));}
${shader.fragmentShader}`.replace('#include <color_fragment>',`#include <color_fragment>
float family=vFacade.x,seed=vFacade.y;
float height=vFacadePosition.y-vFacade.z;
vec2 tangent=normalize(vec2(vFacadeNormal.z,-vFacadeNormal.x)+vec2(.000001));
float horizontal=dot(vFacadePosition.xz,tangent);
float floorHeight=mix(3.15,4.05,seed);
vec2 grid=vec2(horizontal/mix(2.4,4.1,seed),height/floorHeight);
float vertical=facadeBand(grid.x,.055),horizontalBand=facadeBand(grid.y,.075);
vec3 stone=mix(vec3(.52,.51,.45),vec3(.76,.75,.69),seed);
vec3 glass=mix(vec3(.11,.21,.26),vec3(.30,.43,.47),seed);
vec3 trim=mix(stone,vec3(.39,.44,.44),.55);
float panel=fract(sin(dot(floor(grid),vec2(17.13,79.31))+seed*123.)*43758.5453);
glass*=mix(.88,1.12,panel);
vec3 facade=glass;
if(family<5.){
 if(family<.5)glass=mix(glass,vec3(.17,.32,.43),.45);
 if(family>2.5&&family<3.5)horizontalBand=facadeBand(grid.y,.16);
 if(family>1.5&&family<2.5)vertical=facadeBand(grid.x,.17);
 if(family>3.5)vertical=facadeBand(grid.x,.24);
 facade=mix(glass,trim,max(vertical,horizontalBand));
}else if(family<9.){
 float window=(1.-facadeBand(grid.x,.19))*(1.-facadeBand(grid.y,.19));
 facade=mix(stone,glass,window);
 if(family<6.5)facade=mix(facade,mix(trim,glass,.25),facadeBand(grid.y-.24,.11));
 if(family>7.5&&height<8.)facade=mix(glass,stone,max(vertical,facadeBand(grid.y,.2)));
}else if(family<12.){
 facade=mix(glass,stone,max(facadeBand(grid.x,.13),facadeBand(grid.y,.22)));
 if(family>9.5&&family<10.5)facade=mix(facade,stone,.32);
 if(family>10.5)facade=mix(facade,vec3(.16,.19,.18),facadeBand(grid.y-.24,.15));
}else if(family<14.){
 facade=mix(vec3(.22,.27,.27),trim,facadeBand(grid.y*4.,.26));
 if(family>12.5)facade=mix(facade,stone,facadeBand(grid.x*2.,.1));
}else if(family<16.5){
 float window=(1.-facadeBand(grid.x,.28))*(1.-facadeBand(grid.y,.27));
 facade=mix(stone,glass,window);
 if(family>14.5&&family<15.5)facade=mix(glass,stone,max(vertical,horizontalBand));
}else{
 float window=(1.-facadeBand(grid.x,.19))*(1.-facadeBand(grid.y,.19));
 facade=mix(vec3(.24,.27,.27),glass,window);
}
// A distinct public ground floor and roof edge belong to every family.
if(height<3.7&&vFacade.z<1.)facade=mix(glass,stone,max(facadeBand(grid.x,.12),facadeBand(height/3.7,.07)));
if(vFacade.w-vFacadePosition.y<.45)facade=trim;
if(abs(vFacadeNormal.y)>.7)facade=mix(vec3(.30,.34,.33),stone,.25);
diffuseColor.rgb*=facade;
`);
 };
 material.customProgramCacheKey=()=> 'bgc-universal-facades-v1';
 return material;
}
