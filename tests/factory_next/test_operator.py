"""Operator CLI contract; no network, credentials or provider calls."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from factory_next.operator import progress,run,main
from factory_next.pipeline import Pipeline,PreDispatchUnavailable,ReconciliationRequired


REV='c'*40


class OfflineAdapter:
    def __init__(self):
        self.sends=0
    def research(self,context):
        self.sends+=1
        return {'fixture':'read-only and source verified'}


class OfflineDeferral:
    def __init__(self):
        self.sends=0
    def research(self,context):
        self.sends+=1
        raise AssertionError('deferred provider stage must not be sent')


class OperatorTests(unittest.TestCase):
    def test_progress_only_one_stage_when_capped(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter=OfflineAdapter()
            pipeline=Pipeline(directory,adapter,REV)
            job=str(uuid4())
            pipeline.create(job,'Offline subject','pl',15)
            state=progress(pipeline,job,max_steps=1)
            self.assertEqual(state['next_stage'],'materials')
            self.assertEqual(adapter.sends,1)

    def test_deferred_not_due_cannot_send_or_reconcile(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter=OfflineDeferral()
            pipeline=Pipeline(directory,adapter,REV,clock=lambda:100)
            job=str(uuid4())
            pipeline.create(job,'Controlled topic','pl',15)
            state=pipeline.snapshot(job)
            state['status']='provider_wait'
            state['provider_wait_receipt']={
                'protocol':'budgeted-explicit-503',
                'stage':'research','retry_at':'2999-01-01T00:00:00+00:00'}
            pipeline.save(pipeline.directory(job),state)
            result=progress(pipeline,job)
            self.assertEqual(result['status'],'provider_wait')
            self.assertEqual(adapter.sends,0)

    def test_running_or_failed_checkpoint_never_dispatches(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter=OfflineAdapter()
            pipeline=Pipeline(directory,adapter,REV)
            job=str(uuid4())
            pipeline.create(job,'Controlled topic','pl',15)
            state=pipeline.snapshot(job)
            for status in ('running','checking','needs_attention','checking_provider'):
                state['status']=status
                pipeline.save(pipeline.directory(job),state)
                with self.subTest(status=status),self.assertRaisesRegex(ValueError,'manual reconciliation'):
                    progress(pipeline,job)
            self.assertEqual(adapter.sends,0)

    def test_start_creates_new_identity_and_one_stage_only(self):
        with tempfile.TemporaryDirectory() as directory:
            settings=Path(directory)/'settings.json'
            settings.write_text('{}')
            settings.chmod(0o600)
            seen=[]
            adapter=OfflineAdapter()
            def register(runtime,job,topic,language,seconds):
                seen.append((job,topic,language,seconds))
                return {'created':True}
            with patch.dict(os.environ,{'FACTORY_V3_REVISION':REV}),                 patch('factory_next.operator.Runtime',return_value=object()),                 patch('factory_next.operator.connected_adapters',return_value=adapter),                 patch('factory_next.operator.register_next',side_effect=register):
                output=StringIO()
                with redirect_stdout(output):
                    returned=run(['--data-root',directory,'--settings',str(settings),
                                  '--steps','1','start','--topic','Pollination',
                                  '--language','pl','--seconds','15'])
            self.assertEqual(returned,0)
            messages=[json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(messages[0]['action'],'registration_start')
            job=messages[0]['new_job_id']
            self.assertEqual(messages[1]['job_id'],job)
            self.assertEqual(messages[1]['next_stage'],'materials')
            self.assertEqual(seen,[(job,'Pollination','pl',15)])
            self.assertEqual(adapter.sends,1)
            state=Pipeline(Path(directory)/'factory-next-states',None,REV).snapshot(job)
            self.assertEqual(state['revision'],REV)

    def test_status_requires_no_runtime_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            job=str(uuid4())
            pipeline=Pipeline(Path(directory)/'factory-next-states',None,REV)
            pipeline.create(job,'Photo topic','en',30)
            with patch.dict(os.environ,{'FACTORY_V3_REVISION':REV}),                 patch('factory_next.operator.load_settings',side_effect=AssertionError('must not read secrets')):
                output=StringIO()
                with redirect_stdout(output):
                    returned=run(['--data-root',directory,'status',job])
            self.assertEqual(returned,0)
            self.assertEqual(json.loads(output.getvalue())['next_stage'],'research')

    def test_help_exits_successfully_without_false_error(self):
        with patch('sys.argv',['factory_next.operator','--help']):
            output=StringIO();errors=StringIO()
            with redirect_stdout(output),redirect_stderr(errors):
                with self.assertRaises(SystemExit) as finished:
                    main()
        self.assertEqual(finished.exception.code,0)
        self.assertIn('start',output.getvalue())
        self.assertEqual(errors.getvalue(),'')

    def test_revision_mismatch_or_bad_arguments_rejected_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            job=str(uuid4())
            Pipeline(Path(directory)/'factory-next-states',None,REV).create(job,'Subject','pl',15)
            with patch.dict(os.environ,{'FACTORY_V3_REVISION':'d'*40}),                 patch('factory_next.operator.load_settings',return_value={}):
                with patch('factory_next.operator.Runtime',return_value=object()),                     patch('factory_next.operator.connected_adapters',return_value=OfflineAdapter()):
                    with self.assertRaisesRegex(ValueError,'revision mismatch'):
                        run(['--data-root',directory,'continue',job])
            with patch.dict(os.environ,{'FACTORY_V3_REVISION':REV}):
                with self.assertRaises(SystemExit):
                    run(['--data-root',directory,'--steps','9','status',job])


if __name__=='__main__':unittest.main()
