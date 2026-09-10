import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {MotionDiagram, MotionDiagramProps} from "./MotionDiagram";

export type CaptionWord = {
  text: string;
  start_seconds: number;
  end_seconds: number;
};

export type V6VisualItem = {
  shot_number: number;
  start_seconds: number;
  end_seconds: number;
  src?: string;
  media_type?: "image" | "video";
  representation: "exact_media" | "factual_graphic" | "diagram";
  visual_form: string;
  crop_safe_portrait: boolean;
  graphic?: MotionDiagramProps;
};

export type V6VerticalShortProps = {
  duration_seconds: number;
  audio_src: string;
  captions: CaptionWord[];
  visual_track: V6VisualItem[];
};

const PhotoFrame: React.FC<{item: V6VisualItem}> = ({item}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = interpolate(frame, [0, Math.max(1, durationInFrames - 1)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = 1.025 + progress * 0.045;
  const direction = item.shot_number % 2 === 0 ? -1 : 1;
  const translateX = direction * (progress - 0.5) * 18;
  const style: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: `translateX(${translateX}px) scale(${scale})`,
    transformOrigin: item.shot_number % 2 === 0 ? "58% 50%" : "42% 50%",
  };
  if (!item.src) throw new Error(`V6 media shot ${item.shot_number} has no source`);
  return <AbsoluteFill style={{backgroundColor: "#05070b", overflow: "hidden"}}>
    {item.media_type === "video" ? <OffthreadVideo src={item.src} muted style={style}/> : <Img src={item.src} style={style}/>} 
  </AbsoluteFill>;
};

const GraphicFrame: React.FC<{item: V6VisualItem}> = ({item}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const scale = interpolate(frame, [0, Math.max(1, durationInFrames - 1)], [0.985, 1.025], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mediaStyle: React.CSSProperties = {
    position: "absolute",
    left: 44,
    right: 44,
    top: 82,
    bottom: 360,
    width: "calc(100% - 88px)",
    height: "calc(100% - 442px)",
    objectFit: "contain",
    transform: `scale(${scale})`,
  };
  if (!item.src) throw new Error(`V6 factual graphic shot ${item.shot_number} has no source`);
  return <AbsoluteFill style={{background: "linear-gradient(180deg,#070b12 0%,#0b111b 100%)", overflow: "hidden"}}>
    {item.media_type === "video" ? <OffthreadVideo src={item.src} muted style={mediaStyle}/> : <Img src={item.src} style={mediaStyle}/>} 
  </AbsoluteFill>;
};

const Visual: React.FC<{item: V6VisualItem}> = ({item}) => {
  if (item.representation === "diagram") {
    if (!item.graphic) throw new Error(`V6 diagram shot ${item.shot_number} has no compiled graphic`);
    return <MotionDiagram {...item.graphic}/>;
  }
  const ordinaryPhoto = item.representation === "exact_media" && item.visual_form === "photo";
  if (ordinaryPhoto && !item.crop_safe_portrait) {
    throw new Error(`V6 ordinary photo shot ${item.shot_number} is not portrait-safe`);
  }
  return ordinaryPhoto ? <PhotoFrame item={item}/> : <GraphicFrame item={item}/>;
};

const Captions: React.FC<{words: CaptionWord[]}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = frame / fps;
  let active = words.findIndex((word) => now >= word.start_seconds && now < word.end_seconds);
  if (active < 0) active = words.findIndex((word) => word.start_seconds > now);
  if (active < 0) return null;
  const pageSize = 3;
  const pageStart = Math.floor(active / pageSize) * pageSize;
  const page = words.slice(pageStart, pageStart + pageSize);
  return <div
    data-v6-caption-box="true"
    style={{
      position: "absolute",
      zIndex: 50,
      left: 90,
      right: 90,
      bottom: 176,
      minHeight: 118,
      maxHeight: 260,
      display: "flex",
      flexWrap: "wrap",
      alignItems: "center",
      alignContent: "center",
      justifyContent: "center",
      gap: "8px 12px",
      padding: "12px 18px",
      overflow: "hidden",
      fontFamily: "DejaVu Sans, Arial, sans-serif",
      fontSize: 48,
      fontWeight: 800,
      lineHeight: 1.12,
      textAlign: "center",
      textShadow: "0 3px 10px rgba(0,0,0,.95), 0 0 3px rgba(0,0,0,.9)",
      boxSizing: "border-box",
    }}
  >
    {page.map((word, index) => {
      const globalIndex = pageStart + index;
      return <span key={`${globalIndex}-${word.start_seconds}`} style={{
        color: globalIndex === active ? "#ffe17a" : "#ffffff",
        maxWidth: "100%",
        overflowWrap: "anywhere",
      }}>{word.text}</span>;
    })}
  </div>;
};

export const V6VerticalShort: React.FC<V6VerticalShortProps> = (props) => {
  const {fps} = useVideoConfig();
  return <AbsoluteFill style={{backgroundColor: "#05070b"}}>
    {props.visual_track.map((item) => {
      const from = Math.max(0, Math.round(item.start_seconds * fps));
      const durationInFrames = Math.max(1, Math.round((item.end_seconds - item.start_seconds) * fps));
      return <Sequence key={`shot-${item.shot_number}`} from={from} durationInFrames={durationInFrames} premountFor={fps}>
        <Visual item={item}/>
      </Sequence>;
    })}
    <Audio src={props.audio_src}/>
    <Captions words={props.captions}/>
  </AbsoluteFill>;
};
