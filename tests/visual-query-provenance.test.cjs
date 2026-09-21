const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));
const sql=fs.readFileSync('db/09-visuals.sql','utf8');

test('provider HTTP requests use effective provider_query, not provenance query',()=>{
  const pix=byName['Pixabay Search'].parameters.queryParameters.parameters.find(p=>p.name==='q').value;
  const pex=byName['Pexels Search'].parameters.queryParameters.parameters.find(p=>p.name==='query').value;
  assert.match(pix,/\$json\.provider_query/);
  assert.doesNotMatch(pix,/\$json\.query\s*\}\}/);
  assert.match(pex,/\$json\.provider_query/);
  assert.doesNotMatch(pex,/\$json\.query\s*\}\}/);
  for(const name of ['Wikimedia Search','Wikimedia Retry 1','Wikimedia Retry 2']){
    const value=byName[name].parameters.queryParameters.parameters.find(p=>p.name==='gsrsearch').value;
    assert.match(value,/\$json\.provider_query/);
  }
});

test('normalizers preserve storyboard query and expose actual provider query separately',()=>{
  for(const name of ['Normalize Pixabay','Normalize Pexels','Normalize Wikimedia']){
    const code=byName[name].parameters.jsCode;
    assert.match(code,/query_text:ctx\.query/);
    assert.match(code,/provider_query_text:String\(ctx\.provider_query \|\| ctx\.query/);
  }
});

test('persist nodes use v3 and pass both query provenance fields',()=>{
  for(const name of ['Persist Pixabay Searches','Persist Pexels Searches','Persist Wikimedia Searches']){
    const p=byName[name].parameters;
    assert.match(p.query,/record_live_visual_search_v3/);
    assert.match(p.options.queryReplacement,/\$json\.query_text/);
    assert.match(p.options.queryReplacement,/\$json\.provider_query_text/);
  }
});

test('database stores original and effective query separately and caches by effective query',()=>{
  assert.match(sql,/provider_query_text text NOT NULL/);
  assert.match(sql,/ADD COLUMN IF NOT EXISTS provider_query_text text/);
  assert.match(sql,/SET provider_query_text=query_text/);
  assert.match(sql,/CREATE OR REPLACE FUNCTION factory\.record_live_visual_search_v3/);
  assert.match(sql,/p_query_text text,\s*p_provider_query_text text,/s);
  assert.match(sql,/factory\.put_visual_cache\(\s*p_provider,\s*p_endpoint_kind,\s*v_provider_query_text,/s);
  assert.match(sql,/factory\.record_visual_search\(\s*p_visual_run_id,\s*p_shot_id,\s*p_provider,\s*p_query_index,\s*p_query_text,/s);
  assert.match(sql,/SET provider_query_text=v_provider_query_text/);
});
