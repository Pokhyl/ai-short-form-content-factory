# Dated browser regression. Default is read-only; --submit creates one UK/45 galaxy job.
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('/data/factory-universal/qa');out.mkdir(exist_ok=True)
settings=json.load(open('/run/secrets/n8n-project-settings.json'))
receipt={'page_errors':[]}
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage'])
  context=browser.new_context(http_credentials={'username':settings['STUDIO_AUTH_USERNAME'],'password':settings['STUDIO_AUTH_PASSWORD']},viewport={'width':1440,'height':1000})
  page=context.new_page();page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)))
  page.goto('https://studio.hodor.com.pl/',wait_until='networkidle')
  page.wait_for_selector('article[data-origin="user"]')
  assert page.locator('article[data-origin="test"]').count()==0
  assert page.locator('article[data-job-id="4a747543-e99e-487b-83d6-89019a610843"][data-state="failed"]').count()==1
  receipt['default_user_only']=True;page.screenshot(path=str(out/'user-view.png'))
  page.select_option('#historyView','examples');page.wait_for_selector('article[data-origin="test"][data-state="ready"]')
  assert page.locator('article:not([data-state="ready"])').count()==0
  receipt['ready_examples']=page.locator('article').count()
  video=page.locator('video').first;video.scroll_into_view_if_needed()
  page.evaluate('async()=>{window.qaVideo=document.querySelector("video");qaVideo.muted=true;await qaVideo.play()}')
  page.wait_for_timeout(5200)
  before=video.evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,error:v.error&&v.error.message})')
  page.evaluate('async()=>{await draw()}');page.wait_for_timeout(1200)
  after=page.evaluate('()=>({same:qaVideo===document.querySelector("video"),time:qaVideo.currentTime,width:qaVideo.videoWidth})')
  assert before['time']>4 and before['width']==1080 and after['same'] and after['time']>before['time'],(before,after)
  receipt['continuous_playback']={'before':before,'after_refresh':after}
  page.screenshot(path=str(out/'examples-playback.png'));video.evaluate('(v)=>v.pause()')
  page.select_option('#historyView','tests');page.wait_for_selector('article[data-state="failed"]');receipt['diagnostics_accessible']=True
  page.select_option('#historyView','user');page.wait_for_selector('article[data-origin="user"]')
  if '--submit' not in sys.argv:
   browser.close();raise SystemExit(0)
  page.fill('input[name="topic"]','Столкновение галактик');page.select_option('[name="language"]','uk');page.select_option('[name="duration_s"]','45')
  with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/jobs')) as response:
   page.click('#new button')
  r=response.value;data=r.json();assert r.status==202,data
  receipt['submitted_job']=data['id'];print('SUBMITTED',data['id'],flush=True)
  page.wait_for_function('document.querySelector("#new button").disabled===false')
  assert page.input_value('[name="language"]')=='uk' and page.input_value('[name="duration_s"]')=='45'
  receipt['form_keeps_language_duration']=True
  assert receipt['page_errors']==[],receipt['page_errors']
  browser.close()
finally:
 (out/'browser-regression.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps(receipt,ensure_ascii=False),flush=True)
