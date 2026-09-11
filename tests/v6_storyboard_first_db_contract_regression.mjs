import assert from 'node:assert/strict';
import fs from 'node:fs';
const migration=fs.readFileSync('db/migrations/027_storyboard_first_story_package.sql','utf8');
const init=fs.readFileSync('db/init/001_init.sql','utf8');
for(const text of [migration,init]){
  for(const marker of ['inventory-first-story-v1','visual-facts-story-v1','visual-facts-first-v1','storyboard-first-v1','representation-first-v1','editorial_contract_version','storyboard-v1']) assert.ok(text.includes(marker),`missing ${marker}`);
  assert.match(text,/jsonb_array_length\([^)]*assets[^)]*\)\s*=\s*jsonb_array_length\([^)]*units[^)]*\)/s);
}
assert.ok(migration.includes('DROP CONSTRAINT IF EXISTS jobs_story_package_check'));
assert.ok(migration.includes('ADD CONSTRAINT jobs_story_package_check CHECK'));
console.log('V6_STORYBOARD_FIRST_DB_CONTRACT_PASS');
