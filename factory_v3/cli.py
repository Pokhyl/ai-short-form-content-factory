"""Internal operator entrypoint. Public callers cannot submit fabricated review receipts."""
import argparse
import json
import os
from pathlib import Path
from .ledger import PostgresLedger
from .executor import Executor
from .worker_adapters import GoogleVoice, WorkerAdapters
from scripts.audit_final_media import audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation",choices=["create","step","status"])
    parser.add_argument("job_id")
    parser.add_argument("--plan",type=Path)
    parser.add_argument("--media-root",type=Path,default=Path("/data"))
    args = parser.parse_args()
    ledger = PostgresLedger(os.environ["V3_DATABASE_URL"])
    if args.operation=="status":
        state=ledger.snapshot(args.job_id)
        print(json.dumps({"id":state["id"],"status":state["status"],"completed":list(state["outputs"])}))
        return
    def token():
        return Path(os.environ["V3_GOOGLE_ACCESS_TOKEN_FILE"]).read_text().strip()
    adapters=WorkerAdapters(args.media_root,GoogleVoice(token),
        os.environ.get("V3_WORKER_URL","http://shorts-v2-media-worker-1:3001"),audit)
    executor=Executor(ledger,args.media_root,adapters)
    if args.operation=="create":
        if args.plan is None:
            parser.error("--plan is required for create")
        executor.create(args.job_id,json.loads(args.plan.read_text()))
        print(json.dumps({"id":args.job_id,"status":"prepared"}))
    else:
        state=executor.run_next(args.job_id)
        print(json.dumps({"id":state["id"],"status":state["status"]}))


if __name__=="__main__":
    main()
