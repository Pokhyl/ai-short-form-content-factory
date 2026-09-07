import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '..');
const dir = path.join(root, 'n8n', 'workflows');
let checked = 0;
for (const file of fs.readdirSync(dir).filter((name) => name.endsWith('.json')).sort()) {
  const raw = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'));
  const workflows = Array.isArray(raw) ? raw : [raw];
  for (const workflow of workflows) {
    for (const node of workflow.nodes ?? []) {
      if (node.type !== 'n8n-nodes-base.postgres') continue;
      checked += 1;
      const postgres = node.credentials?.postgres;
      assert.ok(postgres?.id, `${file}: PostgreSQL node ${node.name} is missing credentials.postgres.id`);
      assert.ok(postgres?.name, `${file}: PostgreSQL node ${node.name} is missing credentials.postgres.name`);
    }
  }
}
assert.ok(checked > 0, 'No PostgreSQL nodes were checked');
console.log(`POSTGRES_CREDENTIALS_CONTRACT_PASS: ${checked} nodes`);
