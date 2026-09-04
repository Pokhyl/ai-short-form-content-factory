export function buildVisualDiscoveryOptions(
  body,
  { pixabayApiKey = "", pexelsApiKey = "" } = {},
) {
  return {
    canonicalSource: body?.canonical_source,
    beats: body?.beats,
    timedBeats: body?.timed_beats,
    visualQueriesEn: body?.visual_queries_en,
    pixabayApiKey,
    pexelsApiKey,
  };
}
