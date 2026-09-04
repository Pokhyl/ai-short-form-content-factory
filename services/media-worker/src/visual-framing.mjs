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
      const x = index % 2 === 0
        ? `(iw-ow)*${progress}`
        : `(iw-ow)*(1-${progress})`;
      return [`${input}scale=1200:2134:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920:x='${x}':y='(ih-oh)/2',setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
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
