"""Explicit saved-input diagnostic: new native edit/review, no discovery or TTS.

Saved composition responses are test inputs, never cache hits for changed prompts.
The fresh diagnostic preparation is terminalized even when its boundary passes;
it cannot be confused with a prepared/renderable production job.
"""
import argparse
import json
from pathlib import Path

from factory_v3.runtime import Runtime, load_settings
from factory_v3.gemini import validate_json
from factory_v3.grounding import validate_script_review
from material_first.paragraphs import compose_paragraphs
from material_first.engine import fit_contextual_paragraphs, validate_story
from material_first.visuals import make_visuals


def main():
    parser = argparse.ArgumentParser()
    for name in ('plan', 'context', 'responses', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    context = json.loads(Path(args.context).read_text())
    rows = {r['key']: r for r in json.loads(Path(args.responses).read_text())}
    runtime = Runtime(load_settings('/run/factory-v3/settings.json'), '/data', plan['revision'])
    request = context['request']
    diagnostic = {**request, 'diagnostic': 'saved-composition-boundary',
                  'source_id': plan['source_id']}
    # INSERT has a unique key: this script never resumes or repeats a prior ID.
    limit = plan['maximum_calls']['gemini']
    if type(limit) is not int or not 2 <= limit <= 6:
        raise ValueError('diagnostic Gemini budget must be between two and six')
    runtime.preparations.create(plan['id'], diagnostic, {'gemini': limit, 'metadata': 1})
    runtime.preparations.claim_run(plan['id'])
    result = {'id': plan['id'], 'source_id': plan['source_id'],
              'revision': plan['revision'], 'project_ready': False,
              'new_searches': 0, 'new_downloads': 0, 'new_tts': 0}
    try:
        producer = runtime.producer(plan['id'])
        producer.authorize()
        gemini = producer.operations.gemini
        gemini.retry_unavailable = plan.get('retry_explicit_unavailable', False)

        class SavedInputThenNativeEdit:
            def generate(self, key, instruction, payload, schema):
                if key == 'material-language-edit':
                    return gemini.generate(key, instruction, payload, schema,
                                           max_tokens=plan.get('native_edit_max_tokens', 8192))
                if key not in {'material-compose', 'material-compose-length-repair'}:
                    raise ValueError('unexpected saved-input boundary')
                raw = rows[key]['response']['body']
                candidate, = raw['candidates']
                if candidate['finishReason'] != 'STOP':
                    raise ValueError('incomplete saved response')
                value = json.loads(''.join(p['text'] for p in candidate['content']['parts']
                                          if 'text' in p and not p.get('thought')))
                validate_json(value, schema)
                return value, {}

        draft = compose_paragraphs(SavedInputThenNativeEdit(), context, ValueError)
        result['draft'] = draft
        draft = fit_contextual_paragraphs(context['materials'], draft, seconds=request['seconds'])
        scenes = validate_story(request, context['evidence'], context['materials'], draft)
        script = ' '.join(s['narration'] for s in scenes)
        review_input = {**request, 'script': script, 'scenes': scenes,
                        'evidence': context['evidence'], 'materials': context['materials']}
        review = producer.operations.review_script(review_input)
        result.update(script=script, review=review)
        if review.get('native_language_quality') is not True:
            raise ValueError('native-language review did not pass')
        validate_script_review(context['evidence'], request['language'], script, scenes,
                               review, topic=request['topic'])
        visuals = make_visuals(request['seconds'], context['materials'], scenes,
                               request['presentation_policy'])
        result.update(state='boundary_passed', visuals=visuals)
    except Exception as error:
        result.update(state='boundary_failed', error_type=type(error).__name__,
                      error=str(error))
    finally:
        result['calls'] = runtime.ledger._call(
            "SELECT jsonb_agg(jsonb_build_object('key',call_key,'state',state,"
            "'status',response->'status','error_status',response->'error_status')) "
            "FROM factory_v3.preparation_calls WHERE preparation_id=%s::uuid", (plan['id'],))
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        # A provider transport failure may already have terminalized the row.
        # Preserve that unknown/failed outcome instead of masking it with a
        # second terminal-state exception from the diagnostic cleanup.
        status = runtime.preparations.snapshot(plan['id'])['status']
        if status not in {'failed', 'unknown', 'prepared'}:
            runtime.preparations.reject(plan['id'], 'DiagnosticBoundaryComplete' if
                                        result.get('state') == 'boundary_passed' else
                                        result.get('error_type', 'DiagnosticInterrupted'))
    print(json.dumps({k: v for k, v in result.items() if k not in {'draft', 'script', 'review', 'visuals'}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
