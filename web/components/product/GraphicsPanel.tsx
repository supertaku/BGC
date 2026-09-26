import {useEffect,useRef} from 'react';
import type {GraphicsPreset} from '../runtime/graphicsConfig';
export function GraphicsPanel({value,onChange,onClose}:{value:GraphicsPreset;onChange:(value:GraphicsPreset)=>void;onClose:()=>void}){
 const panel=useRef<HTMLElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;panel.current?.querySelector<HTMLInputElement>('input:checked')?.focus();return()=>previous?.focus();},[]);
 return <aside ref={panel} className="product-panel graphics-panel" role="dialog" aria-modal="true" aria-labelledby="graphics-title" onKeyDown={event=>{
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();onClose();}
  if(event.key==='Tab'){const controls=Array.from(panel.current?.querySelectorAll<HTMLElement>('button,input:checked')??[]);const first=controls[0],last=controls.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}
 }}><div className="panel-heading"><h2 id="graphics-title">Graphics</h2><button type="button" className="panel-close" aria-label="Close graphics" onClick={onClose}>Close</button></div><fieldset><legend>Choose your visual quality</legend>{([
 ['performance','Performance','Smoother movement with fewer small details.'],
 ['balanced','Balanced — Recommended','A balance of detail and responsiveness.'],
 ['quality','Quality','More greenery, fine details and shadows.'],
 ] as const).map(([id,title,description])=><label key={id} className="graphics-option"><input type="radio" name="graphics" value={id} checked={value===id} onChange={()=>onChange(id)}/><span><strong>{title}</strong><small>{description}</small></span></label>)}</fieldset></aside>;
}
