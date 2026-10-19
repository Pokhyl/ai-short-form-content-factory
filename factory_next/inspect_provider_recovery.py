"""Inspect one durable factory-next job for possible 503 recovery without sending requests."""
import argparse
import json
import os
from pathlib import Path
from factory_v3.runtime import Runtime, load_settings
from factory_next.provider_recovery import inspect_exhausted_503

def inspect(job_id, *, root="/data", settings="/run/factory-v3/settings.json"):
    revision = os.environ["FACTORY_V3_REVISION"]
    runtime = Runtime(load_settings(settings), root, revision)
    state = json.loads((Path(root) / "factory-next-states" / job_id / "state.json").read_text())
    prep = runtime.preparations.snapshot(job_id)
    calls = runtime.ledger._call(
        "SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM "
        "(SELECT kind,state,error_code,response FROM factory_v3.preparation_calls "
        "WHERE preparation_id=%s::uuid ORDER BY started_at) t", (job_id,))
    budget = runtime.ledger._call(
        "SELECT (budgets->>%s)::integer FROM factory_v3.preparations WHERE id=%s::uuid",
        ("gemini", job_id))
    return inspect_exhausted_503(
        checkpoint=state, preparation=prep, calls=calls, gemini_budget=budget)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id")
    args = parser.parse_args()
    print(json.dumps(inspect(args.job_id), sort_keys=True))
