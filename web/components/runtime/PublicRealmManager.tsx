"use client";
import { useEffect, useMemo, useState } from "react";
import { loadDetail, type DetailPackage } from "./publicRealmData";
import { SurfaceDetailLayer } from "./SurfaceDetailLayer";
import { StreetscapeInstanceLayer } from "./StreetscapeInstanceLayer";
import type { EnvironmentQuality } from "./types";
import type { BGCVisualMaterials } from "./visualSystem";
type Props={activeIds:string[];quality:EnvironmentQuality;materials:BGCVisualMaterials};
function LoadedDetail({activeIds,materials,mode}:Props & {mode:string}) {
 const [data,setData]=useState<DetailPackage|null>(null);
 useEffect(()=>{let live=true; loadDetail().then(d=>{if(live)setData(d);}).catch(console.error); return ()=>{live=false;};},[]);
 const tileKey=activeIds.filter(id=>data?.tiles[id]).sort().join("|");
 const tiles=useMemo(()=>tileKey&&data?tileKey.split("|").map(id=>data.tiles[id]):[],[tileKey,data]);
 useEffect(()=>{window.__BGC_DETAIL__={tiles:tiles.length,instances:mode === "surfaces" ? 0 : tiles.reduce((sum,t)=>sum+Object.values(t.instances).reduce((n,i)=>n+i.length,0),0)}; return ()=>{window.__BGC_DETAIL__={tiles:0,instances:0};};},[tiles,mode]);
 if(!data)return null;
 return <>{mode!=="instances"&&<SurfaceDetailLayer tiles={tiles} materials={materials}/ >}{mode!=="surfaces"&&<StreetscapeInstanceLayer tiles={tiles} materials={materials}/>}</>;
}
export function PublicRealmManager(props:Props) {
 const mode=typeof window!=="undefined"?new URLSearchParams(window.location.search).get("detail"):null;
 if(props.quality==="LEGACY"||!mode||!["1","surfaces","instances"].includes(mode))return null;
 return <LoadedDetail {...props} mode={mode}/>;
}
declare global { interface Window {__BGC_DETAIL__?:{tiles:number;instances:number};} }
