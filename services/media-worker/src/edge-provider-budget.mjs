export function edgeProviderBudgetMilliseconds(targetDurationSeconds) {
  const target = Number(targetDurationSeconds);
  if (!Number.isFinite(target) || target <= 0) return 30000;
  // Bound a stalled Read Aloud websocket tightly. A fresh transport attempt is
  // more useful than leaving the whole job apparently frozen for four minutes.
  return Math.max(25000, Math.min(40000, Math.round(20000 + (target * 350))));
}
