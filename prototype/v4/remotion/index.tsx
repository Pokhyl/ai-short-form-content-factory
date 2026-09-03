import React from "react";
import {Composition, registerRoot} from "remotion";
import {MotionDiagram, MotionDiagramProps} from "./MotionDiagram";

const Root: React.FC = () => <Composition
  id="MotionDiagram"
  component={MotionDiagram}
  width={720}
  height={1280}
  fps={30}
  durationInFrames={180}
  defaultProps={{durationSeconds:6, background:"#0B1020", elements:[]} as MotionDiagramProps}
  calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.ceil((props.durationSeconds ?? 6) * 30))})}
/>;
registerRoot(Root);
