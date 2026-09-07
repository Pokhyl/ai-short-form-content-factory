const FRAME_TOLERANCE_SECONDS = 1 / 30;
const MAX_NATURAL_TAIL_PAD_SECONDS = 0.4;
const PROVIDER_POSTROLL_SECONDS = FRAME_TOLERANCE_SECONDS;

export function buildProviderTailTrimPlan(durationSeconds, lastWordEndSeconds) {
  const duration = Number(durationSeconds);
  const lastWordEnd = Number(lastWordEndSeconds);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('voiceover duration must be positive');
  if (!Number.isFinite(lastWordEnd) || lastWordEnd <= 0) throw new Error('provider last-word end must be positive');
  if (lastWordEnd > duration + 0.002) throw new Error('provider last-word end exceeds measured audio duration');
  const finalDuration = Math.min(duration, lastWordEnd + PROVIDER_POSTROLL_SECONDS);
  const trim = duration - finalDuration;
  if (trim <= 0.002) {
    return { apply: false, trim_seconds: 0, final_duration_seconds: duration, last_word_end_seconds: lastWordEnd };
  }
  return {
    apply: true,
    trim_seconds: Number(trim.toFixed(6)),
    final_duration_seconds: Number(finalDuration.toFixed(6)),
    last_word_end_seconds: Number(lastWordEnd.toFixed(6)),
  };
}

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

export { FRAME_TOLERANCE_SECONDS, MAX_NATURAL_TAIL_PAD_SECONDS, PROVIDER_POSTROLL_SECONDS };
