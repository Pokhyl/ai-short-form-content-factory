"""Check Studio in isolated Chrome; default is read-only, submission is explicit and recorded."""
import argparse,json,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default='https://studio.hodor.com.pl')
parser.add_argument('--receipt',required=True)
parser.add_argument('--chrome-executable')
parser.add_argument('--submit-topic')
parser.add_argument('--language',choices=['en','pl','ru','uk'],default='uk')
parser.add_argument('--duration',type=int,choices=[15,30,45,60],default=45)
args=parser.parse_args();target=Path(args.receipt)
if target.exists():raise SystemExit('Receipt exists; inspect it instead of replaying a submission')
target.parent.mkdir(parents=True,exist_ok=True)
receipt={'page_errors':[],'authenticated':False,'submission_attempted':False,'passed':False}
def save():target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
save()
try:
 with sync_playwright() as pw:
  options={'headless':True}
  if args.chrome_executable:options['executable_path']=args.chrome_executable
  else:options['channel']='chrome'
  browser=pw.chromium.launch(**options)
  context=browser.new_context(viewport={'width':1440,'height':1000})
  page=context.new_page();page.on('pageerror',lambda error:receipt['page_errors'].append(str(error)))
  response=page.goto(args.base_url,wait_until='networkidle');assert response.status==200,response.status
  page.wait_for_selector('#new input[name="topic"]')
  page.wait_for_function('document.querySelector("#new button").disabled===false',timeout=30000)
  page.wait_for_function('document.querySelector("#jobs").textContent.trim().length>0')
  assert page.locator('article:not([data-origin="user"])').count()==0
  receipt['default_user_only']=True;page.screenshot(path=str(target.with_name(target.stem+'-user.png')))
  page.select_option('#historyView','examples');page.wait_for_selector('article[data-origin="test"][data-state="ready"] video')
  assert page.locator('article:not([data-state="ready"])').count()==0
  receipt['ready_examples']=page.locator('article').count()
  video=page.locator('video').first;video.scroll_into_view_if_needed()
  page.evaluate('async()=>{window.qaVideo=document.querySelector("video");qaVideo.muted=true;await qaVideo.play()}')
  page.wait_for_timeout(5200)
  before=video.evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,error:v.error&&v.error.message})')
  page.evaluate('async()=>{await draw()}');page.wait_for_timeout(1200)
  after=page.evaluate('()=>({same:qaVideo===document.querySelector("video"),time:qaVideo.currentTime,width:qaVideo.videoWidth})')
  assert before['time']>4 and before['width']==1080 and after['same'] and after['time']>before['time'] and not before['error'],(before,after)
  receipt['continuous_playback']={'before':before,'after_refresh':after};video.evaluate('(v)=>v.pause()')
  page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)')
  receipt['mobile_dimensions']=page.evaluate('()=>({viewport:innerWidth,content:document.documentElement.scrollWidth})')
  assert receipt['mobile_dimensions']['content']<=391,receipt['mobile_dimensions']
  page.screenshot(path=str(target.with_name(target.stem+'-mobile.png')))
  page.set_viewport_size({'width':1440,'height':1000});page.select_option('#historyView','tests')
  page.wait_for_selector('article');receipt['diagnostics_accessible']=True
  page.select_option('#historyView','user');page.wait_for_function('!document.querySelector("article:not([data-origin=user])")')
  if args.submit_topic:
   page.fill('input[name="topic"]',args.submit_topic);page.select_option('[name="language"]',args.language);page.select_option('[name="duration_s"]',str(args.duration))
   receipt['submission_attempted']=True;receipt['submission_started_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt['request']={'topic':args.submit_topic,'language':args.language,'duration_s':args.duration};save()
   with page.expect_response(lambda response:response.request.method=='POST' and response.url.endswith('/api/jobs')) as pending:
    page.click('#new button')
   result=pending.value;data=result.json();receipt['submission_http_status']=result.status;receipt['submitted_job']=data.get('id');save();assert result.status==202,data
   page.wait_for_function('document.querySelector("#new button").disabled===false')
   assert page.input_value('[name="language"]')==args.language and page.input_value('[name="duration_s"]')==str(args.duration)
   receipt['form_keeps_language_duration']=True
  assert not receipt['page_errors'],receipt['page_errors']
  receipt['passed']=True;browser.close()
finally:
 save();print(json.dumps(receipt,ensure_ascii=False),flush=True)
