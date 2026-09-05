export function requiredUniqueVisualCount(beatCount) {
  const count = Number(beatCount);
  if (!Number.isInteger(count) || count <= 0) throw new Error("beat count must be positive");
  if (count <= 2) return count;
  return Math.min(count, Math.max(3, Math.ceil(count * 0.75)));
}

export function evaluateVisualSequence(beats) {
  if (!Array.isArray(beats) || beats.length === 0) throw new Error("visual sequence requires beats");
  let totalDuration = 0;
  const durationByCluster = new Map();
  const assetKeys = [];
  const clusterKeys = [];
  let adjacentClusterDuplicateCount = 0;

  for (let index = 0; index < beats.length; index += 1) {
    const beat = beats[index] ?? {};
    const assetKey = String(beat.asset_key ?? "").trim();
    const clusterKey = String(beat.visual_cluster_key ?? "").trim();
    const duration = Number(beat.duration_seconds);
    if (!assetKey) throw new Error(`beat ${index + 1} asset_key is missing`);
    if (!clusterKey) throw new Error(`beat ${index + 1} visual_cluster_key is missing`);
    if (!Number.isFinite(duration) || duration <= 0) throw new Error(`beat ${index + 1} duration is invalid`);
    totalDuration += duration;
    assetKeys.push(assetKey);
    clusterKeys.push(clusterKey);
    durationByCluster.set(clusterKey, (durationByCluster.get(clusterKey) ?? 0) + duration);
    if (index > 0 && clusterKey === clusterKeys[index - 1]) adjacentClusterDuplicateCount += 1;
  }

  if (!Number.isFinite(totalDuration) || totalDuration <= 0) throw new Error("visual sequence duration is invalid");
  const uniqueAssetCount = new Set(assetKeys).size;
  const uniqueVisualClusterCount = new Set(clusterKeys).size;
  const requiredUniqueVisualClusterCount = requiredUniqueVisualCount(beats.length);
  const maxVisualClusterDuration = Math.max(...durationByCluster.values());
  const maxVisualClusterDurationShare = maxVisualClusterDuration / totalDuration;
  if (!Number.isFinite(maxVisualClusterDurationShare)) throw new Error("visual sequence cluster duration share is invalid");
  const pass =
    uniqueVisualClusterCount >= requiredUniqueVisualClusterCount &&
    adjacentClusterDuplicateCount === 0 &&
    maxVisualClusterDurationShare <= 0.34;

  return {
    version: "visual-quality-v2",
    beat_count: beats.length,
    unique_asset_count: uniqueAssetCount,
    unique_visual_cluster_count: uniqueVisualClusterCount,
    required_unique_visual_cluster_count: requiredUniqueVisualClusterCount,
    unique_visual_cluster_ratio: Number((uniqueVisualClusterCount / beats.length).toFixed(4)),
    adjacent_visual_cluster_duplicate_count: adjacentClusterDuplicateCount,
    max_visual_cluster_duration_share: Number(maxVisualClusterDurationShare.toFixed(4)),
    pass,
  };
}

export function hammingDistance(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) throw new Error("hashes must have equal length");
  let distance = 0;
  for (let index = 0; index < a.length; index += 1) if (a[index] !== b[index]) distance += 1;
  return distance;
}

export function clusterAverageHashes(hashes, threshold = 18) {
  if (!Array.isArray(hashes) || hashes.length === 0) throw new Error("hash list is empty");
  if (!Number.isInteger(threshold) || threshold < 0) throw new Error("hash threshold must be a non-negative integer");
  const clusters = [];
  for (let index = 0; index < hashes.length; index += 1) {
    const hash = hashes[index];
    if (!Array.isArray(hash) || hash.length !== 256 || hash.some((bit) => bit !== 0 && bit !== 1)) {
      throw new Error(`hash ${index + 1} must contain exactly 256 binary values`);
    }
    let placed = false;
    for (const cluster of clusters) {
      if (hammingDistance(hash, hashes[cluster[0]]) <= threshold) {
        cluster.push(index);
        placed = true;
        break;
      }
    }
    if (!placed) clusters.push([index]);
  }
  return clusters;
}


export function requiredRenderedShotStateCount(shotCount, maxClusterOccurrences = 2) {
  const count = Number(shotCount);
  const maxOccurrences = Number(maxClusterOccurrences);
  if (!Number.isInteger(count) || count <= 0) throw new Error("shot count must be positive");
  if (!Number.isInteger(maxOccurrences) || maxOccurrences <= 0) throw new Error("max cluster occurrences must be positive");
  return Math.min(count, 2);
}

export function evaluateVisualShotSequence(shots, options = {}) {
  if (!Array.isArray(shots) || shots.length === 0) throw new Error("visual shot sequence requires shots");
  const maxClusterDurationShareLimit = Number(options.max_cluster_duration_share ?? 0.34);
  const maxClusterOccurrencesLimit = Number(options.max_cluster_occurrences ?? 2);
  const requireUniqueAssets = options.require_unique_assets === true;
  if (!Number.isFinite(maxClusterDurationShareLimit) || maxClusterDurationShareLimit <= 0 || maxClusterDurationShareLimit > 1) throw new Error("max cluster duration share is invalid");
  if (!Number.isInteger(maxClusterOccurrencesLimit) || maxClusterOccurrencesLimit <= 0) throw new Error("max cluster occurrences is invalid");

  let totalDuration = 0;
  let previousEnd = 0;
  let adjacentClusterDuplicateCount = 0;
  const assetKeys = [];
  const clusterKeys = [];
  const durationByCluster = new Map();
  const occurrenceByCluster = new Map();

  for (let index = 0; index < shots.length; index += 1) {
    const shot = shots[index] ?? {};
    const number = Number(shot.shot_number ?? index + 1);
    const start = Number(shot.start_seconds);
    const end = Number(shot.end_seconds);
    const duration = Number(shot.duration_seconds);
    const assetKey = String(shot.asset_key ?? "").trim();
    const clusterKey = String(shot.visual_cluster_key ?? "").trim();
    if (!Number.isInteger(number) || number !== index + 1) throw new Error(`shot ${index + 1} number is invalid`);
    if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(duration) || start < 0 || end <= start || duration <= 0) throw new Error(`shot ${number} timing is invalid`);
    if (Math.abs(start - previousEnd) > 0.02 || Math.abs((end - start) - duration) > 0.02) throw new Error(`shot ${number} timing is not contiguous`);
    if (!assetKey) throw new Error(`shot ${number} asset_key is missing`);
    if (!clusterKey) throw new Error(`shot ${number} visual_cluster_key is missing`);
    if (index > 0 && clusterKey === clusterKeys[index - 1]) adjacentClusterDuplicateCount += 1;
    assetKeys.push(assetKey);
    clusterKeys.push(clusterKey);
    totalDuration += duration;
    durationByCluster.set(clusterKey, (durationByCluster.get(clusterKey) ?? 0) + duration);
    occurrenceByCluster.set(clusterKey, (occurrenceByCluster.get(clusterKey) ?? 0) + 1);
    previousEnd = end;
  }

  if (!Number.isFinite(totalDuration) || totalDuration <= 0) throw new Error("visual shot sequence duration is invalid");
  const uniqueAssetCount = new Set(assetKeys).size;
  const uniqueVisualClusterCount = new Set(clusterKeys).size;
  const requiredUniqueVisualClusterCount = requiredRenderedShotStateCount(shots.length, maxClusterOccurrencesLimit);
  const maxVisualClusterDurationShare = Math.max(...durationByCluster.values()) / totalDuration;
  const maxVisualClusterOccurrenceCount = Math.max(...occurrenceByCluster.values());
  const maxShotDurationSeconds = Math.max(...shots.map((shot) => Number(shot.duration_seconds)));
  if (!Number.isFinite(maxVisualClusterDurationShare) || !Number.isFinite(maxShotDurationSeconds)) throw new Error("visual shot sequence quality metric is invalid");
  const pass =
    (!requireUniqueAssets || uniqueAssetCount === shots.length) &&
    uniqueVisualClusterCount >= requiredUniqueVisualClusterCount &&
    adjacentClusterDuplicateCount === 0;

  return {
    version: "visual-segments-v3",
    shot_count: shots.length,
    unique_asset_count: uniqueAssetCount,
    asset_reuse_count: shots.length - uniqueAssetCount,
    unique_visual_cluster_count: uniqueVisualClusterCount,
    required_unique_visual_cluster_count: requiredUniqueVisualClusterCount,
    adjacent_visual_cluster_duplicate_count: adjacentClusterDuplicateCount,
    max_visual_cluster_occurrence_count: maxVisualClusterOccurrenceCount,
    max_allowed_visual_cluster_occurrence_count: maxClusterOccurrencesLimit,
    max_visual_cluster_duration_share: Number(maxVisualClusterDurationShare.toFixed(4)),
    max_allowed_visual_cluster_duration_share: maxClusterDurationShareLimit,
    max_shot_duration_seconds: Number(maxShotDurationSeconds.toFixed(4)),
    all_assets_unique: uniqueAssetCount === shots.length,
    pass,
  };
}
