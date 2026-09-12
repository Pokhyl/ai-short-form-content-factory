"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PortraitVideo = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const remotion_1 = require("remotion");
const BarlowCondensed_1 = require("@remotion/google-fonts/BarlowCondensed");
const utils_1 = require("../utils");
const { fontFamily } = (0, BarlowCondensed_1.loadFont)();

const PortraitVideo = ({ scenes, music, config }) => {
  const frame = (0, remotion_1.useCurrentFrame)();
  const { fps } = (0, remotion_1.useVideoConfig)();
  const captionBackgroundColor = config.captionBackgroundColor ?? "blue";
  const activeStyle = {
    backgroundColor: captionBackgroundColor,
    padding: "10px",
    marginLeft: "-10px",
    marginRight: "-10px",
    borderRadius: "10px",
  };
  const captionPosition = config.captionPosition ?? "center";
  let captionStyle = {};
  if (captionPosition === "top") captionStyle = { top: 100 };
  if (captionPosition === "center") captionStyle = { top: "50%", transform: "translateY(-50%)" };
  if (captionPosition === "bottom") captionStyle = { bottom: 100 };

  const [musicVolume, musicMuted] = (0, utils_1.calculateVolume)(config.musicVolume);
  const narrationUrl = scenes[0]?.audio?.url;

  return (0, jsx_runtime_1.jsxs)(remotion_1.AbsoluteFill, {
    style: { backgroundColor: "black" },
    children: [
      (0, jsx_runtime_1.jsx)(remotion_1.Audio, {
        loop: true,
        src: music.url,
        startFrom: music.start * fps,
        endAt: music.end * fps,
        volume: () => musicVolume,
        muted: musicMuted,
      }),
      narrationUrl ? (0, jsx_runtime_1.jsx)(remotion_1.Audio, { src: narrationUrl }) : null,
      scenes.map((scene, i) => {
        const { captions, audio, video, mediaType } = scene;
        const pages = (0, utils_1.createCaptionPages)({
          captions,
          lineMaxLength: 20,
          lineCount: 1,
          maxDistanceMs: 1000,
        });
        const startFrame = Math.round(
          scenes.slice(0, i).reduce((acc, curr) => acc + curr.audio.duration, 0) * fps,
        );
        let durationInFrames = Math.max(1, Math.round(audio.duration * fps));
        if (config.paddingBack && i === scenes.length - 1) {
          durationInFrames += Math.round((config.paddingBack / 1000) * fps);
        }
        const localFrame = Math.max(0, frame - startFrame);
        const progress = (0, remotion_1.interpolate)(
          localFrame,
          [0, Math.max(1, durationInFrames - 1)],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );
        const foregroundScale = 1 + progress * 0.025;
        const videoScale = 1.05 + progress * 0.08;
        const videoDrift = (i % 2 === 0 ? -1 : 1) * (2 - progress * 4);

        const mediaLayer = mediaType === "image"
          ? (0, jsx_runtime_1.jsxs)(remotion_1.AbsoluteFill, {
              style: { backgroundColor: "black", overflow: "hidden" },
              children: [
                (0, jsx_runtime_1.jsx)(remotion_1.Img, {
                  src: video,
                  style: {
                    position: "absolute",
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    filter: "blur(34px) brightness(0.52)",
                    transform: "scale(1.16)",
                  },
                }),
                (0, jsx_runtime_1.jsx)(remotion_1.Img, {
                  src: video,
                  style: {
                    position: "absolute",
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    transform: `scale(${foregroundScale})`,
                  },
                }),
              ],
            })
          : (0, jsx_runtime_1.jsx)(remotion_1.OffthreadVideo, {
              src: video,
              muted: true,
              loop: true,
              style: {
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${videoScale}) translateX(${videoDrift}%)`,
              },
            });

        return (0, jsx_runtime_1.jsxs)(remotion_1.Sequence, {
          from: startFrame,
          durationInFrames,
          children: [
            mediaLayer,
            pages.map((page, j) =>
              (0, jsx_runtime_1.jsx)(remotion_1.Sequence, {
                from: Math.round((page.startMs / 1000) * fps),
                durationInFrames: Math.max(
                  1,
                  Math.round(((page.endMs - page.startMs) / 1000) * fps),
                ),
                children: (0, jsx_runtime_1.jsx)("div", {
                  style: { position: "absolute", left: 0, width: "100%", ...captionStyle },
                  children: page.lines.map((line, k) =>
                    (0, jsx_runtime_1.jsx)("p", {
                      style: {
                        fontSize: "6em",
                        fontFamily,
                        fontWeight: "black",
                        color: "white",
                        WebkitTextStroke: "2px black",
                        WebkitTextFillColor: "white",
                        textShadow: "0px 0px 10px black",
                        textAlign: "center",
                        width: "100%",
                        textTransform: "uppercase",
                      },
                      children: line.texts.map((text, l) => {
                        const active =
                          frame >= startFrame + (text.startMs / 1000) * fps &&
                          frame <= startFrame + (text.endMs / 1000) * fps;
                        return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, {
                          children: [
                            (0, jsx_runtime_1.jsx)("span", {
                              style: { fontWeight: "bold", ...(active ? activeStyle : {}) },
                              children: text.text,
                            }, `scene-${i}-page-${j}-line-${k}-text-${l}`),
                            l < line.texts.length - 1 ? " " : "",
                          ],
                        });
                      }),
                    }, `scene-${i}-page-${j}-line-${k}`),
                  ),
                }),
              }, `scene-${i}-page-${j}`),
            ),
          ],
        }, `scene-${i}`);
      }),
    ],
  });
};

exports.PortraitVideo = PortraitVideo;
