# Factory repair: start here
Snapshot for Codex handoff after owner request, 2026-10-20 17:26 Europe/Warsaw.

Goal: finish the automatic video factory for arbitrary topics, PL/EN/RU/UK and15/30/45/60seconds. Owner explicitly removed automatic503 retries. No paid fallback, fabricated approvals, tempo manipulation, manual one-topic substitute, or modifications to unrelated projects. Do not claim completion without a new normal automatically produced MP4 and actual audit.

Repository: Pokhyl/ai-short-form-content-factory.
Branch: fix/provider-deferral-sequence-20261020.
Current source candidate:6d10ca7544facb9b47f37a532426c2d7794d2a48.
Read docs/OPERATOR_RULES.md, then THIS snapshot; historical dated notes below docs/CODEX_HANDOFF.md are not current instructions.

## Live versus candidate
LIVE Studio https://studio.hodor.com.pl/factory-next/ runs bf800a35f743735b451c8ee620be4995a393b1c5, container factory-next-studio-v9, image sha256:56646d33d1a8a8ee6a50a0f58213db9bf5ca229dbe0b5d917242cfe5e4e8ac53. Automatic provider retry loop/options, ProviderResumeGate, pipeline/operator resume and Studio503 scheduling were removed.179Next/123core packaged checks passed; runtime absence of retry options/gate, publichealth200/exactgateway403 verified. No provider_wait jobs. Two historic complete jobs are not acceptance of new code.

CANDIDATE6d10ca7 is NOT deployed. Clean release /opt/factory-source-context-release-6d10ca7; image factory-v3:factory-next-source-context-6d10ca7, sha256:6f854219ce64a5c7e4d474dfc57f521e56ad43bf2fe80a6116da55831a0bffe9.185Next/123core exact-image checks pass with networking disabled and no runtime source overlay. It bounds only research generation/repair source context via factory_next/source_context.py. Actual DNA corpus146214->17722chars,131->16 exact whole spans, source coverage7/7/2. Full original pages, hashes, citation binding and independent reviews remain unchanged. Six additional retrieval/schema/citation regressions pass.

## Actual provider evidence
Current selected reasoning model Gemini3.8Flash is unavailable in multiple distinct bounded checks. Source-context research2eda70ca-d9b1-47b7-8d46-26f713fc58a5 returned503 high demand after4.735s, one physical call/no retry. Prior full-context Ukrainian DNA2e1a444d-20b0-4639-a445-d91076fcb455 returned503 after249.129s,146214chars. This DOES NOT establish that context size causes503 or that the cap restores availability. Prior0d8477b1... also explicit503. None is semantic research acceptance. Candidate is held before deployment/new full request.

Old normal4fa81f5b-04ec-43cd-8e3e-a5159ec8829f is terminal at research with final review3 UNKNOWN502. Old77e850da-b9aa-479f-9e10-e763ea4b2789 is terminal unknown narrative review. Never replay/rescue failed/unknown IDs. No new MP4.

## Pending alternative-model diagnostic: NOT EXECUTED
Gemini3.6Flash official Standard pricing lists free input/output including thinking: https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash. No runtime model change/fallback implemented.
Fresh diagnostic a6647022-f98f-430c-97cd-fff70f4e89ca passed a fresh billing-disabled gate and reserved exactly one Gemini call under key reviewer36-evaluation. Reservation state may be started, but native provider execution has NOT occurred. Inactive n8n workflow F3Eval3620261020B was imported, using existing credential reference V3GeminiFreeTier20261005 and the same six positive/negative controls previously used to reject the weak model. No publish/restart/production gateway changes.

VPS operations files: /opt/factory-source-context-20261020/acceptance/factory-v3/reviewer36-evaluation-{plan,input}-20261020.json and reviewer36-reservation-20261020.json. Workflow source: /opt/factory-source-context-20261020/workflows/VIDEO-Factory-Reviewer36-Evaluation.json. No reviewer36-native-started marker/execution/result at handoff. Before any eventual execution inspect actual marker/native history and freshness of billing evidence; never infer permission to repeat an unknown send. Budgeted physical ceiling1Gemini/1metadata/0search/0TTS. Native raw CLI output can contain resume tokens: keep private, publish sanitized results only. No semantic approval or availability claim for3.6 exists yet.

## Runtime access and continuation
VPS ubuntu-4gb-hel1-1, SentinelX host_58bbeb7da5059807. Repository access alone does not grant server/secret access. Private settings stay /var/lib/factory-v3/settings.json; never print or commit them. Media volume shorts-v2_media_data, states /data/factory-next-states, read-only originals preserved. Keep /opt/factory-v4-clean untouched. n8n container ai-short-form-n8n; active credential gateway6624cdc6-cdff-4284-b91d-278e9f58499d unchanged.

Read source and evidence, form a concrete diagnosis, then test the smallest relevant boundary. An available model must also reject known bad claims and pass real source/native review before selection. Only after semantic boundary, exact package tests, protected deployment and exact-route verification may a new normal public request be submitted. Prepared source-context rollout/submission scripts on VPS are gated and were NOT executed. Do not use offline tests, a prepared script, a provider503 or historic video as a ready factory claim.
