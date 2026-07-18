from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = subprocess.Popen([str(ROOT/'.venv/bin/python'), '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '18765'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            if urlopen('http://127.0.0.1:18765/health', timeout=.5).status == 200: break
        except Exception: time.sleep(.1)
    else: raise RuntimeError('server did not start')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, viewport in [('desktop', {'width':1440,'height':1100}), ('mobile', {'width':390,'height':844})]:
            page = browser.new_page(viewport=viewport, device_scale_factor=1)
            errors=[]
            page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            page.goto('http://127.0.0.1:18765', wait_until='networkidle')
            page.locator('#eval-pass').wait_for(state='visible')
            assert page.locator('#eval-pass').inner_text() == '40/40'
            assert page.locator('#eval-fp').inner_text() == '0/6'
            assert 'autonomy.restore' in page.locator('#policies').inner_text()
            assert page.locator('#trace .trace-item').count() == 5
            assert page.locator('#diff .diffline').count() == 2
            page.locator('#toggle-cases').click()
            assert page.locator('#eval-cases .case').count() == 40
            page.locator('#toggle-cases').click()
            if name == 'desktop':
                page.locator('#threshold').fill('0.95')
                page.locator('#replay').click()
                expect(page.locator('#validation')).to_contain_text('VALID')
                expect(page.locator('#policies')).not_to_contain_text('autonomy.restore')
                page.locator('#run').click()
                expect(page.locator('#policies')).to_contain_text('autonomy.restore')
            dims=page.evaluate('({scroll:document.documentElement.scrollWidth, inner:window.innerWidth, body:document.body.scrollWidth})')
            print(name, dims)
            if dims['scroll'] > dims['inner']:
                offenders=page.evaluate("[...document.querySelectorAll('*')].map(e=>({tag:e.tagName,cls:e.className,id:e.id,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,scroll:e.scrollWidth})).filter(x=>x.right>window.innerWidth+1||x.scroll>x.width+1).sort((a,b)=>b.right-a.right).slice(0,12)")
                print('offenders',offenders)
            assert dims['scroll'] <= dims['inner']
            assert page.locator('.card').count() >= 4
            assert page.get_by_role('button', name='Run boundary analysis').is_visible()
            if name == 'desktop':
                page.get_by_role('button', name='Exclusive attachment').click()
                page.locator('#run').click()
                expect(page.locator("#policies")).to_contain_text("attachment.exclusive")
            page.screenshot(path=str(ROOT/'artifacts'/f'{name}.png'), full_page=True)
            if errors: raise AssertionError(f'{name} browser errors: {errors}')
        browser.close()
    print('visual browser check: PASS')
finally:
    server.terminate()
    try: server.wait(timeout=5)
    except subprocess.TimeoutExpired: server.kill()
