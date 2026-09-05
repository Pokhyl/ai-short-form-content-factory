import assert from "node:assert/strict";
import fs from "node:fs";

const raw=JSON.parse(fs.readFileSync("n8n/workflows/WF01-create-content-job.json","utf8"));
const wf=Array.isArray(raw)?raw[0]:raw;
assert.equal(wf.id,"Xy94qe35OigtMxkR");
const insert=wf.nodes.find(n=>n.name==="Insert Job");
const respond=wf.nodes.find(n=>n.name==="Return Created Job");
const start=wf.nodes.find(n=>n.name==="Start Script Planning");
assert.ok(insert&&respond&&start,"WF01 intake/orchestration nodes must exist");
assert.equal(start.type,"n8n-nodes-base.executeWorkflow");
assert.equal(start.parameters?.workflowId?.value,"TJfA4ZYUEKSTad6k","WF01 must start WF02");
assert.equal(start.parameters?.workflowInputs?.value?.job_id,"={{ $json.job_id }}","WF01 must pass only persisted job_id into WF02");
assert.equal(start.parameters?.options?.waitForSubWorkflow,false,"WF01 webhook response must not block on full generation");
const next=(wf.connections?.["Insert Job"]?.main?.[0]??[]).map(x=>x.node);
assert.ok(next.includes("Return Created Job"),"WF01 must return created job id");
assert.ok(next.includes("Start Script Planning"),"WF01 must autonomously launch generation after insert");
assert.equal(wf.nodes.filter(n=>n.type==="n8n-nodes-base.executeWorkflow").length,1,"WF01 should have one downstream orchestrator handoff");
console.log("WF01_N8N_ORCHESTRATION_REGRESSION_PASS");
