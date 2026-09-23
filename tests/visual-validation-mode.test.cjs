const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

function workflow(name) {
  return JSON.parse(fs.readFileSync(path.join(root, 'workflows', name), 'utf8'));
}

function nodeByName(wf, name) {
  const node = wf.nodes.find((item) => item.name === name);
  assert.ok(node, 'missing node: ' + name);
  return node;
}

function runValidate(body) {
  const wf = workflow('VIDEO-M3-Intake.json');
  const code = nodeByName(wf, 'Validate Intake').parameters.jsCode;
  return new Function('$json', code)({ body });
}

test('M3 defaults omitted visual validation mode to metadata', () => {
  const out = runValidate({topic:'How GPS works', language:'en', duration:30});
  assert.equal(out.json.valid, true);
  assert.equal(out.json.visual_validation_mode, 'metadata');
});

test('M3 accepts explicit Gemini visual validation mode', () => {
  const out = runValidate({
    topic:'How GPS works',
    language:'en',
    duration:30,
    visual_validation_mode:'gemini',
  });
  assert.equal(out.json.valid, true);
  assert.equal(out.json.visual_validation_mode, 'gemini');
});

test('M3 rejects unknown visual validation mode', () => {
  const out = runValidate({
    topic:'How GPS works',
    language:'en',
    duration:30,
    visual_validation_mode:'other',
  });
  assert.equal(out.json.valid, false);
  assert.match(out.json.response.details.join(' '), /visual_validation_mode/);
});

test('M3 persists visual validation mode through four-argument create_job', () => {
  const wf = workflow('VIDEO-M3-Intake.json');
  const create = nodeByName(wf, 'Create Job').parameters;
  assert.match(create.query, /\$4::text/);
  assert.match(create.options.queryReplacement, /visual_validation_mode/);
});

test('job schema persists metadata or gemini mode', () => {
  const sql = fs.readFileSync(path.join(root, 'db', '04-jobs.sql'), 'utf8');
  assert.match(sql, /visual_validation_mode text NOT NULL DEFAULT 'metadata'/);
  assert.match(sql, /visual_validation_mode IN \('metadata', 'gemini'\)/);
  assert.match(sql, /p_visual_validation_mode text/);
});

test('Studio exposes visual quality mode and submits it', () => {
  const html = fs.readFileSync(path.join(root, 'studio', 'index.html'), 'utf8');
  assert.match(html, /id="visualValidationMode"/);
  assert.match(html, /value="metadata"/);
  assert.match(html, /value="gemini"/);
  assert.match(html, /visual_validation_mode:\s*document\.getElementById\('visualValidationMode'\)\.value/);
});

test('latest job API exposes visual validation mode', () => {
  const wf = workflow('VIDEO-Self-Test-API.json');
  const load = nodeByName(wf, 'Load Latest Job');
  assert.match(load.parameters.query, /j\.visual_validation_mode/);
});
