import http.client,json,os,shutil,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from factory_v3.deletion import MEDIA_DIRECTORIES,remove_media,ensure_visible,marker,deleted_ids
from factory_v3.server import Application,handler
from factory_v3.runtime import Runtime as ProductionRuntime
from test_server import Runtime,JOB,ORIGIN,OWNER
from http.server import ThreadingHTTPServer
OTHER='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'

class DeletionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.runtime=Runtime(self.root);self.app=Application(self.runtime,ORIGIN)
        self.app.pool.shutdown();self.app.pool=Mock()
        for category in MEDIA_DIRECTORIES:
            for identity in (JOB,OTHER):
                path=self.root/category/identity;path.mkdir(parents=True);(path/'media.bin').write_bytes(b'owned media')
    def tearDown(self):self.temp.cleanup()
    def test_physical_removal_all_owned_media_and_no_reuse_or_old_links(self):
        shared=self.root/'visuals'/OTHER/'linked.jpg'
        os.link(self.root/'catalog'/JOB/'media.bin',shared)
        self.assertTrue(self.app.delete(JOB,{'delete':True})['deleted'])
        for category in MEDIA_DIRECTORIES:
            self.assertFalse((self.root/category/JOB).exists())
            self.assertTrue((self.root/category/OTHER/'media.bin').exists())
        self.assertEqual(shared.read_bytes(),b'owned media')
        self.assertEqual(deleted_ids(self.root),[JOB])
        self.assertEqual(self.app.delete(JOB,{'delete':True}),{'id':JOB,'deleted':True})
        for operation in (lambda:self.app.video(JOB),lambda:self.app.detail(JOB),lambda:self.app.photo(JOB,'photo-1'),lambda:self.app.submit({'request_id':JOB,'topic':'x','language':'ru','seconds':30})):
            with self.assertRaises(KeyError):operation()
        # Production admission must reject a deleted UUID before DB/provider use.
        runtime=object.__new__(ProductionRuntime);runtime.root=self.root
        with self.assertRaises(KeyError):runtime.create(JOB,'x','ru',30)
        self.app.pool.submit.assert_not_called()
    def test_active_or_nonexplicit_deletion_keeps_files(self):
        for status in ('preparing','prepared','voice_running','voice_ready','render_ready'):
            self.runtime.ledger.state['status']=status
            with self.assertRaises(ValueError):self.app.delete(JOB,{'delete':True})
        self.runtime.ledger.state['status']='qa_pass'
        for data in ({},{'delete':False},{'delete':1},{'delete':True,'all':True}):
            with self.assertRaises(ValueError):self.app.delete(JOB,data)
        self.assertFalse(marker(self.root,JOB).exists())
        self.assertTrue((self.root/'renders'/JOB/'media.bin').exists())
    def test_partial_removal_is_hidden_and_explicit_retry_finishes(self):
        actual=shutil.rmtree
        def remove(path):
            if path.parent.name=='voiceovers':raise OSError('controlled interrupted deletion')
            return actual(path)
        with patch('factory_v3.deletion.shutil.rmtree',side_effect=remove):
            with self.assertRaises(OSError):self.app.delete(JOB,{'delete':True})
        self.assertEqual(json.loads(marker(self.root,JOB).read_text())['state'],'deleting')
        with self.assertRaises(KeyError):ensure_visible(self.root,JOB)
        self.app.delete(JOB,{'delete':True})
        self.assertFalse((self.root/'voiceovers'/JOB).exists())
    def test_symlink_and_invalid_uuid_never_remove_other_media(self):
        folder=self.root/'renders'/JOB;shutil.rmtree(folder);folder.symlink_to(self.root/'renders'/OTHER,target_is_directory=True)
        with self.assertRaises(ValueError):self.app.delete(JOB,{'delete':True})
        self.assertTrue((self.root/'renders'/OTHER/'media.bin').exists())
        with self.assertRaises(ValueError):remove_media(self.root,'../renders')
    def test_authenticated_download_attachment_ranges_and_deleted_route(self):
        import hashlib
        final=self.root/'renders'/JOB/'final.mp4';final.write_bytes(b'controlled-video-bytes')
        sha=hashlib.sha256(final.read_bytes()).hexdigest()
        self.runtime.ledger.state['outputs']={'render':{'sha256':sha},'qa':{'sha256':sha}}
        server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.app));thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.05),daemon=True);thread.start()
        cookie='factory_v3_session='+self.app.sessions.issue()
        def send(method,path,data=None,auth=True,origin=ORIGIN,range=None):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            headers={'Origin':origin,'Content-Type':'application/json'}
            if auth:headers['Cookie']=cookie
            if range:headers['Range']=range
            try:
                conn.request(method,'/factory-v3'+path,json.dumps(data) if data is not None else None,headers)
                response=conn.getresponse();return response.status,dict(response.getheaders()),response.read()
            finally:conn.close()
        try:
            self.assertEqual(send('POST','/api/requests/'+JOB+'/delete',{'delete':True},auth=False)[0],401)
            self.assertEqual(send('POST','/api/requests/'+JOB+'/delete',{'delete':True},origin='https://other.invalid')[0],403)
            code,headers,raw=send('GET','/video/'+JOB+'?download=1',range='bytes=0-9')
            self.assertEqual(code,206);self.assertEqual(raw,final.read_bytes()[:10]);self.assertIn('attachment',headers['Content-Disposition'])
            self.assertEqual(send('POST','/api/requests/'+JOB+'/delete',{'delete':True})[0],200)
            self.assertFalse(final.exists())
            self.assertEqual(send('GET','/video/'+JOB)[0],404)
            self.assertEqual(send('GET','/api/requests/'+JOB)[0],404)
        finally:server.shutdown();server.server_close();thread.join(timeout=2)
