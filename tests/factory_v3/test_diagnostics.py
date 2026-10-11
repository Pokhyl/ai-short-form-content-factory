import unittest

from factory_v3.diagnostics import refresh_preparation_progress


class ScalarReturningLedger:
    def __init__(self, voice_revision_count):
        self.voice_revision_count = voice_revision_count

    def _call(self, sql, parameters):
        if "preparation_calls" in sql:
            return {"gemini": 2, "metadata": 1}
        if "voice_revisions" in sql:
            # PostgresLedger._call returns row[0], so COUNT(*) is an int.
            return self.voice_revision_count
        if "stage_runs" in sql:
            return {"stage": "voice", "state": "running", "error_code": None}
        raise AssertionError("unexpected query")

    def snapshot(self, preparation_id):
        return {"status": "unknown"}


class DiagnosticsTests(unittest.TestCase):
    def test_progress_handles_scalar_count_returned_by_postgres_ledger(self):
        progress = refresh_preparation_progress(ScalarReturningLedger(1), "test-id")
        self.assertEqual(progress, {
            "tts_sends": 1,
            "gemini_calls": 2,
            "metadata_calls": 1,
            "job_status": "unknown",
            "latest_stage": {"stage": "voice", "state": "running", "error_code": None},
        })

    def test_empty_scalar_count_means_no_voice_sends(self):
        progress = refresh_preparation_progress(ScalarReturningLedger(0), "test-id")
        self.assertEqual(progress["tts_sends"], 0)


if __name__ == "__main__":
    unittest.main()
