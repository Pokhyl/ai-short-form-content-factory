export function buildVisualBeatFilters({ index, duration, isImage, isFactualGraphic }) {
  if (!Number.isInteger(index) || index < 0) throw new Error("visual frame index must be a non-negative integer");
  const seconds = Number(duration);
  if (!Number.isFinite(seconds) || seconds <= 0) throw new Error("visual frame duration must be positive");
  const d = seconds.toFixed(6);
  const imageHold = isImage ? `tpad=stop_mode=clone:stop_duration=${d},` : "";
  const input = `[${index}:v]fps=30,${imageHold}`;

  // Still images are never destructively center-cropped. Preserve the complete
  // source in a foreground layer and use a blurred fill behind it. This keeps
  // people, diagrams, labels and edge content visible on a 9:16 canvas.
  if (isImage) {
    const phase = (index % 7) * 0.41;
    const overlayX = isFactualGraphic ? "(W-w)/2" : `(W-w)/2+8*sin(t*0.55+${phase.toFixed(2)})`;
    const overlayY = isFactualGraphic ? "(H-h)/2" : `(H-h)/2+10*cos(t*0.43+${phase.toFixed(2)})`;
    return [
      `${input}split=2[bg${index}][fg${index}]`,
      `[bg${index}]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,boxblur=22:1,setsar=1[bgfill${index}]`,
      `[fg${index}]scale=1020:1760:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[fgfit${index}]`,
      `[bgfill${index}][fgfit${index}]overlay=x='${overlayX}':y='${overlayY}':eval=frame:format=auto,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`,
    ];
  }

  // Motion footage may fill the frame; the still-image preservation rule above
  // is the crop-aware contract required for the default photo-first product path.
  return [`${input}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,trim=duration=${d},setpts=PTS-STARTPTS,format=yuv420p[v${index}]`];
}
