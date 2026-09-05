import assert from 'node:assert/strict';
import { discoverVisualCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const requests = [];
let activeProviderSearches = 0;
let maxActiveProviderSearches = 0;

const makeResponse = payload => ({ ok: true, status: 200, json: async () => payload });
const imagePage = (id, query) => ({
  title: `File:${id}.jpg`,
  imageinfo: [{
    mime: 'image/jpeg', width: 1200, height: 800,
    url: `https://upload.wikimedia.org/${id}.jpg`,
    thumburl: `https://upload.wikimedia.org/${id}-thumb.jpg`,
    descriptionurl: `https://commons.wikimedia.org/wiki/File:${id}.jpg`,
    extmetadata: { ImageDescription: { value: query }, LicenseShortName: { value: 'CC BY' } },
  }],
});

async function fakeFetch(input, options = {}) {
  const url = new URL(String(input));
  requests.push({ url: url.toString(), host: url.host, path: url.pathname, q: url.searchParams.get('q') ?? url.searchParams.get('gsrsearch') ?? '' });

  if (url.hostname.endsWith('.wikipedia.org')) {
    if (url.searchParams.get('prop') === 'langlinks') {
      return makeResponse({ query: { pages: [{ langlinks: [{ title: 'Hydroelectric power' }] }] } });
    }
    return makeResponse({ query: { pages: [] } });
  }

  activeProviderSearches += 1;
  maxActiveProviderSearches = Math.max(maxActiveProviderSearches, activeProviderSearches);
  await new Promise(resolve => setTimeout(resolve, 15));
  activeProviderSearches -= 1;

  if (url.hostname === 'commons.wikimedia.org') {
    const query = url.searchParams.get('gsrsearch') ?? '';
    return makeResponse({ query: { pages: [imagePage(`commons-${encodeURIComponent(query).slice(0, 24)}`, query)] } });
  }
  if (url.hostname === 'pixabay.com') {
    const query = url.searchParams.get('q') ?? '';
    return makeResponse({ hits: [{
      id: `pix-${query.length}`,
      largeImageURL: `https://cdn.pixabay.com/${encodeURIComponent(query)}.jpg`,
      webformatURL: `https://cdn.pixabay.com/${encodeURIComponent(query)}-preview.jpg`,
      imageWidth: 1600,
      imageHeight: 1000,
      tags: query,
      pageURL: 'https://pixabay.com/photos/test',
      user: 'fixture',
    }] });
  }
  if (url.hostname === 'api.pexels.com') {
    assert.equal(url.pathname, '/v1/search', 'Pexels must use the photo search endpoint');
    const query = url.searchParams.get('query') ?? '';
    return makeResponse({ photos: [{
      id: `pex-${query.length}`,
      width: 1600,
      height: 1000,
      url: 'https://www.pexels.com/photo/test-1/',
      photographer: 'fixture',
      alt: query,
      src: {
        original: 'https://images.pexels.com/photos/1/original.jpeg',
        large2x: 'https://images.pexels.com/photos/1/large2x.jpeg',
        medium: 'https://images.pexels.com/photos/1/medium.jpeg',
      },
    }] });
  }
  throw new Error(`unexpected URL ${url}`);
}

const timedBeats = [
  { scene_number: 1, narration: 'Water rushes through the spillway.', narration_support_evidence_ids: ['S1'], beat_start_seconds: 0, beat_end_seconds: 3, duration_seconds: 3 },
  { scene_number: 2, narration: 'The turbine blades rotate.', narration_support_evidence_ids: ['S1'], beat_start_seconds: 3, beat_end_seconds: 6, duration_seconds: 3 },
  { scene_number: 3, narration: 'A generator converts rotation into electricity.', narration_support_evidence_ids: ['S2'], beat_start_seconds: 6, beat_end_seconds: 9, duration_seconds: 3 },
  { scene_number: 4, narration: 'Electricity reaches homes through the grid.', narration_support_evidence_ids: ['S2'], beat_start_seconds: 9, beat_end_seconds: 12, duration_seconds: 3 },
];
const visualQueriesEn = [
  'hydroelectric dam spillway rushing water',
  'hydroelectric turbine blades close up',
  'hydroelectric generator shaft and turbine inside power plant with visible mechanical coupling components',
  'residential houses connected to electrical power grid at night',
];

const result = await discoverVisualCandidates({
  canonicalSource: { language: 'en', title: 'Hydroelectric power' },
  timedBeats,
  visualQueriesEn,
  pixabayApiKey: 'pix-key',
  pexelsApiKey: 'pex-key',
  fetchImpl: fakeFetch,
});

assert.equal(result.visual_segments.length, 4);
assert.equal(result.provider_counts.pixabay_base, 0, 'timed mode must not mix topic-level Pixabay stock');
assert.equal(result.provider_counts.pexels_base, 0, 'timed mode must not mix topic-level Pexels stock');
assert.equal(result.provider_counts.commons_base, 0, 'timed mode must not mix topic-level Commons stock');
assert.equal(result.provider_counts.segment_query_count, 4);
assert.ok(maxActiveProviderSearches >= 6, `provider/segment discovery should be concurrent; max active was ${maxActiveProviderSearches}`);

const providerRequests = requests.filter(row => ['commons.wikimedia.org', 'pixabay.com', 'api.pexels.com'].includes(row.host));
assert.ok(providerRequests.length >= 12);
for (const request of providerRequests) {
  assert.ok(request.q.length <= 90, `provider query exceeds bounded length: ${request.q.length}`);
  assert.notEqual(request.q, 'Hydroelectric power', 'timed discovery must not issue generic topic-level stock searches');
  assert.ok(!request.q.startsWith('Hydroelectric power '), `canonical topic must not be prefixed to exact beat query: ${request.q}`);
}
assert.ok(providerRequests.some(row => row.q === visualQueriesEn[0]), 'first beat query must be sent verbatim when already within provider limit');

for (const segment of result.visual_segments) {
  assert.ok(segment.candidates.length >= 3, `segment ${segment.segment_number} should contain exact-query provider candidates`);
  const pexels = segment.candidates.find(candidate => candidate.provider === 'pexels');
  assert.ok(pexels, `segment ${segment.segment_number} missing Pexels photo candidate`);
  assert.equal(pexels.media_kind, 'photo');
  assert.equal(pexels.metadata.media_type, 'image');
  assert.equal(segment.provider_query, providerRequests.find(row => row.q === segment.provider_query)?.q ?? segment.provider_query);
}

console.log('VISUAL_DISCOVERY_EXACT_SEGMENT_QUERY_REGRESSION_PASS');
