import fs from 'node:fs';
import assert from 'node:assert/strict';

const workflows = fs.readdirSync('n8n/workflows').filter(p => p.endsWith('.json'))
  .flatMap(p => {
    const w = JSON.parse(fs.readFileSync(`n8n/workflows/${p}`, 'utf8'));
    return Array.isArray(w) ? w : [w];
  });
const ids = new Set(workflows.map(w => w.id));
assert.equal(ids.size, workflows.length, 'duplicate workflow IDs');
const webhooks = new Set();
for (const w of workflows) {
  const names = new Set(w.nodes.map(n => n.name));
  assert.equal(names.size, w.nodes.length, `${w.name}: duplicate node names`);
  for (const [name, outputs] of Object.entries(w.connections)) {
    assert(names.has(name), `${w.name}: missing connection source ${name}`);
    for (const channel of Object.values(outputs)) for (const edges of channel) {
      for (const edge of edges) assert(names.has(edge.node), `${w.name}: missing target ${edge.node}`);
    }
  }
  for (const n of w.nodes) {
    if (n.type === 'n8n-nodes-base.executeWorkflow') {
      const target = n.parameters.workflowId;
      assert(ids.has(typeof target === 'string' ? target : target.value), `${n.name}: absent child workflow`);
    }
    if (n.type === 'n8n-nodes-base.webhook') {
      const key = `${n.parameters.httpMethod || 'GET'} ${n.parameters.path}`;
      assert(!webhooks.has(key), `duplicate webhook ${key}`);
      webhooks.add(key);
    }
    if (n.type === 'n8n-nodes-base.code') {
      // Compile as an async n8n Code node; this does not execute network/SQL actions.
      const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
      assert.doesNotThrow(() => new AsyncFunction(n.parameters.jsCode), `${w.name}/${n.name}`);
    }
  }
}
assert(webhooks.has('GET review/job'), 'human review API is absent from source');
assert(webhooks.has('POST review/decision'), 'human decision API is absent from source');
console.log(`WORKFLOW_GRAPH_CONTRACT_PASS: ${workflows.length} workflows`);
