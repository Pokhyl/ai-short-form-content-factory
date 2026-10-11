"""Read-only helpers for bounded production diagnostics."""


def refresh_preparation_progress(ledger, preparation_id):
    """Return durable counters using PostgresLedger._call scalar semantics."""
    calls = ledger._call(
        "SELECT COALESCE(jsonb_object_agg(kind,n),'{}'::jsonb) FROM "
        "(SELECT kind,count(*) AS n FROM factory_v3.preparation_calls "
        "WHERE preparation_id=%s::uuid GROUP BY kind) counts", (preparation_id,))
    voice_revisions = ledger._call(
        "SELECT count(*) FROM factory_v3.voice_revisions "
        "WHERE job_id=%s::uuid", (preparation_id,))
    latest_stage = ledger._call(
        "SELECT jsonb_build_object('stage',stage,'state',state,'error_code',error_code) "
        "FROM factory_v3.stage_runs WHERE job_id=%s::uuid "
        "ORDER BY started_at DESC LIMIT 1", (preparation_id,))
    job = ledger.snapshot(preparation_id)
    return {
        "tts_sends": voice_revisions or 0,
        "gemini_calls": (calls or {}).get("gemini", 0),
        "metadata_calls": (calls or {}).get("metadata", 0),
        "job_status": job["status"],
        "latest_stage": latest_stage,
    }
