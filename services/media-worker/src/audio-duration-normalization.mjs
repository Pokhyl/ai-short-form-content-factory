const FRAME_TOLERANCE_SECONDS = 1 / 30;
const MAX_NATURAL_TAIL_PAD_SECONDS = 0.4;

export function buildNaturalTailPadPlan(durationSeconds, targetDurationSeconds) {
  const duration = Number(durationSeconds);
  const target = Number(targetDurationSeconds);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('voiceover duration must be positive');
  if (!Number.isFinite(target) || target <= 0) throw new Error('target duration must be positive');
  const acceptedMin = (target * 0.90) - FRAME_TOLERANCE_SECONDS;
  if (duration >= acceptedMin - 1e-9) {
    return { apply: false, pad_seconds: 0, accepted_min_seconds: Number(acceptedMin.toFixed(6)), final_duration_seconds: duration };
  }
  // Normalize only a tiny sentence-final pause difference. This is not speech-rate
  // manipulation and cannot rescue materially short narration.
  const desiredFinal = acceptedMin + (FRAME_TOLERANCE_SECONDS / 2);
  const pad = desiredFinal - duration;
  if (pad <= 0 || pad > MAX_NATURAL_TAIL_PAD_SECONDS + 1e-9) {
    return { apply: false, pad_seconds: 0, accepted_min_seconds: Number(acceptedMin.toFixed(6)), final_duration_seconds: duration };
  }
  return {
    apply: true,
    pad_seconds: Number(pad.toFixed(6)),
    accepted_min_seconds: Number(acceptedMin.toFixed(6)),
    final_duration_seconds: Number(desiredFinal.toFixed(6)),
  };
}

export { FRAME_TOLERANCE_SECONDS, MAX_NATURAL_TAIL_PAD_SECONDS };
