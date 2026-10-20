"""Real PostgreSQL regression for the six-attempt Gemini/SQL contract. No providers."""
import os
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb

conn=psycopg.connect(os.environ["V3_TEST_DATABASE_URL"],autocommit=True)
conn.execute("""CREATE SCHEMA factory_v3;
CREATE TABLE factory_v3.preparations(id uuid PRIMARY KEY,status text,source_revision text,budgets jsonb,frozen jsonb,request jsonb);
CREATE TABLE factory_v3.preparation_calls(preparation_id uuid,call_key text,kind text,state text,finished_at timestamptz,response jsonb);
CREATE TABLE factory_v3.preparation_runs(preparation_id uuid,source_revision text);""")
conn.execute(Path("/fixtures/preparation_deferrals.sql").read_text())
def check(failed,nxt,expected,*,state="failed",status=503,budget=16,unknown=False,revision="test",delay=900):
    conn.execute("BEGIN")
    try:
        job=uuid4()
        conn.execute("INSERT INTO factory_v3.preparations VALUES (%s,'preparing','test',%s,NULL,'{}')",(job,Jsonb({"gemini":budget})))
        conn.execute("INSERT INTO factory_v3.preparation_calls VALUES (%s,%s,'gemini',%s,now(),%s)",
          (job,failed,state,Jsonb({"status":status,"error_status":"UNAVAILABLE","gateway_execution_id":"123"})))
        if unknown:
            conn.execute("INSERT INTO factory_v3.preparation_calls VALUES (%s,'unresolved','gemini','unknown',NULL,NULL)",(job,))
        try:
            result=conn.execute("SELECT factory_v3.defer_preparation_call(%s,%s,%s,%s,%s)",(job,failed,nxt,delay,revision)).fetchone()[0]
        except psycopg.errors.RaiseException:
            if expected: raise
        else:
            assert expected, (failed,nxt,"unexpected acceptance")
            assert result["deferred"] is True, result
            assert conn.execute("SELECT retry_call_key FROM factory_v3.preparation_deferrals").fetchone()[0]==nxt
    finally: conn.execute("ROLLBACK")

for ordinal in range(1,6):
    failed="research" if ordinal==1 else "research:availability:"+str(ordinal)
    check(failed,"research:availability:"+str(ordinal+1),True)
for failed,nxt in [("research:availability:6","research:availability:7"),
 ("research","research:availability:3"),
 ("research:availability:3","other:availability:4"),
 ("research:availability:3","research:availability:5"),
 ("research:availability:0","research:availability:1")]:
    check(failed,nxt,False)
for kwargs in [dict(state="unknown"),dict(status=429),dict(budget=1),dict(unknown=True),
               dict(revision="wrong"),dict(delay=59),dict(delay=1801)]:
    check("research:availability:3","research:availability:4",False,**kwargs)
print("PASS: 5 allowed transitions, 5 invalid sequences, 7 safety/budget controls")
conn.close()
