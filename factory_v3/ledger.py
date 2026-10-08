"""PostgreSQL ledger; no persistent SQLite production fallback."""
import json


class PostgresLedger:
    def __init__(self, dsn):
        import psycopg
        self.psycopg = psycopg
        self.dsn = dsn

    def _call(self, sql, parameters):
        with self.psycopg.connect(self.dsn, connect_timeout=5,
                                 options="-c statement_timeout=5000") as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
                row = cursor.fetchone()
                return row[0] if row else None

    def create(self, job_id, frozen):
        return self._call("SELECT factory_v3.create_job(%s::uuid,%s::jsonb)",
                          (job_id, json.dumps(frozen)))

    def snapshot(self, job_id):
        result = self._call("""
          SELECT jsonb_build_object('id',j.id,'status',j.status,'frozen',j.frozen,
            'outputs',COALESCE((SELECT jsonb_object_agg(stage,output)
              FROM factory_v3.stage_runs WHERE job_id=j.id AND state='succeeded'),'{}'::jsonb))
          FROM factory_v3.jobs j WHERE id=%s::uuid""", (job_id,))
        if result is None:
            raise KeyError("job not found")
        return result

    def claim(self, job_id, stage, plan_hash):
        return self._call("SELECT factory_v3.claim_stage(%s::uuid,%s,%s)",
                          (job_id, stage, plan_hash))

    def account_voice_attempt(self, job_id):
        self._call("SELECT factory_v3.account_voice_attempt(%s::uuid)", (job_id,))

    def account_voice_revision(self, job_id, attempt, frozen):
        self._call("SELECT factory_v3.account_voice_revision(%s::uuid,%s,%s::jsonb)",
                   (job_id,attempt,json.dumps(frozen)))

    def measure_voice_revision(self, job_id, attempt, result):
        self._call("SELECT factory_v3.measure_voice_revision(%s::uuid,%s,%s::jsonb)",
                   (job_id,attempt,json.dumps(result)))

    def finish(self, job_id, stage, output):
        self._call("SELECT factory_v3.finish_stage(%s::uuid,%s,%s::jsonb)",
                   (job_id, stage, json.dumps(output)))

    def fail(self, job_id, stage, code, unknown):
        self._call("SELECT factory_v3.fail_stage(%s::uuid,%s,%s,%s)",
                   (job_id, stage, code, unknown))
