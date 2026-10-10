'use strict';
// Run inside the exact deployed n8n image, without credentials or provider calls.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Module = require('module');
const root = process.argv[2];
const nativePath = '/usr/local/lib/node_modules/n8n/node_modules/n8n-nodes-base/dist/nodes/HttpRequest/V3/HttpRequestV3.node.js';
const source = fs.readFileSync(nativePath, 'utf8');
const native = new Module(nativePath, module);
native.filename = nativePath;
native.paths = Module._nodeModulePaths(path.dirname(nativePath));
native._compile(source + '\nmodule.exports.parseForContractTest = parseJsonParameter;', nativePath);
const parse = native.exports.parseForContractTest;
const workflow = JSON.parse(fs.readFileSync(path.join(root, 'workflows/VIDEO-V3-Credential-Gateway.json')));
const payload = {
  query: {q: 'bee flower', per_page: 8},
  headers: {'x-goog-user-project': 'controlled-project'},
  body: {contents: [{parts: [{text: 'Żółty цветок\n"quoted" 🌼'}]}]},
};
let checks = 0;
const expression = value => {
  assert(value.startsWith('={{') && value.endsWith('}}'));
  return new Function('$json', 'return (' + value.slice(3, -2) + ');')(payload);
};
// Reproduce the previous object-valued expression at the actual parser boundary.
for (const [field, value] of Object.entries(payload)) {
  assert.throws(() => parse({name: 'Controlled HTTP', parameters: {}}, value, field, 0),
    /not valid JSON/);
}
for (const node of workflow.nodes.filter(n => n.type.endsWith('.httpRequest'))) {
  for (const [enabled, parameter, field] of [
    ['sendQuery', 'jsonQuery', 'query'],
    ['sendHeaders', 'jsonHeaders', 'headers'],
    ['sendBody', 'jsonBody', 'body'],
  ]) {
    if (!node.parameters[enabled]) continue;
    const value = expression(node.parameters[parameter]);
    assert.strictEqual(typeof value, 'string');
    assert.deepStrictEqual(parse(node, value, parameter, 0), payload[field]);
    checks++;
  }
  if (node.parameters.sendBody) assert.strictEqual(node.parameters.contentType, 'json');
}
// Execute the installed native text/full-response output branch, not a mirrored mapper.
const assignment = source.indexOf('returnItem[outputPropertyName] = toText(response[property]);');
assert(assignment > 0);
const start = source.lastIndexOf('if (fullResponse) {', assignment);
const end = source.indexOf('// responseFormat:', assignment);
assert(start > 0 && end > start);
const branch = source.slice(start, end).replace(/\}\s*else\s*\{\s*$/, '');
const mapNative = new Function('response', 'outputPropertyName', 'toText',
  'const fullResponse=true, fullResponseProperties=["body","headers","statusCode","statusMessage"], returnItems=[], itemIndex=0;'
  + branch + ';return returnItems[0].json;');
const normalizeCode = workflow.nodes.find(n => n.name === 'Sanitize receipt').parameters.jsCode;
const normalizeReceipt = data => new Function('$input','$execution',normalizeCode)(
  {first:()=>({json:data})},{id:'controlled-native'})[0].json;
const nativeResponse = {statusCode:200, headers:{'content-type':'application/json'},
  body:JSON.stringify({projectId:'controlled-project',billingEnabled:false})};
const oldOutput = mapNative(nativeResponse, 'data', String);
assert.strictEqual(oldOutput.body, undefined);
assert.strictEqual(normalizeReceipt(oldOutput).status, 502);
for (const node of workflow.nodes.filter(n => n.type.endsWith('.httpRequest'))) {
  assert.strictEqual(node.onError, 'continueRegularOutput');
  assert.strictEqual(node.retryOnFail, false);
  const options=node.parameters.options.response.response;
  assert.strictEqual(options.responseFormat, 'text');
  assert.strictEqual(options.outputPropertyName, 'body');
  const output=mapNative(nativeResponse, options.outputPropertyName, String);
  assert.deepStrictEqual(normalizeReceipt(output).body, JSON.parse(nativeResponse.body));
}
// The native continue-on-error output must still reach a safe explicit receipt.
for (const errorOutput of [{error:'read ECONNRESET'}, {error:{message:'timeout',request:{headers:{Authorization:'secret-fixture'}}}}, {}]) {
  const receipt=normalizeReceipt(errorOutput);
  assert.strictEqual(receipt.status,502);
  assert.strictEqual(receipt.error_status,'UNKNOWN_PROVIDER_RESULT');
  assert.strictEqual(receipt.body,null);
  assert(!JSON.stringify(receipt).includes('secret-fixture'));
}
for (const [error,reason] of [
  ['read ECONNRESET Bearer secret-fixture','UPSTREAM_CONNECTION_RESET'],
  [{code:'ETIMEDOUT',request:{password:'secret-fixture'}},'UPSTREAM_TIMEOUT'],
  ['getaddrinfo EAI_AGAIN','UPSTREAM_DNS_FAILURE'],
  ['connect ECONNREFUSED','UPSTREAM_CONNECTION_REFUSED'],
  [{message:'invalid_grant',description:'secret-fixture'},'OAUTH_GRANT_REJECTED'],
  ['The provided authorization grant is invalid or expired. secret-fixture','OAUTH_GRANT_REJECTED'],
  ['Unknown failure secret-fixture','UPSTREAM_RESPONSE_UNAVAILABLE'],
]) {
  const receipt=normalizeReceipt({error});
  assert.strictEqual(receipt.error_reason,reason);
  assert.strictEqual(receipt.error_status,'UNKNOWN_PROVIDER_RESULT');
  assert.strictEqual(receipt.body,null);
  assert(!JSON.stringify(receipt).includes('secret-fixture'));
}
const response = workflow.nodes.find(n => n.type.endsWith('.respondToWebhook'));
assert.deepStrictEqual(JSON.parse(expression(response.parameters.responseBody)), payload);
console.log(JSON.stringify({status: 'passed', actual_n8n_parser: true, actual_n8n_text_response_branch: true, provider_response_contracts: 6,
  object_expressions_rejected: 3, serialized_fields_checked: checks,
  provider_calls: 0, production_mutations: 0}));
