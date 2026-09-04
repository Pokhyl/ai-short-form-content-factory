import React from "react";
import {Composition, registerRoot} from "remotion";
import {MotionDiagram, MotionDiagramProps} from "./MotionDiagram";
import {VerticalShort, VerticalShortProps} from "./VerticalShort";

const defaultVertical: VerticalShortProps = {
  duration_seconds: 6,
  profile:{width:1080,height:1920,fps:30,caption_safe_bottom_px:320,caption_max_width_ratio:0.70},
  audio:{src:""},
  captions:{items:[]},
  visual_track:[],
};

const Root: React.FC = () => <>
  <Composition
    id="MotionDiagram"
    component={MotionDiagram}
    width={720}
    height={1280}
    fps={30}
    durationInFrames={180}
    defaultProps={{durationSeconds:6, background:"#0B1020", elements:[]} as MotionDiagramProps}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.ceil((props.durationSeconds ?? 6) * 30))})}
  />
  <Composition
    id="VerticalShort"
    component={VerticalShort}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={180}
    defaultProps={defaultVertical}
    calculateMetadata={({props}) => ({
      width: props.profile?.width ?? 1080,
      height: props.profile?.height ?? 1920,
      fps: props.profile?.fps ?? 30,
      durationInFrames: Math.max(1, Math.ceil((props.duration_seconds ?? 6) * (props.profile?.fps ?? 30))),
    })}
  />
</>;
registerRoot(Root);
