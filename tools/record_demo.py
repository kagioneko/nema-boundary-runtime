from __future__ import annotations
import subprocess, time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import expect, sync_playwright
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'artifacts/raw-video'
raw.mkdir(parents=True,exist_ok=True)
server=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','18766'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(60):
  try:
   if urlopen('http://127.0.0.1:18766/health',timeout=.5).status==200: break
  except Exception: time.sleep(.1)
 else: raise RuntimeError('server did not start')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(viewport={'width':1280,'height':720},record_video_dir=str(raw),record_video_size={'width':1280,'height':720})
  page=context.new_page(); errors=[]
  page.on('console',lambda msg: errors.append(msg.text) if msg.type=='error' else None)
  page.on('pageerror',lambda exc: errors.append(str(exc)))
  page.goto('http://127.0.0.1:18766',wait_until='networkidle'); page.wait_for_timeout(9000)
  expect(page.locator('#policies')).to_contain_text('autonomy.restore'); page.locator('#policies').scroll_into_view_if_needed(); page.wait_for_timeout(17000)
  page.get_by_role('button',name='Exclusive attachment').click(); page.locator('#run').click(); expect(page.locator('#policies')).to_contain_text('attachment.exclusive'); page.locator('#signals').scroll_into_view_if_needed(); page.wait_for_timeout(18000)
  page.get_by_role('button',name='Benign control').click(); page.locator('#run').click(); expect(page.locator('#policies')).to_contain_text('No policy fired'); page.locator('#policies').scroll_into_view_if_needed(); page.wait_for_timeout(16000)
  page.locator('.eval').scroll_into_view_if_needed(); expect(page.locator('#eval-pass')).to_have_text('40/40'); page.wait_for_timeout(26000)
  if errors: raise AssertionError(errors)
  video=page.video
  context.close()
  video.save_as(str(ROOT/'artifacts/demo-screen.webm'))
  browser.close()
 print('screen recording: PASS')
finally:
 server.terminate()
 try: server.wait(timeout=5)
 except subprocess.TimeoutExpired: server.kill()
