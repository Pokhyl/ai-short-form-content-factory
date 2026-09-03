import React from "react";
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";

export type MotionElement = {
  id: string;
  type: "rect" | "circle" | "line" | "polygon" | "text";
  x?: number; y?: number; width?: number; height?: number; rx?: number;
  cx?: number; cy?: number; r?: number;
  x1?: number; y1?: number; x2?: number; y2?: number;
  points?: Array<[number, number]>;
  text?: string; fontSize?: number; fontWeight?: number;
  fill?: string; stroke?: string; strokeWidth?: number;
  opacity?: number;
  enter?: [number, number];
  from?: {x?: number; y?: number; scale?: number; opacity?: number};
  draw?: [number, number];
  arrow?: boolean;
  pulse?: {start: number; end: number; amount?: number};
  move?: {start: number; end: number; x?: number; y?: number; scale?: number};
};

export type MotionDiagramProps = {
  durationSeconds: number;
  background?: string;
  title?: string;
  elements: MotionElement[];
};

const clampProgress = (t: number, range?: [number, number]) => {
  if (!range) return 1;
  if (range[1] <= range[0]) return t >= range[1] ? 1 : 0;
  return interpolate(t, range, [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
};

const Element: React.FC<{spec: MotionElement; t: number}> = ({spec, t}) => {
  const enter = clampProgress(t, spec.enter);
  const from = spec.from ?? {};
  let tx = (from.x ?? 0) * (1 - enter);
  let ty = (from.y ?? 0) * (1 - enter);
  let scale = (from.scale ?? 1) + (1 - (from.scale ?? 1)) * enter;
  if (spec.move) {
    const move = clampProgress(t, [spec.move.start, spec.move.end]);
    tx += (spec.move.x ?? 0) * move;
    ty += (spec.move.y ?? 0) * move;
    scale *= 1 + ((spec.move.scale ?? 1) - 1) * move;
  }
  if (spec.pulse && t >= spec.pulse.start && t <= spec.pulse.end) {
    const local = (t - spec.pulse.start) / Math.max(0.001, spec.pulse.end - spec.pulse.start);
    scale *= 1 + Math.sin(local * Math.PI * 4) * (spec.pulse.amount ?? 0.05);
  }
  const opacity = (spec.opacity ?? 1) * ((from.opacity ?? 0) + (1 - (from.opacity ?? 0)) * enter);
  const svgTransform = `translate(${tx} ${ty})`;
  const common = {opacity, transform: `scale(${scale})`, transformBox: "fill-box" as const, transformOrigin: "center"};

  if (spec.type === "rect") {
    return <rect x={spec.x} y={spec.y} width={spec.width} height={spec.height} rx={spec.rx ?? 0}
      fill={spec.fill ?? "none"} stroke={spec.stroke} strokeWidth={spec.strokeWidth ?? 0} transform={svgTransform} style={common}/>;
  }
  if (spec.type === "circle") {
    return <circle cx={spec.cx} cy={spec.cy} r={spec.r} fill={spec.fill ?? "none"}
      stroke={spec.stroke} strokeWidth={spec.strokeWidth ?? 0} transform={svgTransform} style={common}/>;
  }
  if (spec.type === "polygon") {
    const points=(spec.points ?? []).map(([x,y])=>`${x},${y}`).join(" ");
    return <polygon points={points} fill={spec.fill ?? "none"} stroke={spec.stroke}
      strokeWidth={spec.strokeWidth ?? 0} strokeLinejoin="round" transform={svgTransform} style={common}/>;
  }
  if (spec.type === "text") {
    return <text x={spec.x} y={spec.y} fill={spec.fill ?? "#fff"} fontSize={spec.fontSize ?? 34}
      fontWeight={spec.fontWeight ?? 600} fontFamily="Arial, sans-serif" textAnchor="middle" transform={svgTransform} style={common}>{spec.text}</text>;
  }
  const draw = clampProgress(t, spec.draw);
  const x1=spec.x1 ?? 0, y1=spec.y1 ?? 0, x2=spec.x2 ?? x1, y2=spec.y2 ?? y1;
  const ex=x1+(x2-x1)*draw, ey=y1+(y2-y1)*draw;
  const angle=Math.atan2(ey-y1, ex-x1);
  const size=spec.arrow ? 16 : 0;
  const p1=[ex,ey] as const;
  const p2=[ex-size*Math.cos(angle-Math.PI/6), ey-size*Math.sin(angle-Math.PI/6)] as const;
  const p3=[ex-size*Math.cos(angle+Math.PI/6), ey-size*Math.sin(angle+Math.PI/6)] as const;
  return <g transform={svgTransform} style={common}>
    <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={spec.stroke ?? "#fff"} strokeWidth={spec.strokeWidth ?? 5} strokeLinecap="round"/>
    {spec.arrow && draw > 0.03 ? <polygon points={`${p1[0]},${p1[1]} ${p2[0]},${p2[1]} ${p3[0]},${p3[1]}`} fill={spec.stroke ?? "#fff"}/> : null}
  </g>;
};

export const MotionDiagram: React.FC<MotionDiagramProps> = ({background="#0B1020", title, elements}) => {
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const t=frame/fps;
  return <AbsoluteFill style={{background}}>
    <svg width="100%" height="100%" viewBox="0 0 720 1280" preserveAspectRatio="xMidYMid meet">
      {title ? <text x="360" y="90" fill="rgba(255,255,255,0.88)" fontSize="34" fontWeight="700" fontFamily="Arial, sans-serif" textAnchor="middle">{title}</text> : null}
      {elements.map((spec)=><Element key={spec.id} spec={spec} t={t}/>) }
    </svg>
  </AbsoluteFill>;
};
