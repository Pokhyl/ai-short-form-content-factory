export function buildVisualBeatFilters({ index, duration, isImage, isFactualGraphic }) {
  if (!Number.isInteger(index) || index < 0) throw new Error("visual frame index must be a non-negative integer");
  const seconds = Number(duration);
  if (!Number.isFinite(seconds) || seconds <= 0) throw new Error("visual frame duration must be positive");
  const d = seconds.toFixed(6);
  const imageHold = isImage ? `tpad=stop_mode=clone:stop_duration=${d},` : "";
  const input = `[${index}:v]fps=30,${imageHold}`;

  // Ordinary photos fill a portrait canvas. Keep a small overscan and move the
  // crop window slowly inside it so landscape sources become native 9:16 shots
  // with restrained motion instead of horizontal cards over blurred fill.
  if (isImage && !isFactualGraphic) {
    const phase = (index % 7) * 0.41;
    const x = `(in_w-out_w)/2+(in_w-out_w)*0.12*sin(n*0.018+${phase.toFixed(2)})`;
    const y = `(in_h-out_h)/2+(in_h-out_h)*0.12*cos(n*0.015+${phase.toFixed(2)})`;
    return [`${input}scale=1200:2134:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920:x='${x}':y='${y}',setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
  }

  // Diagrams/graphics may contain labels or edge details that must remain visible.
  // Preserve the complete graphic and use blurred fill only for this factual-graphic lane.
  if (isImage && isFactualGraphic) {
    return [
      `${input}split=2[bg${index}][fg${index}]`,
      `[bg${index}]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,boxblur=20:1,setsar=1[bgfill${index}]`,
      `[fg${index}]scale=1020:1840:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[fgfit${index}]`,
      `[bgfill${index}][fgfit${index}]overlay=(W-w)/2:(H-h)/2:format=auto,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`,
    ];
  }

  return [`${input}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
}
