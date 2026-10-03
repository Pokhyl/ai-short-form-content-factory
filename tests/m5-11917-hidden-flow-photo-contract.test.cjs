const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');

const workflow = JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const nodes = workflow.nodes.filter(n =>
  typeof n?.parameters?.jsCode === 'string' &&
  n.parameters.jsCode.includes('function canonicalizeTransientPhotoActionIntent')
);

function extract(node) {
  const code = node.parameters.jsCode;
  const start = code.indexOf('function canonicalizeTransientPhotoActionIntent');
  const end = code.indexOf('// MUST_SHOW_SECONDARY_GUARD_END', start);
  assert.ok(start >= 0 && end > start, node.name);
  return new Function(
    code.slice(start, end) + '\nreturn canonicalizeTransientPhotoActionIntent;'
  )();
}

test('11917 hidden flow through closed valve/pipe becomes static photo contract', () => {
  assert.ok(nodes.length >= 3);
  for (const node of nodes) {
    const fn = extract(node);
    assert.equal(
      fn(
        ['check valve','metal pipe'],
        'An open check valve allowing medium flow through a metal pipe section.'
      ),
      'A clear photo of check valve with metal pipe.',
      node.name
    );
  }
});

test('visible external flow is not canonicalized away', () => {
  for (const node of nodes) {
    const fn = extract(node);
    const intent = 'Water flowing from a faucet into a glass.';
    assert.equal(fn(['faucet','glass'], intent), intent, node.name);
  }
});

test('transparent conduit keeps explicitly visible internal flow', () => {
  for (const node of nodes) {
    const fn = extract(node);
    const intent = 'Water flowing through a transparent pipe.';
    assert.equal(fn(['transparent pipe'], intent), intent, node.name);
  }
});
