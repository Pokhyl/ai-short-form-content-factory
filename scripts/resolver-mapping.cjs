const fs = require('node:fs');
const {PexelsAPI} = require('../engine-overlay/Pexels');
const {sourceLexicon} = require('../engine-overlay/VisualSubject');
const fixture = require('../tests/fixtures/scenes.cjs');
const {api: fixtureAPI} = require('../tests/fixtures/api.cjs');
const live = process.argv.includes('--live');
const languages = process.argv.includes('--uk-only') ? ['uk'] : fixture.langs;
const recordIndex = process.argv.indexOf('--record');
const recorded = {capturedAt: new Date().toISOString(), requests: {}};

function compact(data) {
  const copy = structuredClone(data);
  if (copy.parse?.wikitext) {
    // Store only the source-linked lexical forms used by the resolver. Wikipedia
    // article prose, references and unrelated templates are not needed by tests.
    copy.parse.wikitext['*'] = sourceLexicon(copy.parse.wikitext['*'], copy.parse.title)
      .flatMap(e => e.aliases.map(a => `[[${e.title}|${a}]]`)).join('\n');
  }
  for (const e of Object.values(copy.entities || {})) {
    if (e.claims) e.claims = Object.fromEntries(Object.entries(e.claims).filter(([p]) => ['P18','P31','P279'].includes(p)));
  }
  return copy;
}
(async()=>{
  const results=[];
  const network = new PexelsAPI('');
  for (const lang of languages) {
    const resolver = live ? new PexelsAPI('', {fetchJson:async url=>{
      const data = await network._fetchJson(url);
      recorded.requests[url] = compact(data);
      return data;
    }}) : fixtureAPI();
    const media = await resolver.preflightScenes(fixture.scenes(lang));
    results.push(...media.map(m=>({language:lang, narration:m.narration, entity:m.groundedEntity, qid:m.groundedEntityId, media:m.title, source:m.source, subject:m.subject, reuseReason:m.reuseReason || null, url:m.url || null, components:m.components || null, sourceRevision:m.sourceRevision})));
  }
  if (recordIndex >= 0) fs.writeFileSync(process.argv[recordIndex+1], JSON.stringify(recorded,null,2)+'\n');
  process.stdout.write(JSON.stringify({mode:live?'live_wikimedia':'deterministic_fixtures',results},null,2)+'\n');
})().catch(error=>{console.error(error);process.exitCode=1;});
