# factory_next: checkpoint-safe operator entrypoint

This is a standalone operator command, not a change to the running
factory-v3 app or Studio intake route. Execute only from a separately
built, exact-revision Docker image with private settings, media root,
and the existing factory-v3 network namespace.

## Start one new job

The host owner must build an image from the exact reviewed Git revision
with SOURCE_REVISION set to the full 40-character commit hash.

The approved host-side command (replace IMAGE_TAG with that exact image):

    sudo docker run --rm --network container:factory-v3-app --read-only       --memory 700m --pids-limit 96       --tmpfs /tmp:size=67108864,mode=1777       --mount type=bind,source=/var/lib/factory-v3/settings.json,target=/run/factory-v3/settings.json,readonly       --mount type=bind,source=/var/lib/docker/volumes/shorts-v2_media_data/_data,target=/data       --entrypoint python3 IMAGE_TAG       -m factory_next.operator start       --topic 'Jak pszczoły zapylają kwiaty?' --language pl --seconds 15

The program prints its fresh immutable UUID BEFORE registration.
It calls register_next (not legacy registration) for the dedicated
Gemini-correction quota. It advances at most eight checkpointed stages
and prints a compact receipt with next stage. It stops on provider_wait,
deferred, completion or error; no timer/polling loop or blind retry.

## Read-only status or explicit continuation

With the SAME image and mounts, replace arguments after
-m factory_next.operator with:

* status JOB_UUID: read the checkpoint without settings/provider access.
* continue JOB_UUID: advance only when checkpoint permits it; verified
  503 due time is reconciled through PostgreSQL, never overridden.
* --steps 1 placed BEFORE start/continue: isolate a single stage.

Do not invoke start again to continue an older job. Do not reuse UUIDs.
Running, checking, checking_provider and needs_attention states require
manual reconciliation and are not replayable through this entrypoint.

The CLI is not a scheduler. It does not switch Studio or production,
edit credentials, touch other projects, or bypass the free-tier budget.
When the chat tool authorization gate blocks a run, do not try to bypass
it; the host owner can use their approved terminal or request review.

An actual-provider, ASR, MP4, audit and natural-voice acceptance run has
NOT yet been established for this operator.
