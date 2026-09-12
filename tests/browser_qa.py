"""Fresh Chromium evidence, exclusively loopback + synthetic form data."""
import argparse
import base64
import hashlib
import io
import json
import re
import time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='http://127.0.0.1:8765'
def revision():
    files=sorted((ROOT/'site').rglob('*'))
    return hashlib.sha256('\n'.join(f'{f.relative_to(ROOT/"site").as_posix()}:{hashlib.sha256(f.read_bytes()).hexdigest()}' for f in files if f.is_file()).encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r2');parser.add_argument('--skip-matrix',action='store_true');args=parser.parse_args()
    dest=ROOT/'screenshots'/args.revision;dest.mkdir(parents=True,exist_ok=True)
    report={'revision':revision(),'started':time.time(),'screens':[],'checks':[],'errors':[],'console':[],'external_requests':[]}
    def check(name,value,detail=None):
        report['checks'].append({'name':name,'pass':bool(value),'detail':detail})
        if not value:report['errors'].append({'name':name,'detail':detail});print('FAIL',name,detail,flush=True)
        (ROOT/'qa'/f'browser-{args.revision}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    routes=json.loads((ROOT/'generation_reports/routes.json').read_text())
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
        context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(ORIGIN) else (report['external_requests'].append(route.request.url),route.abort())[1])
        page=context.new_page();page.on('pageerror',lambda err:report['console'].append(str(err)))
        def goto(route):
            response=page.goto(ORIGIN+route,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(120);return response
        def capture(name,full=False):
            file=dest/(name+'.png');page.screenshot(path=str(file),full_page=full,animations='disabled');return str(file.relative_to(ROOT))
        if not args.skip_matrix:
            for width in [1440,1024,768,390,360]:
                page.set_viewport_size({'width':width,'height':1000 if width>768 else 844})
                for route in routes:
                    response=goto(route);slug=route.strip('/').replace('/','-') or 'home'
                    check(f'{width}:{route}:status',response.status==200,response.status)
                    geometry=page.evaluate('''()=>({w:innerWidth,scroll:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,header:document.querySelector('header').getBoundingClientRect().top,buttons:[...document.querySelectorAll('.button')].filter(x=>x.getClientRects().length).map(x=>({label:x.innerText,width:x.clientWidth,scroll:x.scrollWidth,height:x.getBoundingClientRect().height}))})''')
                    check(f'{width}:{route}:overflow',geometry['scroll']<=width+1,geometry)
                    check(f'{width}:{route}:heading',geometry['h1']==1)
                    check(f'{width}:{route}:cta_geometry',all(b['scroll']<=b['width']+2 and b['height']>=44 for b in geometry['buttons']))
                    if route in ['/','/en']:
                        first=page.locator('.product-card').first.bounding_box();second=page.locator('.product-card').nth(1).bounding_box()
                        check(f'{width}:{route}:catalog_first',first['y']<700 and (width>600 or second['x']<width),{'first':first,'second':second})
                    viewport=capture(f'{slug}-{width}-viewport');full=capture(f'{slug}-{width}-full',True)
                    page.evaluate('scrollTo({top:document.body.scrollHeight,behavior:"instant"})');page.wait_for_timeout(50)
                    check(f'{width}:{route}:sticky_header',abs(page.locator('.header').bounding_box()['y'])<=1)
                    if width in [360,390]:capture(f'{slug}-{width}-footer')
                    report['screens'].append({'route':route,'width':width,'viewport':viewport,'full':full})
                print('Captured width',width,flush=True)
        for width in [1024,768,390,360]:
            page.set_viewport_size({'width':width,'height':844});goto('/');page.locator('.product-track').focus();page.keyboard.press('End');page.wait_for_timeout(800);check(f'{width}:catalog_end_settled',page.locator('.position').inner_text()=='4 / 4');page.locator('.next').click();page.wait_for_timeout(800);check(f'{width}:catalog_wrap_after_end',page.locator('.position').inner_text()=='1 / 4')
            for expected in [2,3,4,1]:
                page.locator('.next').click();page.wait_for_timeout(700);check(f'{width}:catalog_next_{expected}',page.locator('.position').inner_text()==f'{expected} / 4')
            check(f'{width}:brand_target',page.locator('.header .brand').bounding_box()['height']>=44)
        page.set_viewport_size({'width':390,'height':844});goto('/')
        page.evaluate('scrollTo({top:900,behavior:"instant"})');page.wait_for_timeout(100);before=page.evaluate('scrollY')
        box=page.locator('.menu-toggle').bounding_box();before=page.evaluate('scrollY');page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);check('menu_opens',page.locator('#mobile-menu').evaluate('(e)=>e.open'))
        capture('menu-open-390');page.keyboard.press('Shift+Tab');check('menu_focus_trap',page.evaluate('document.querySelector("#mobile-menu").contains(document.activeElement)'))
        page.keyboard.press('Escape');check('menu_escape_restore',abs(page.evaluate('scrollY')-before)<3);check('menu_focus_return',page.locator('.menu-toggle').evaluate('(e)=>e===document.activeElement'))
        page.locator('.menu-toggle').click();page.set_viewport_size({'width':1440,'height':1000});check('menu_resize_closes',not page.locator('#mobile-menu').evaluate('(e)=>e.open'))
        page.set_viewport_size({'width':360,'height':844});goto('/');page.locator('.menu-toggle').click();page.locator('#mobile-menu a').last.scroll_into_view_if_needed();capture('menu-last-360');check('menu_last_reachable',page.locator('#mobile-menu a').last.is_visible());page.keyboard.press('Escape')
        goto('/');track=page.locator('.product-track');track.focus();page.keyboard.press('End');page.wait_for_timeout(400);check('catalog_end',page.locator('.position').inner_text()=='4 / 4');page.locator('.next').click();page.wait_for_timeout(400);check('catalog_loop',page.locator('.position').inner_text()=='1 / 4');page.locator('.next').click();page.wait_for_timeout(400)
        page.locator('[data-product="counter-stand"] .details-link').click();check('correct_product_deep_link','/solutions/counter-stand' in page.url)
        page.go_back(wait_until='domcontentloaded');page.wait_for_timeout(400);check('catalog_restore',page.locator('.position').inner_text()=='2 / 4')
        # Touch gestures through real Chromium DevTools input, preserving native vertical scroll.
        touch=context.new_cdp_session(page);goto('/');box=track.bounding_box()
        y=min(box['y']+90,700);touch.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':280,'y':y}]})
        for x in [240,180,100,45]:touch.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y}]});page.wait_for_timeout(30)
        touch.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(500)
        check('native_touch_swipe',track.evaluate('(e)=>e.scrollLeft')>20)
        goto('/#faq-4');page.wait_for_timeout(250);faq_box=page.locator('#faq-4').bounding_box();check('faq_open_answer_in_viewport',faq_box['y']>=page.locator('.header').bounding_box()['height']-1 and faq_box['y']+faq_box['height']<=page.locator('.sticky-order').bounding_box()['y']);check('faq_deep_link',page.locator('#faq-4').evaluate('(e)=>e.open'));capture('faq-open-360');page.locator('#faq-4 summary').click();check('faq_toggle',not page.locator('#faq-4').evaluate('(e)=>e.open'))
        goto('/solutions/review-card');page.locator('[data-gallery="2"]').click();check('gallery_selection',page.locator('[data-gallery="2"]').get_attribute('aria-pressed')=='true');page.locator('[data-gallery="2"]').focus();page.keyboard.press('ArrowRight');check('gallery_keyboard',page.locator('[data-gallery="3"]').get_attribute('aria-pressed')=='true')
        page.locator('#product-quantity').fill('7');page.locator('.product-order button').click();page.wait_for_selector('form[data-enhanced=true]');check('product_quantity_preselected',page.locator('#f-product').input_value()=='review-card' and page.locator('#f-quantity').input_value()=='7')
        page.locator('#f-product').select_option('multi-location');check('network_fields_open',page.locator('.network-fields').is_visible());check('maps_visibly_required',page.locator('[data-maps-required]').is_visible());page.locator('#f-product').select_option('review-card');check('network_fields_disabled',page.locator('.network-fields input').first.is_disabled())
        page.locator('.submit-button').click();check('required_validation',page.locator('.error-summary').is_visible());page.wait_for_timeout(100);summary_box=page.locator('.error-summary').bounding_box();check('validation_summary_in_viewport',summary_box['y']>=page.locator('.header').bounding_box()['height'] and summary_box['y']+summary_box['height']<=page.locator('.sticky-order').bounding_box()['y']);capture('form-validation-360')
        def fill_form():
            page.locator('#f-name').fill('Тестова людина' if '/en/' not in page.url else 'Synthetic person');page.locator('#f-business').fill('NFC QA synthetic');page.locator('#f-city').fill('Test city');page.locator('#f-maps').fill('https://maps.app.goo.gl/TESTONLY');page.locator('#f-contact').fill('qa@example.test');page.locator('#f-consent').check()
        fill_form();page.locator('#f-quantity').fill('');page.locator('.submit-button').click();check('blank_quantity_error',page.locator('#e-quantity').is_visible());page.locator('#f-quantity').fill('7')
        page.reload(wait_until='domcontentloaded');page.wait_for_selector('form[data-enhanced=true]');check('draft_restored',page.locator('#f-name').input_value()=='Тестова людина');page.locator('#f-consent').check()
        raw=io.BytesIO();Image.new('RGB',(16,16),'white').save(raw,format='PNG');png=raw.getvalue()
        page.locator('#f-logo').set_input_files({'name':'qa-only.png','mimeType':'image/png','buffer':png});page.wait_for_function('document.querySelector(".upload-state").textContent.includes("qa-only.png")');capture('upload-focus-360')
        submitted=[];held=[];hold_first=True
        def error_route(route):
            submitted.append(route.request.post_data_json)
            if hold_first:held.append(route)
            else:route.fulfill(status=503,content_type='application/json',body='{"ok":false,"code":"synthetic_error"}')
        page.route('**/api/leads',error_route);page.locator('.submit-button').click();page.wait_for_timeout(150);check('pending_disables_duplicate_submit',page.locator('.submit-button').is_disabled() and page.locator('form').get_attribute('aria-busy')=='true');capture('form-pending-360');hold_first=False;held.pop().fulfill(status=503,content_type='application/json',body='{"ok":false,"code":"synthetic_error"}');page.wait_for_selector('.form-result[data-status=error]');page.wait_for_timeout(100);retry_box=page.locator('.form-result .button').bounding_box();check('retry_button_clear_of_sticky',retry_box['y']+retry_box['height']<=page.locator('.sticky-order').bounding_box()['y']);capture('form-error-360');check('error_preserves_fields',page.locator('#f-name').input_value()=='Тестова людина')
        page.reload(wait_until='domcontentloaded');page.wait_for_selector('form[data-enhanced=true]');page.locator('#f-consent').check();page.locator('.submit-button').click();page.wait_for_selector('.form-result[data-status=error]');check('reload_retry_keeps_logo_and_key',len(submitted)==2 and submitted[0]['idempotencyKey']==submitted[1]['idempotencyKey'] and submitted[0]['logo']==submitted[1]['logo'],{'submits':len(submitted),'same_key':len(submitted)==2 and submitted[0]['idempotencyKey']==submitted[1]['idempotencyKey']})
        page.unroute('**/api/leads',error_route)
        # Real API persistence in isolated local SQLite; mock notifier only.
        page.locator('.form-result .button').click();page.wait_for_selector('.form-result[data-status=success]',timeout=25000);capture('form-success-360');check('real_api_success',page.locator('.form-result').inner_text().find('Тестову заявку збережено локально')>=0)
        check('success_sticky_has_visible_destination',page.locator('.sticky-order .button').get_attribute('href')==ORIGIN+'/solutions')
        events=page.evaluate('window.nfcAnalyticsEvents');check('analytics_no_pii',all(set(e)<= {'event','locale','route','product','quantity'} for e in events),events)
        page.locator('.sticky-order .button').click();check('success_sticky_navigates_catalog',page.url==ORIGIN+'/solutions')
        # A malformed hash must not disable the form.
        goto('/order#%');page.wait_for_selector('form[data-enhanced=true]');check('malformed_hash_safe',page.locator('form').get_attribute('data-enhanced')=='true')
        # Browser URL language persistence and query preselection.
        goto('/order?product=team-kit&quantity=4');page.wait_for_selector('form[data-enhanced=true]');page.locator('.locale-switch').click();page.wait_for_selector('form[data-enhanced=true]');check('locale_equivalent_and_quantity','/en/order' in page.url and page.locator('#f-product').input_value()=='team-kit' and page.locator('#f-quantity').input_value()=='4');check('english_not_mixed',not re.search(r'[\u0400-\u04ff]',page.locator('body').inner_text()))
        # Default header entry has no product, while text draft is retained.
        page.set_viewport_size({'width':1440,'height':1000});goto('/solutions/team-kit');page.locator('.header-actions>.button').click();page.wait_for_selector('form[data-enhanced=true]');check('header_entry_unselected',page.locator('#f-product').input_value()=='')
        page.set_viewport_size({'width':360,'height':844});goto('/solutions/multi-location');page.locator('#product-quantity').fill('8');page.locator('.sticky-order .button').click();page.wait_for_selector('form[data-enhanced=true]');check('sticky_product_quantity_preserved',page.locator('#f-product').input_value()=='multi-location' and page.locator('#f-quantity').input_value()=='8')
        # Independent English contact flow and network order through the local API.
        goto('/en/contact');page.wait_for_selector('form[data-enhanced=true]');page.locator('#f-name').fill('Synthetic person');page.locator('#f-business').fill('NFC QA synthetic');page.locator('#f-topic').fill('Synthetic local question');page.locator('#f-message').fill('Synthetic message; no notification expected.');page.locator('#f-contact').fill('qa@example.test');page.locator('#f-consent').check();page.locator('.submit-button').click();page.wait_for_selector('.form-result[data-status=success]');check('english_contact_success',not re.search(r'[\u0400-\u04ff]',page.locator('body').inner_text()) and page.locator('.form-result dt').count()==2);capture('contact-success-en-360');check('english_success_sticky_localized',page.locator('.sticky-order .button').get_attribute('href')==ORIGIN+'/en/solutions')
        goto('/en/order?product=multi-location&quantity=8');page.wait_for_selector('form[data-enhanced=true]');fill_form();page.locator('#f-locations').fill('2');page.locator('#f-perLocation').fill('4');page.locator('#f-addresses').fill('Synthetic branch A\nSynthetic branch B');page.locator('#f-locationMaps').fill('https://maps.app.goo.gl/TESTA\nhttps://maps.app.goo.gl/TESTB');page.locator('#f-responsible').fill('qa@example.test');page.locator('.submit-button').click();page.wait_for_selector('.form-result[data-status=success]');check('english_network_order_success','Multi-Location' in page.locator('.form-result').inner_text());capture('network-success-en-360')
        # Hover, keyboard focus and active state evidence.
        page.set_viewport_size({'width':1440,'height':1000});goto('/');page.locator('.header-actions>.button').hover();capture('cta-hover-1440');page.locator('.header-actions>.button').focus();capture('cta-focus-1440');button_box=page.locator('.header-actions>.button').bounding_box();page.mouse.move(button_box['x']+15,button_box['y']+15);page.mouse.down();capture('cta-active-1440');page.mouse.move(1,1);page.mouse.up()
        page.set_viewport_size({'width':360,'height':844});goto('/order');page.wait_for_selector('form[data-enhanced=true]');page.locator('#f-comment').focus();page.wait_for_timeout(700);rect=page.locator('#f-comment').bounding_box();check('focused_field_clear_of_sticky',rect['y']+rect['height']<=page.locator('.sticky-order').bounding_box()['y']+1,rect);capture('field-focus-360')
        # Reduced motion, zoom reflow and no-JS reading/navigation.
        page.emulate_media(reduced_motion='reduce');goto('/');check('reduced_motion',page.locator('.button').first.evaluate('(e)=>parseFloat(getComputedStyle(e).transitionDuration)<.01'))
        page.set_viewport_size({'width':390,'height':844});page.locator('.menu-toggle').click();capture('menu-reduced-motion-390');page.keyboard.press('Escape')
        zoom=browser.new_context(viewport={'width':390,'height':844},bypass_csp=True);zp=zoom.new_page();zp.goto(ORIGIN+'/');zp.evaluate('document.fonts.ready');zp.add_style_tag(content='html{font-size:200%}');check('text_zoom_no_overflow',zp.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));check('text_zoom_actually_doubles',zp.locator('body').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')>=32);zp.screenshot(path=str(dest/'zoom-390.png'),animations='disabled');zoom.close()
        nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});np=nojs.new_page();np.goto(ORIGIN+'/');check('nojs_catalog_and_faq',np.locator('.product-card').count()==4 and np.locator('details').count()>=12);np.locator('#faq-1 summary').click();check('nojs_faq_opens',np.locator('#faq-1').get_attribute('open') is not None);np.locator('[data-product=review-card] .details-link').click();check('nojs_product_navigation','/solutions/review-card' in np.url);nojs.close()
        check('no_runtime_errors',len(report['console'])==0,report['console']);check('no_external_browser_requests',len(report['external_requests'])==0)
        browser.close()
    report['finished']=time.time();report['revision_after']=revision();check('unchanged_revision',report['revision']==report['revision_after'])
    (ROOT/'qa'/f'browser-{args.revision}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'checks':len(report['checks']),'failed':len(report['errors']),'screens':len(report['screens']),'runtime_errors':report['console']},ensure_ascii=False),flush=True)
    return 1 if report['errors'] else 0

if __name__=='__main__':raise SystemExit(main())
