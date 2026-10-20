"""Apply only the verified deferral function; abort on concurrent changes."""
import json, os, hashlib
from pathlib import Path
from factory_v3.runtime import Runtime,load_settings
runtime=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
old=Path('/tmp/deferral-before.sql').read_text()
new=Path('/tmp/deferral-after.sql').read_text()
def body(sql): return sql.split('AS $$',1)[1].split('$$;',1)[0]
definition=new[new.index('CREATE OR REPLACE FUNCTION factory_v3.defer_preparation_call'):].split('$$;',1)[0]+'$$;'
for path in Path('/data/factory-next-states').glob('*/state.json'):
    state=json.loads(path.read_text())
    if state.get('status') in ('running','provider_wait'):
        raise RuntimeError('active or waiting Studio job; deployment postponed')
with runtime.ledger.psycopg.connect(runtime.ledger.dsn,connect_timeout=5,options='-c statement_timeout=5000') as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT prosrc FROM pg_proc WHERE oid='factory_v3.defer_preparation_call(uuid,text,text,integer,text)'::regprocedure")
        actual=cur.fetchone()[0]
        assert actual==body(old), 'Concurrent migration detected; no change applied'
        def snapshot():
            result={}
            for table in ('preparations','preparation_calls','preparation_deferrals','preparation_runs'):
                cur.execute('SELECT count(*) FROM factory_v3.'+table)
                result[table]=cur.fetchone()[0]
            return result
        before=snapshot()
        cur.execute(definition)
        cur.execute("SELECT prosrc FROM pg_proc WHERE oid='factory_v3.defer_preparation_call(uuid,text,text,integer,text)'::regprocedure")
        assert cur.fetchone()[0]==body(new), 'Function body mismatch'
        assert snapshot()==before, 'Concurrent table change'
print(json.dumps({'deployed':True,'function':'factory_v3.defer_preparation_call','body_sha256':hashlib.sha256(body(new).encode()).hexdigest(),'unchanged_row_counts':before,'provider_calls':0,'jobs_replayed':0}))
