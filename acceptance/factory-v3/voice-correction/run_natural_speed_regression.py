"""Bounded live measured-TTS regression using an existing frozen product plan."""
import copy
import json
import os
from pathlib import Path

from factory_v3.runtime import Runtime, load_settings
from factory_v3.preflight import digest
from material_first.engine import verify
from material_first.voice_correction import POLICY

IDENTITY = '1c2bafd9-00a0-47c1-884c-372265df5fe5'
SOURCE = '72705d11-4556-4a4a-b751-676cc71e215d'
REVISION = 'fe7fab4acbe6d36e1a76458087436358a62c7b7a'

r = Runtime(load_settings('/run/factory-v3/settings.json'), '/data',
            os.environ['FACTORY_V3_REVISION'])
if r.revision != REVISION:
    raise RuntimeError('deployed source revision differs from committed plan')
try:
    r.preparations.snapshot(IDENTITY)
except KeyError:
    pass
else:
    raise RuntimeError('regression ID already exists; never repeat it')

folder = Path('/data/checks') / ('natural-speed-regression-' + IDENTITY)
folder.mkdir(parents=True, exist_ok=False)
receipt = {'id': IDENTITY, 'source_job': SOURCE, 'revision': r.revision,
           'state': 'preflight', 'new_research': 0, 'photo_searches': 0,
           'photo_downloads': 0, 'photo_inspections': 0, 'tts_sends': 0,
           'gemini_calls': 0, 'render_count': 0}


def save():
    (folder / 'receipt.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: receipt.get(k) for k in
                      ('id', 'state', 'tts_sends', 'gemini_calls')},
                     ensure_ascii=False), flush=True)


try:
    source = r.ledger.snapshot(SOURCE)['frozen']
    frozen = copy.deepcopy(source)
    original_payload = copy.deepcopy(frozen['payload'])
    frozen['payload']['voice_correction'] = dict(POLICY)
    frozen['sha256'] = digest(frozen['payload'])
    verify('/data', frozen)
    unchanged = {k: v for k, v in frozen['payload'].items()
                 if k != 'voice_correction'}
    if unchanged != original_payload:
        raise ValueError('voice policy changed the source product plan')
    receipt.update(state='source_plan_verified', source_plan_sha256=source['sha256'],
                   initial_plan_sha256=frozen['sha256'])
    save()

    request = r.preparations.snapshot(SOURCE)['request']
    r.preparations.create(IDENTITY, request, {'gemini': 4, 'metadata': 1})
    r.preparations.claim_run(IDENTITY)
    producer = r.producer(IDENTITY)
    producer.authorize()  # Read-only free-tier/billing proof; no generation.
    r.preparations.complete(IDENTITY, frozen)

    executor = r.executor()
    for stage in ('voice', 'align', 'render', 'qa'):
        receipt['state'] = stage
        save()
        state = executor.run_next(IDENTITY)

    state = r.ledger.snapshot(IDENTITY)
    outputs = state['outputs']
    voice, render, qa = outputs['voice'], outputs['render'], outputs['qa']
    attempts = voice.get('voice_attempts', [])
    rows = r.ledger._call(
        "SELECT COALESCE(jsonb_object_agg(kind,n),'{}'::jsonb) FROM "
        "(SELECT kind,count(*) AS n FROM factory_v3.preparation_calls "
        "WHERE preparation_id=%s::uuid GROUP BY kind) counts", (IDENTITY,))
    receipt.update(
        state='complete_diagnostic_only', job_status=state['status'],
        tts_sends=len(attempts), gemini_calls=rows.get('gemini', 0),
        metadata_calls=rows.get('metadata', 0),
        voice_duration_ms=voice.get('duration_ms'),
        voice_sha256=voice.get('sha256'),
        render_duration_ms=render.get('actual_duration_ms'),
        audio_tempo_factor=render.get('audio_tempo_factor'),
        render_audio_duration_ms=render.get('audio_duration_ms'),
        render_sha256=render.get('sha256'),
        qa_machine_pass=qa.get('machine_pass'), qa_human_pass=qa.get('human_pass'),
        source_plan_unchanged=True, project_ready=False)
    if (state['status'] != 'qa_pass' or not 59000 <= voice['duration_ms'] <= 60000
            or render.get('audio_tempo_factor') != 1.0
            or render.get('actual_duration_ms') != 60000
            or len(attempts) > 3 or rows.get('gemini', 0) > 4):
        receipt['state'] = 'failed_terminal'
        receipt['acceptance'] = False
    else:
        receipt['acceptance'] = True
    save()
except BaseException as error:
    receipt.update(state='failed_terminal', failure_type=type(error).__name__,
                   failure=str(error)[:1000])
    save()
    raise
