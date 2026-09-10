import React from "react";
import {Composition, registerRoot} from "remotion";
import {V6VerticalShort, V6VerticalShortProps} from "./VerticalShort";

const defaults: V6VerticalShortProps = {
  duration_seconds: 15,
  audio_src: "",
  captions: [],
  visual_track: [],
};

const Root: React.FC = () => (
  <Composition
    id="V6VerticalShort"
    component={V6VerticalShort}
    durationInFrames={450}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaults}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Math.ceil(Number(props.duration_seconds) * 30)),
      fps: 30,
      width: 1080,
      height: 1920,
    })}
  />
);

registerRoot(Root);
