export function buildVisualBeatFilters({ index, duration, isImage, isFactualGraphic }) {
  if (!Number.isInteger(index) || index < 0) throw new Error("visual frame index must be a non-negative integer");
  const seconds = Number(duration);
  if (!Number.isFinite(seconds) || seconds <= 0) throw new Error("visual frame duration must be positive");
  const d = seconds.toFixed(6);
  const imageHold = isImage ? `tpad=stop_mode=clone:stop_duration=${d},` : "";
  const input = `[${index}:v]fps=30,${imageHold}`;
  if (!isFactualGraphic) {
    if (isImage) {
      const progress = `min(max(t/${d},0),1)`;
      const states = [
        { x: `(iw-ow)*${progress}`, y: `(ih-oh)*0.15` },
        { x: `(iw-ow)*(1-${progress})`, y: `(ih-oh)*0.85` },
        { x: `(iw-ow)*0.15`, y: `(ih-oh)*${progress}` },
        { x: `(iw-ow)*0.85`, y: `(ih-oh)*(1-${progress})` },
        { x: `(iw-ow)*0.7*${progress}`, y: `(ih-oh)*0.7*${progress}` },
        { x: `(iw-ow)*(0.3+0.7*${progress})`, y: `(ih-oh)*(0.3+0.7*(1-${progress}))` },
      ];
      const state = states[index % states.length];
      return [`${input}scale=1320:2350:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920:x='${state.x}':y='${state.y}',setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
    }
    return [`${input}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
  }
  return [
    `${input}split=2[bg${index}][fg${index}]`,
    `[bg${index}]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,boxblur=20:1,setsar=1[bgfill${index}]`,
    `[fg${index}]scale=1020:1840:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[fgfit${index}]`,
    `[bgfill${index}][fgfit${index}]overlay=(W-w)/2:(H-h)/2:format=auto,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`,
  ];
}
