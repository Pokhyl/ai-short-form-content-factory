"""Executable evidence inventory; file hashes are provenance, not acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = [
 ('owner intake/concurrency', 'tests/factory_v3/test_server.py', 'acceptance/factory-v3/image-postgres-driver.txt', 'Fresh acceptance after citation change remains unverified.'),
 ('credential gateway/free quota', 'tests/factory_v3/test_credential_http.py', 'acceptance/factory-v3/response-body-billing.json', 'Per-request billing and quota gates still required.'),
 ('fetched research/source citations', 'tests/material_first/test_source_spans.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-plan.json', 'r14 reused a frozen source-grounded plan; unseen source quality and support remain provider-dependent.'),
 ('three photo providers/download', 'tests/factory_v3/test_providers.py', 'acceptance/factory-v3/providers-postgres.txt', 'Availability and relevance of unseen searches remain provider-dependent.'),
 ('retrieved metadata context planning', 'tests/material_first/test_photo_planning.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-plan.json', 'r14 reused frozen, reviewed materials; fresh discovery and enough relevant photos for every scene remain unproven.'),
 ('metadata/Vision/selection', 'tests/material_first/test_metadata_mode.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-plan.json', '17 reviewed photos were frozen; only5 supported the longest scene. New retrieval must produce sufficient scene coverage.'),
 ('global variety/composition', 'tests/material_first/test_topic_connected.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-plan.json', 'Controlled topical preparation/scheduling tests pass; live relevant-photo coverage failed at exact timing in r14.'),
 ('topical photo cadence preflight before voice', 'tests/material_first/test_topic_quality.py', 'acceptance/factory-v3/visual-capacity-preflight-20261011.json', 'Word- and character-weighted estimates now stop impossible plans before TTS; actual measured scene timing remains authoritative at render.'),
 ('independent factual script review', 'tests/factory_v3/test_gemini.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-result.json', 'r14 reached voice correction and semantic review on the source-bound script; unseen topics and scripts still require provider review.'),
 ('deployed constrained proofread -> review', 'tests/material_first/test_voice_correction.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-result.json', 'r14 used2 voice sends and3 Gemini calls; no audio playback or owner listening review is evidenced.'),
 ('one voice/alignment', 'tests/factory_v3/test_executor.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-result.json', 'Measured voices were50,928 and59,616 ms; exact alignment reached the render stage. No successful final audio/video package exists.'),
 ('whole photos/exact timing/render/audit', 'tests/material_first/test_connected_presentation.py', 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-result.json', 'r14 stopped at render with no subject-related photo for an interval; no MP4 or final-media audit exists.'),
 ('owner review/save/physical deletion', 'tests/studio-delete.test.cjs', 'acceptance/factory-v3/delete-ui-checks.json', 'Explicit HUMAN acceptance of actual new MP4 remains absent.'),
]

def inventory():
    def proof(name):
        data = (ROOT / name).read_bytes()
        return {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}
    voice_path = 'acceptance/factory-v3/voice-correction/natural-speed-regression-gemini35-r14-result.json'
    latest_voice = json.loads((ROOT / voice_path).read_text())
    return {'project_ready': False, 'scope': 'Controlled tests and saved actual receipts, not new provider acceptance',
            'latest_voice_acceptance': {'id': latest_voice['id'], 'state': latest_voice['state'],
                                        'measured_voice_durations_ms': latest_voice['measured_voice_durations_ms'],
                                        'job_status': latest_voice['job_status'],
                                        'latest_stage': latest_voice['latest_stage'],
                                        'failure_type': latest_voice['failure_type'],
                                        'render_count': latest_voice['render_count'],
                                        'receipt': proof(voice_path)},
            'boundaries': [{'name': name, 'test': proof(test), 'saved_evidence': proof(evidence),
                            'remaining': remaining} for name, test, evidence, remaining in BOUNDARIES]}

if __name__ == '__main__':
    output = ROOT / 'acceptance/factory-v3/current-boundaries.json'
    output.write_text(json.dumps(inventory(), indent=2) + '\n')
    report = inventory()
    print(json.dumps({'boundaries': len(BOUNDARIES), 'latest_voice_acceptance': report['latest_voice_acceptance'], 'project_ready': False}))
