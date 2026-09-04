export function edgeProviderBudgetMilliseconds(targetDurationSeconds) {
  const target = Number(targetDurationSeconds);
  if (!Number.isFinite(target) || target <= 0) return 120000;
  // One natural-rate provider call. This is a transport wall-clock budget,
  // not a retry or speech-speed adjustment.
  return Math.max(120000, Math.min(240000, Math.round(60000 + (target * 3000))));
}
