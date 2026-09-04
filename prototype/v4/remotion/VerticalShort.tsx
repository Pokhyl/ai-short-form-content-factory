import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {MotionDiagram, MotionDiagramProps} from "./MotionDiagram";

type CaptionWord = {text:string; startMs:number; endMs:number};
type VisualItem = {
  beat_id:string;
  start_seconds:number;
  end_seconds:number;
  renderer:"exact_media"|"motion_graphic";
  layout?:"fullscreen"|"contain"|"pip"|"collage"|string;
  visible_subject?:string;
  asset?:{src:string; width?:number; height?:number};
  graphic?:MotionDiagramProps;
};
export type VerticalShortProps = {
  duration_seconds:number;
  profile:{width:number;height:number;fps:number;caption_safe_bottom_px:number;caption_max_width_ratio:number};
  audio:{src:string};
  captions:{items:CaptionWord[]};
  visual_track:VisualItem[];
};

const ExactMedia: React.FC<{item:VisualItem}> = ({item}) => {
  const frame=useCurrentFrame();
  const {durationInFrames}=useVideoConfig();
  const scale=interpolate(frame,[0,Math.max(1,durationInFrames-1)],[1.02,1.075],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
  const contain=item.layout === "contain" || item.layout === "pip" || item.layout === "collage";
  if (!item.asset?.src) return null;
  return <AbsoluteFill style={{backgroundColor:"#05080D",overflow:"hidden"}}>
    {contain ? <Img src={staticFile(item.asset.src)} style={{position:"absolute",width:"100%",height:"100%",objectFit:"cover",filter:"blur(36px)",opacity:0.28,transform:"scale(1.15)"}}/> : null}
    <Img src={staticFile(item.asset.src)} style={{width:"100%",height:"100%",objectFit:contain?"contain":"cover",transform:`scale(${contain?1:scale})`}}/>
  </AbsoluteFill>;
};

const CaptionOverlay: React.FC<{items:CaptionWord[]; bottom:number; maxWidthRatio:number}> = ({items,bottom,maxWidthRatio}) => {
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const now=frame/fps*1000;
  let active=items.findIndex((w)=>now>=w.startMs && now<=w.endMs);
  if (active < 0) active=items.findIndex((w)=>w.startMs>now);
  if (active < 0) return null;
  const pageSize=5;
  const pageStart=Math.floor(active/pageSize)*pageSize;
  const page=items.slice(pageStart,pageStart+pageSize);
  return <div style={{position:"absolute",left:"50%",bottom,transform:"translateX(-50%)",width:`${Math.round(maxWidthRatio*100)}%`,display:"flex",flexWrap:"wrap",justifyContent:"center",gap:"8px 10px",fontFamily:"Arial, sans-serif",fontSize:48,fontWeight:800,lineHeight:1.12,textAlign:"center",textShadow:"0 3px 10px rgba(0,0,0,0.9)",zIndex:20}}>
    {page.map((w,i)=>{
      const global=pageStart+i;
      const current=global===active;
      return <span key={`${global}-${w.startMs}`} style={{color:current?"#FFD36A":"#FFFFFF"}}>{w.text}</span>;
    })}
  </div>;
};

export const VerticalShort: React.FC<VerticalShortProps> = (props) => {
  const {fps}=useVideoConfig();
  return <AbsoluteFill style={{backgroundColor:"#05080D"}}>
    {props.visual_track.map((item)=>{
      const from=Math.round(item.start_seconds*fps);
      const duration=Math.max(1,Math.round((item.end_seconds-item.start_seconds)*fps));
      return <Sequence key={item.beat_id} from={from} durationInFrames={duration} premountFor={fps}>
        {item.renderer === "exact_media" ? <ExactMedia item={item}/> : item.graphic ? <MotionDiagram {...item.graphic}/> : null}
      </Sequence>;
    })}
    <Audio src={staticFile(props.audio.src)}/>
    <CaptionOverlay items={props.captions.items} bottom={props.profile.caption_safe_bottom_px} maxWidthRatio={props.profile.caption_max_width_ratio}/>
  </AbsoluteFill>;
};
