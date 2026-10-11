"""Executable evidence inventory; file hashes are provenance, not acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = [
 ('owner intake/concurrency', 'tests/factory_v3/test_server.py', 'acceptance/factory-v3/image-postgres-driver.txt', 'Fresh acceptance after citation change remains unverified.'),
 ('credential gateway/free quota', 'tests/factory_v3/test_credential_http.py', 'acceptance/factory-v3/response-body-billing.json', 'Per-request billing and quota gates still required.'),
 ('fetched research/source citations', 'tests/material_first/test_source_spans.py', 'acceptance/factory-v3/source-spans-pl15-result.json', 'Actual prior PL15 source-span case passed; unseen source-span selection and semantic support still require independent review.'),
 ('three photo providers/download', 'tests/factory_v3/test_providers.py', 'acceptance/factory-v3/providers-postgres.txt', 'Availability and relevance of unseen searches remain provider-dependent.'),
 ('retrieved metadata context planning', 'tests/material_first/test_photo_planning.py', 'acceptance/factory-v3/wholeplan-saved-distinctness.json', 'Planner strict protocol flags now propagated; actual old15 photos contain1copy/14distinct. Current strict-qualified output pending.'),
 ('metadata/Vision/selection', 'tests/material_first/test_metadata_mode.py', 'acceptance/factory-v3/whole-photo-previews-20261006.json', 'Metadata mode cannot prove pixels; unseen Vision judgments are not certified by saved receipts.'),
 ('global variety/composition', 'tests/material_first/test_topic_connected.py', 'acceptance/factory-v3/wholeplan-uk60-plan.json', 'Controlled current topical16-pair prepare/freeze/schedule matrix passes; actual new model prose, qualified images and image variety remain unverified.'),
 ('independent factual script review', 'tests/factory_v3/test_gemini.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini36-r9-result.json', 'The latest completed independent review rejected selected Ukrainian grammar. The constrained proofread fix is deployed, but r10/r11 stopped before proofread/review on Gemini HTTP503.'),
 ('deployed constrained proofread -> review', 'tests/material_first/test_voice_correction.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini36-r11-result.json', 'Offline regression passes and code is deployed; live proofread has not run because r11 rewrite received Gemini HTTP503 first.'),
 ('one voice/alignment', 'tests/factory_v3/test_executor.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini36-r11-result.json', 'Latest r11 reached one natural TTS at 52,704 ms, then stopped on Gemini HTTP503. No corrected voice, alignment, or listening acceptance.'),
 ('whole photos/exact timing/render/audit', 'tests/material_first/test_connected_presentation.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini36-r11-result.json', 'r11 stopped before alignment/render; no current-release MP4 or final-media audit exists.'),
 ('owner review/save/physical deletion', 'tests/studio-delete.test.cjs', 'acceptance/factory-v3/delete-ui-checks.json', 'Explicit HUMAN acceptance of actual new MP4 remains absent.'),
]

def inventory():
    def proof(name):
        data = (ROOT / name).read_bytes()
        return {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}
    voice_path = 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini36-r11-result.json'
    latest_voice = json.loads((ROOT / voice_path).read_text())
    return {'project_ready': False, 'scope': 'Controlled tests and saved actual receipts, not new provider acceptance',
            'latest_voice_acceptance': {'id': latest_voice['id'], 'state': latest_voice['state'],
                                        'duration_ms': latest_voice['measured_voice_durations_ms'][0],
                                        'failure_type': latest_voice['failure_type'],
                                        'gateway_status': latest_voice['gateway_receipt']['status'],
                                        'proofread_step_reached': latest_voice['proofread_step_reached'],
                                        'render_count': latest_voice['render_count'],
                                        'receipt': proof(voice_path)},
            'boundaries': [{'name': name, 'test': proof(test), 'saved_evidence': proof(evidence),
                            'remaining': remaining} for name, test, evidence, remaining in BOUNDARIES]}

if __name__ == '__main__':
    output = ROOT / 'acceptance/factory-v3/current-boundaries.json'
    output.write_text(json.dumps(inventory(), indent=2) + '\n')
    report = inventory()
    print(json.dumps({'boundaries': len(BOUNDARIES), 'latest_voice_acceptance': report['latest_voice_acceptance'], 'project_ready': False}))
