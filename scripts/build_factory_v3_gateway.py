"""Generate the scoped native credential gateway; never import/publish implicitly."""
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ID = "VIDEO-V3-Credential-Gateway"
TOKEN_CREDENTIAL = "V3ProviderGatewayToken"
guard = (ROOT / "factory_v3/gateway_validate.js").read_text().split("if (typeof module")[0]
nodes = []
def node(name, kind, version, parameters, position, credentials=None):
    value = {"id": str(uuid5(NAMESPACE_URL, WORKFLOW_ID + "/" + name)),
             "name": name, "type": "n8n-nodes-base." + kind, "typeVersion": version,
             "parameters": parameters, "position": position}
    if kind == "webhook":
        value["webhookId"] = str(uuid5(NAMESPACE_URL, WORKFLOW_ID + "/webhook"))
    if credentials:
        value["credentials"] = credentials
    if kind == "httpRequest":
        value["retryOnFail"] = False
        value["onError"] = "continueRegularOutput"
    nodes.append(value)

node("Authenticated provider request", "webhook", 2, {
    "path": "factory-v3-internal-provider", "httpMethod": "POST",
    "authentication": "headerAuth", "responseMode": "responseNode", "options": {}}, [0,0],
    {"httpHeaderAuth": {"id": TOKEN_CREDENTIAL, "name": "Factory V3 private gateway"}})
node("Validate scoped request", "code", 2, {"jsCode": guard +
    "\nreturn [{json: validateProviderRequest($input.first().json.body)}];"}, [240,0])
providers = ["pixabay","pexels","gemini","google_tts","gemini_info","google_metadata"]
rules = [{"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
    "conditions": [{"leftValue": "={{ $json.provider }}", "rightValue": provider,
                    "operator": {"type": "string", "operation": "equals"}}],
    "combinator": "and"}, "renameOutput": True, "outputKey": provider} for provider in providers]
node("Select credential", "switch", 3.2, {"rules": {"values": rules}, "options": {}}, [480,0])
credentials = {
    "pixabay": {"httpQueryAuth": {"id": "Z61TBglXcV08CRbT", "name": "Pixabay API"}},
    "pexels": {"httpHeaderAuth": {"id": "l6QGoHtq4KUiMaWe", "name": "Pexels API"}},
    "gemini": {"googlePalmApi": {"id": "V3GeminiFreeTier20261005", "name": "Factory V3 verified Gemini Free tier"}},
    "google_tts": {"googleOAuth2Api": {"id": "8KbFC6GBZOd18bzG", "name": "Google account"}},
}
for index, provider in enumerate(providers):
    auth = credentials["gemini" if provider == "gemini_info" else "google_tts" if provider == "google_metadata" else provider]
    credential_type = next(iter(auth))
    params = {"method": "={{ $json.method }}", "url": "={{ $json.url }}",
        "options": {"timeout": 120000, "response": {"response": {
            "fullResponse": True, "neverError": True, "responseFormat": "text",
            "outputPropertyName": "body"}}}}
    if credential_type in {"httpQueryAuth","httpHeaderAuth"}:
        params.update({"authentication":"genericCredentialType","genericAuthType":credential_type})
    else:
        params.update({"authentication":"predefinedCredentialType","nodeCredentialType":credential_type})
    if provider == "pixabay":
        keys = ["q","per_page","image_type","safesearch","orientation","lang"]
    elif provider == "pexels":
        keys = ["query","per_page","orientation"]
    elif provider == "google_metadata":
        keys = ["keyString"]
    else:
        keys = []
    if keys:
        params["sendQuery"] = True
        params["specifyQuery"] = "json"
        params["jsonQuery"] = "={{ JSON.stringify($json.query || {}) }}"
    if provider == "google_metadata":
        params.update({"sendHeaders":True,"specifyHeaders":"json",
                       "jsonHeaders":"={{ JSON.stringify($json.headers || {}) }}"})
    if provider in {"gemini","google_tts"}:
        params.update({"sendBody":True,"contentType":"json","specifyBody":"json","jsonBody":"={{ JSON.stringify($json.body) }}"})
    node("Upstream " + provider, "httpRequest", 4.5, params, [760,index*180], auth)
normalize = """
const upstream = $input.first().json;
let status = Number(upstream.statusCode);
if (!Number.isInteger(status) || status < 100 || status > 599) {
  // A transport failure may occur after the provider accepted the request.
  // Never retry it or leak native error objects containing request credentials.
  return [{json:{status:502, headers:{}, body:null,
    error_status:'UNKNOWN_PROVIDER_RESULT', error_reason:'UPSTREAM_RESPONSE_UNAVAILABLE',
    gateway_execution_id:String($execution.id)}}];
}
const allowed = new Set(['date','cache-control','retry-after','content-type','x-ratelimit-limit','x-ratelimit-remaining','x-ratelimit-reset']);
const headers = {};
for (const [key,value] of Object.entries(upstream.headers || {})) {
  if (allowed.has(key.toLowerCase())) headers[key.toLowerCase()] = String(value);
}
let body = null, error_status, error_reason, error_message;
try { body = typeof upstream.body === 'string' ? JSON.parse(upstream.body) : upstream.body; }
catch { if (status >= 200 && status < 300) status = 502; }
if (status >= 200 && status < 300 && (body === null || typeof body !== 'object')) status = 502;
if (status >= 400) {
  const error = body?.error;
  if (/^[A-Z_]{1,100}$/.test(error?.status || '')) error_status = error.status;
  const detail = (error?.details || []).find(d => /^[A-Z_]{1,100}$/.test(d.reason || ''));
  if (detail) error_reason = detail.reason;
  if (typeof error?.message === 'string') {
    error_message = error.message
      .replace(/([?&](?:key|keyString|access_token)=)[^&\\s"']+/gi,'$1[redacted]')
      .replace(/Bearer\\s+[^\\s"']+/gi,'Bearer [redacted]')
      .replace(/[A-Za-z0-9_-]{24,}/g,'[redacted]').slice(0,750);
  }
  body = null;
}
return [{json:{status, headers, body, error_status, error_reason, error_message,
               gateway_execution_id: String($execution.id)}}];
"""
node("Sanitize receipt", "code", 2, {"jsCode": normalize}, [1080,0])
node("Return receipt", "respondToWebhook", 1.4, {"respondWith":"json","responseBody":"={{ JSON.stringify($json) }}",
    "options":{"responseCode":200}}, [1320,0])
connections = {
    "Authenticated provider request":{"main":[[{"node":"Validate scoped request","type":"main","index":0}]]},
    "Validate scoped request":{"main":[[{"node":"Select credential","type":"main","index":0}]]},
    "Select credential":{"main":[[{"node":"Upstream "+p,"type":"main","index":0}] for p in providers]},
    "Sanitize receipt":{"main":[[{"node":"Return receipt","type":"main","index":0}]]},
}
for provider in providers:
    connections["Upstream "+provider]={"main":[[{"node":"Sanitize receipt","type":"main","index":0}]]}
workflow = {"id":WORKFLOW_ID,"name":WORKFLOW_ID,"active":False,"nodes":nodes,"connections":connections,
    "settings":{"executionOrder":"v1","executionTimeout":180,"saveManualExecutions":False,
                "saveDataSuccessExecution":"none","saveDataErrorExecution":"none"}}
path = ROOT / "workflows/VIDEO-V3-Credential-Gateway.json"
path.write_text(json.dumps(workflow,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"workflow":WORKFLOW_ID,"nodes":len(nodes),"imported":False,"provider_calls":0}))
