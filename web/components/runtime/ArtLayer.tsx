import {useRef} from 'react';
import {useFrame} from '@react-three/fiber';
import * as THREE from 'three';
import {Sign} from './SignageLayer';
import {groundSampler} from './GroundSampler';
import {useGraphics} from './GraphicsContext';
import type {ArtAnchor,SignageAnchor} from './m23Data';

function ArtPresence({art}:{art:ArtAnchor}){
 const graphics=useGraphics();
 const group=useRef<THREE.Group>(null);const position=art.position!;
 useFrame(({camera})=>{if(group.current){group.current.visible=Math.hypot(camera.position.x-position[0],camera.position.z-position[2])<graphics.artDistanceM;group.current.position.y=groundSampler.sample(position[0],position[2]);}});
 const label:SignageAnchor={id:art.id,building_id:'public-art',position:[position[0],position[1]+1.9,position[2]],rotation:[0,0,0],width_m:3,height_m:.65,sign_type:'ART_INFORMATION',text:`Art nearby · ${art.title}`,source_id:'art',grounding:'ESTIMATED',rights_status:'NO_ARTWORK_REPRODUCTION',visibility_priority:3,distance_class:'NEAR_DETAIL'};
 return <group ref={group} name={`Art location: ${art.title}`}><mesh position={[position[0],.6,position[2]]}><cylinderGeometry args={[.12,.12,1.2,6]}/><meshStandardMaterial color="#7b8078"/></mesh><Sign anchor={label} billboard/></group>;
}
/** Neutral markers identify art locations; no unlicensed mural/ sculpture copy. */
export function ArtLayer({items}:{items:ArtAnchor[]}){return <>{items.filter(a=>a.position).map(art=><ArtPresence key={art.id} art={art}/>)}</>;}
