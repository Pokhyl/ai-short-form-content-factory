"""Executable evidence inventory; file hashes are provenance, not acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = [
 ('owner intake/concurrency', 'tests/factory_v3/test_server.py', 'acceptance/factory-v3/image-postgres-driver.txt', 'Fresh acceptance after citation change remains unverified.'),
 ('credential gateway/free quota', 'tests/factory_v3/test_credential_http.py', 'acceptance/factory-v3/response-body-billing.json', 'Per-request billing and quota gates still required.'),
 ('fetched research/source citations', 'tests/material_first/test_source_spans.py', 'tests/material_first/fixtures/studio-ru30-quotation-failure.json', 'New model ID-selection behavior needs one normal live case; offline cases cover all16 language/duration pairs.'),
 ('three photo providers/download', 'tests/factory_v3/test_providers.py', 'acceptance/factory-v3/providers-postgres.txt', 'Availability and relevance of unseen searches remain provider-dependent.'),
 ('metadata/Vision/selection', 'tests/material_first/test_metadata_mode.py', 'acceptance/factory-v3/whole-photo-previews-20261006.json', 'Metadata mode cannot prove pixels; unseen Vision judgments are not certified by saved receipts.'),
 ('global variety/composition', 'tests/material_first/test_operations.py', 'tests/material_first/fixtures/coffee-en30-cadence-failure.json', 'Actual new model prose and image variety remain unverified.'),
 ('independent factual script review', 'tests/factory_v3/test_gemini.py', 'tests/material_first/fixtures/bread-ru45-short-draft.json', 'Source span identity proves text origin, not semantic support; independent review remains mandatory.'),
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
    output = ROOT / 'acceptance/factory-v3/source-spans-boundaries.json'
    output.write_text(json.dumps(inventory(), indent=2) + '\n')
    print(json.dumps({'boundaries': len(BOUNDARIES), 'project_ready': False}))
