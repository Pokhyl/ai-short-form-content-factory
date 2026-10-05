"""Internal operator entrypoint; user requests cannot contain fabricated approvals."""
import argparse
import json
import os
from pathlib import Path
from .runtime import Runtime, load_settings


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("operation",choices=["request","prepare","run","step","status","create","version"])
    parser.add_argument("job_id",nargs="?")
    parser.add_argument("--topic")
    parser.add_argument("--language",choices=["pl","en","ru","uk"])
    parser.add_argument("--seconds",type=int,choices=[15,30,45,60])
    parser.add_argument("--plan",type=Path)
    parser.add_argument("--settings",type=Path,default=Path("/run/factory-v3/settings.json"))
    parser.add_argument("--media-root",type=Path,default=Path("/data"))
    args=parser.parse_args()
    revision=os.environ.get("FACTORY_V3_REVISION","")
    if args.operation=="version":
        print(json.dumps({"source_revision":revision}))
        return
    if not args.job_id:
        parser.error("job_id required")
    runtime=Runtime(load_settings(args.settings),args.media_root,revision)
    if args.operation=="request":
        if any(value is None for value in (args.topic,args.language,args.seconds)):
            parser.error("--topic, --language and --seconds required")
        result=runtime.create(args.job_id,args.topic,args.language,args.seconds)
    elif args.operation=="prepare":
        frozen=runtime.producer(args.job_id).prepare(args.job_id)
        result={"id":args.job_id,"status":"prepared","plan_sha256":frozen["sha256"]}
    elif args.operation=="run":
        result=runtime.run(args.job_id)
    elif args.operation=="step":
        state=runtime.executor().run_next(args.job_id)
        result={"id":args.job_id,"status":state["status"]}
    elif args.operation=="status":
        result=runtime.status(args.job_id)
    else:
        if args.plan is None:
            parser.error("--plan required for trusted operator create")
        runtime.executor().create(args.job_id,json.loads(args.plan.read_text()))
        result={"id":args.job_id,"status":"prepared"}
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
