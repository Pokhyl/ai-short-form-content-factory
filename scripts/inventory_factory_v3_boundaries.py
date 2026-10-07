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
 ('metadata/Vision/selection', 'tests/material_first/test_metadata_mode.py', 'acceptance/factory-v3/whole-photo-previews-20261006.json', 'Metadata mode cannot prove pixels; unseen Vision judgments are not certified by saved receipts.'),
 ('global variety/composition', 'tests/material_first/test_topic_connected.py', 'acceptance/factory-v3/resumed-uk60-plan.json', 'Controlled current topical16-pair prepare/freeze/schedule matrix passes; actual new model prose, qualified images and image variety remain unverified.'),
 ('independent factual script review', 'tests/factory_v3/test_gemini.py', 'acceptance/factory-v3/query-review-deployment.json', 'Exact keyed narrated-fact schema deployed; incomplete actual historical review remains rejected. Current case has no accepted full factual/native review yet.'),
 ('one voice/alignment', 'tests/factory_v3/test_executor.py', 'acceptance/factory-v3/connected-presentation-real-worker-fixture.json', 'No fresh TTS or listening acceptance for this release.'),
 ('whole photos/exact timing/render/audit', 'tests/material_first/test_connected_presentation.py', 'acceptance/factory-v3/whole-photo-previews-20261006.json', 'Real cached worker outputs support renderer only; no fresh current-release MP4 yet.'),
 ('owner review/save/physical deletion', 'tests/studio-delete.test.cjs', 'acceptance/factory-v3/delete-ui-checks.json', 'Explicit HUMAN acceptance of actual new MP4 remains absent.'),
]

def inventory():
    def proof(name):
        data = (ROOT / name).read_bytes()
        return {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}
    return {'project_ready': False, 'scope': 'Controlled tests and saved actual receipts, not new provider acceptance',
            'boundaries': [{'name': name, 'test': proof(test), 'saved_evidence': proof(evidence),
                            'remaining': remaining} for name, test, evidence, remaining in BOUNDARIES]}

if __name__ == '__main__':
    output = ROOT / 'acceptance/factory-v3/current-boundaries.json'
    output.write_text(json.dumps(inventory(), indent=2) + '\n')
    print(json.dumps({'boundaries': len(BOUNDARIES), 'project_ready': False}))
