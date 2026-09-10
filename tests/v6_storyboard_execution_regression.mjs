import assert from 'node:assert/strict';
import fs from 'node:fs';

const readWorkflow=(path)=>{const raw=JSON.parse(fs.readFileSync(path,'utf8'));return Array.isArray(raw)?raw[0]:raw;};
const wf04=readWorkflow('n8n/workflows/WF04-visual-sourcing.json');
const wf05=readWorkflow('n8n/workflows/WF05-video-render.json');
const by04=Object.fromEntries(wf04.nodes.map(n=>[n.name,n]));
const by05=Object.fromEntries(wf05.nodes.map(n=>[n.name,n]));

assert.ok(String(by04['Require Eligible Visual Job'].parameters.jsCode).includes('storyboard-first-v1'),'WF04 must accept storyboard-first-v1');
assert.ok(by04['Constructed Diagram?'],'WF04 must branch constructed diagrams');
assert.ok(by04['Construct Diagram Visual'],'WF04 must construct diagrams locally');
assert.equal(by04['Construct Diagram Visual'].parameters.url,'http://media-worker:3001/visual/construct-diagram');
assert.match(String(by04['Construct Diagram Visual'].parameters.jsonBody),/diagram_spec/);
assert.match(String(by04['Construct Diagram Visual'].parameters.jsonBody),/grounded_fact_ids/);
const branch=wf04.connections['Constructed Diagram?']?.main??[];
assert.equal(branch?.[0]?.[0]?.node,'Construct Diagram Visual','diagram branch must construct locally');
assert.equal(branch?.[1]?.[0]?.node,'Download Reserved Visual','external-media branch must still use real provider media');
assert.match(String(by04['Expand Reserved Story Assets'].parameters.jsCode),/representation==='diagram'/);
assert.match(String(by04['Verify Reserved Visual Identity'].parameters.jsCode),/story!=='storyboard-first-v1'/);

assert.ok(String(by05['Require Eligible Render Job'].parameters.jsCode).includes('storyboard-first-v1'),'WF05 must accept storyboard-first-v1 as V6');
assert.match(String(by05['Render Video'].parameters.url),/storyboard-first-v1/);
assert.match(String(by05['Render Video'].parameters.url),/render-v6/);
assert.match(String(by05['Prepare Render Manifest'].parameters.jsCode),/diagram_spec/);
assert.match(String(by05['Prepare Render Manifest'].parameters.jsCode),/grounded_fact_ids/);
assert.match(String(by05['Validate Render Result'].parameters.jsCode),/storyboard-first-render-v1/);

const server=fs.readFileSync('services/media-worker/src/server.mjs','utf8');
assert.match(server,/\/visual\/construct-diagram/);
assert.match(server,/storyboard-first-v1/);
assert.match(server,/diagram_spec/);
console.log('V6_STORYBOARD_EXECUTION_REGRESSION_PASS');
