const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');

const workflow = JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName = Object.fromEntries(workflow.nodes.map(n => [n.name,n]));

test('timing probe release preserves provider error for failure node', () => {
  const release = byName['Release Timing Probe Usage'];
  assert.match(release.parameters.query, /\$2::text AS error_message/);
  assert.match(release.parameters.options.queryReplacement, /\$json\.probe_usage_key/);
  assert.match(release.parameters.options.queryReplacement, /\$json\.error_message/);

  const fail = byName['Prepare Timing Probe Failure'];
  assert.doesNotMatch(fail.parameters.jsCode, /Normalize TTS Timing Probe/);
  const out = new Function('$json', fail.parameters.jsCode)({
    error_message: 'The credential "Google account" needs to be reconnected.',
  });
  assert.equal(
    out.json.message,
    'M5 timing TTS probe failed: The credential "Google account" needs to be reconnected.'
  );
});
