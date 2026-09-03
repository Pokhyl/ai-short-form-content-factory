export function buildVisualDiscoveryOptions(
  body,
  { pixabayApiKey = "", pexelsApiKey = "" } = {},
) {
  return {
    canonicalSource: body?.canonical_source,
    beats: body?.beats,
    timedBeats: body?.timed_beats,
    pixabayApiKey,
    pexelsApiKey,
  };
}
