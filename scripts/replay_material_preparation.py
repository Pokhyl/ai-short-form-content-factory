"""Read-only saved-response replay. Missing calls NEVER invoke a provider."""
import argparse
import json
import os
from factory_v3.runtime import Runtime, load_settings
from factory_v3.preparation import ResourceUnavailable
from material_first.engine import Producer

parser = argparse.ArgumentParser()
parser.add_argument('--id', required=True)
args = parser.parse_args()
runtime = Runtime(load_settings('/run/factory-v3/settings.json'), '/data', os.environ['FACTORY_V3_REVISION'])
prep = runtime.preparations.snapshot(args.id)
if prep['status'] not in {'failed', 'unknown', 'prepared'}:
    raise ValueError('replay only an inactive saved preparation')
rows = runtime.ledger._call("SELECT jsonb_agg(jsonb_build_object('key',call_key,'response',response,'state',state)) "
                          "FROM factory_v3.preparation_calls WHERE preparation_id=%s::uuid", (args.id,))
saved = {row['key']: row for row in rows}
used, observed = [], {}

class MissingSavedCall(RuntimeError):
    pass

class Replay:
    def run(self, key, kind, request, invoke, **kwargs):
        if key not in saved:
            raise MissingSavedCall(key)
        row = saved[key]
        if row['state'] == 'failed' and kwargs.get('allow_unavailable'):
            raise ResourceUnavailable(row['response'])
        if row['state'] != 'succeeded':
            raise ValueError('saved call is not known successful')
        used.append(key)
        return row['response']

ops = runtime.producer(args.id).operations
for component in (ops.source, ops.gemini, ops.search, ops.downloader, ops.downloader.downloader):
    component.calls = Replay()
review = ops.review_script

def record_review(context):
    observed.update({'script': context['script'], 'words': len(context['script'].split()),
                     'inspected_photos': len(context['materials']),
                     'required_fact_ids': context['required_fact_ids']})
    return review(context)

ops.review_script = record_review
request = prep['request']
try:
    Producer('/data', ops).prepare(request['topic'], request['language'], request['seconds'])
    state = 'saved_complete_plan_replayed'
except MissingSavedCall as error:
    state = 'missing_saved_call:' + str(error)
print(json.dumps({'id': args.id, 'replay_revision': runtime.revision, 'state': state,
                  'new_provider_calls': 0, 'new_model_calls': 0, 'new_tts_calls': 0,
                  'database_writes': 0, 'used_saved_calls': used, **observed}, ensure_ascii=False, indent=2))
