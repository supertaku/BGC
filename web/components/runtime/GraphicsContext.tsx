import {createContext,useContext,useEffect} from 'react';
import {useThree} from '@react-three/fiber';
import {GRAPHICS_CONFIG,type GraphicsConfig} from './graphicsConfig';
export const GraphicsContext=createContext<GraphicsConfig>(GRAPHICS_CONFIG.balanced);
export const useGraphics=()=>useContext(GraphicsContext);
export function GraphicsRenderer(){
 const {gl}=useThree();const config=useGraphics();
 useEffect(()=>{window.__BGC_GRAPHICS__={...config,rendererDpr:gl.getPixelRatio(),reversedDepthBuffer:gl.capabilities.reversedDepthBuffer};},[gl,config]);
 return null;
}
declare global{interface Window{__BGC_GRAPHICS__?:GraphicsConfig&{rendererDpr:number;reversedDepthBuffer:boolean}}}
