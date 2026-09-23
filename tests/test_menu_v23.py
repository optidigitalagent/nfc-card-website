"""Focused local acceptance for the additive NFC Menu Card pages and payload."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
from threading import Thread

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import pytest
from server.pricing import menu_quote


ROOT = Path(__file__).resolve().parents[1]


def test_local_python_menu_quote_matches_tiers_and_consultation():
    for quantity, unit in ((1,1000),(4,1000),(5,750),(6,750),(9,750),
                           (10,600),(15,600),(24,600),(25,500),(26,500)):
        quote = menu_quote([{'variant_id':'square_100_black','quantity':quantity}])
        assert quote['amount'] == quantity * unit
        assert quote['balance'] == quote['amount'] - 200
    mixed = menu_quote([{'variant_id':'square_100_black','quantity':2},
                        {'variant_id':'square_60_white','quantity':2},
                        {'variant_id':'round_70_black','quantity':2}])
    assert mixed['quantity'] == 6 and mixed['amount'] == 4500
    assert menu_quote([], 'menu_consultation')['amount'] is None
    with pytest.raises(ValueError):
        menu_quote([{'variant_id':'square_100_black','quantity':True}])


def node(source):
    subprocess.run(['node', '--input-type=module', '-e', source], cwd=ROOT, check=True,
                   capture_output=True, text=True)


def page(route, locale='uk'):
    prefix = 'en/' if locale == 'en' else ''
    return BeautifulSoup((ROOT / 'site' / prefix / route / 'index.html').read_text(), 'html.parser')


def test_menu_tiers_rows_and_payload_contract():
    node(r"""
      import assert from 'node:assert/strict';
      import {MENU_VARIANTS,normalizeMenuRows,menuQuote,menuPublicURL} from './src/menu-contract.mjs';
      import {menuLeadPayload} from './src/menu-client.mjs';
      assert.equal(MENU_VARIANTS.length,6);
      for(const [quantity,unit] of [[1,1000],[4,1000],[5,750],[9,750],[10,600],[24,600],[25,500]]) {
        const q=menuQuote([{variant_id:MENU_VARIANTS[0],quantity}]);
        assert.equal(q.amount,quantity*unit);assert.equal(q.deposit,200);assert.equal(q.balance,q.amount-200);
      }
      const items=[{variant_id:MENU_VARIANTS[0],quantity:2},{variant_id:MENU_VARIANTS[2],quantity:2},{variant_id:MENU_VARIANTS[4],quantity:2}];
      assert.equal(menuQuote(items).amount,4500);
      assert.deepEqual(normalizeMenuRows([{variant_id:MENU_VARIANTS[0],quantity:1},{variant_id:MENU_VARIANTS[0],quantity:2}]),[{variant_id:MENU_VARIANTS[0],quantity:3}]);
      for(const bad of [0,-1,1.5,'2',10001])assert.throws(()=>menuQuote([{variant_id:MENU_VARIANTS[0],quantity:bad}]));
      for(const bad of ['javascript:alert(1)','http://127.0.0.1/a','https://localhost/a','https://user'+':pass@example.org/a',
        'https://192.0.2.1/menu','https://198.51.100.3/menu','https://203.0.113.4/menu'])assert.equal(menuPublicURL(bad),null);
      assert.equal(menuPublicURL('https://restaurant.org/menu'),'https://restaurant.org/menu');
      const common={locale:'uk',name:'Тест',phone:'+380 67 123 4567',messenger:'telegram',consent:true,website:'',comment:'',menu_status:'existing',intent:'card_order',menu_url:'https://restaurant.org/menu',items};
      const order=menuLeadPayload(common,{basePath:'/nfc-card-website',pathname:'/nfc-card-website/solutions/menu-card'});
      assert.equal(order.quantity,6);assert.equal(order.items.length,3);assert.equal(order.menu_url,'https://restaurant.org/menu');
      assert.equal(order.product_id,'nfc-menu-card');assert.equal(order.sourcePage,'/nfc-card-website/solutions/menu-card');
      assert.equal('offer' in order,false);
      assert.equal('amount' in order,false);
      const consult=menuLeadPayload({...common,intent:'menu_consultation',menu_status:'needs_development',items:[],menu_url:''},{basePath:'/nfc-card-website',pathname:'/nfc-card-website/menu-card'});
      for(const field of ['quantity','items','menu_url'])assert.equal(field in consult,false);
      assert.throws(()=>menuLeadPayload({...common,menu_url:'http://127.0.0.1/private'},{pathname:'/solutions/menu-card'}));
    """)


def test_bilingual_pages_gallery_faq_and_form_are_coherent():
    for locale in ('uk', 'en'):
        product = page('solutions/menu-card', locale)
        info = page('menu-card', locale)
        catalog = page('solutions', locale)
        home = BeautifulSoup((ROOT / 'site' / ('en/' if locale == 'en' else '') / 'index.html').read_text(), 'html.parser')
        assert product.select_one('h1').get_text(strip=True) == 'NFC Menu Card'
        assert len(product.select('.commerce-gallery [data-slide]')) == 10
        assert len(product.select('[data-menu-row-template] option[value]')) == 7
        assert len(product.select('.menu-form [name="menu-intent"]')) == 2
        assert len(product.select('.menu-form [name="menu-status"]')) == 2
        assert product.select_one('[name="menu-url"]')['maxlength'] == '1000'
        assert product.select_one('[data-menu-total]') is not None
        assert product.select_one('[data-menu-deposit]') is not None
        assert product.select_one('[data-menu-new-request]') is not None
        assert len(product.select('.product-detail .faq-list>details')) == 15
        schema = [json.loads(tag.string) for tag in product.select('script[type="application/ld+json"]')]
        faq = next(item for item in schema if item['@type'] == 'FAQPage')['mainEntity']
        visible = [(item.summary.get_text(' ', strip=True),item.p.get_text(' ', strip=True))
                   for item in product.select('.product-detail .faq-list>details')]
        assert visible == [(item['name'],item['acceptedAnswer']['text']) for item in faq]
        assert info.select_one('a[href$="/solutions/menu-card"]')
        assert catalog.select_one('.menu-catalog-card')
        assert home.select_one('#faq-menu-faq-1 a[href$="/solutions/menu-card"]')
        assert home.select_one('#faq-menu-faq-4 a[href*="menu_status=needs_development"]')
        assert home.select_one('#request .button')['href'].endswith('/solutions')
        assert product.select_one('[name="consent"]')['required'] == ''
        assert product.select_one('.menu-form [type="submit"]').has_attr('disabled')


@pytest.mark.parametrize('old_state', ['complete', 'uncertain'])
def test_reloaded_attempt_can_start_and_submit_new_enquiry(old_state):
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

    handler = partial(QuietHandler, directory=str(ROOT / 'site'))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sent = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            endpoint = 'https://gateway.nfccard.com/v1/public/leads/nfc-card'

            def reply(route):
                if '/challenge?' in route.request.url:
                    route.fulfill(status=200, content_type='application/json', body=json.dumps({
                        'challenge': 'eyJhdCI6MTAwMDB9.' + 'x' * 43, 'minimumDelayMs': 2000}))
                else:
                    sent.append({'key': route.request.headers['idempotency-key'],
                                 'body': route.request.post_data_json})
                    route.fulfill(status=202, content_type='application/json', body=json.dumps({
                        'ok': True, 'source': 'NFC_CARD', 'durableSaved': True,
                        'leadId': 'a1b2c3d4-1234-4123-8123-123456789abc'}))

            page.route(endpoint + '**', reply)
            page.goto(f'http://127.0.0.1:{server.server_port}/solutions/menu-card/', wait_until='networkidle')
            old_key = page.evaluate("crypto.randomUUID()")
            page.evaluate("""async ({oldState,oldKey,endpoint})=>{
              const current=document.querySelector('[data-menu-form]');
              const fresh=current.cloneNode(true);current.replaceWith(fresh);
              delete fresh.dataset.menuMounted;
              sessionStorage.setItem('nfc-menu-v23-attempt:/nfc-card-website/solutions/menu-card',JSON.stringify({
                key:oldKey,state:oldState,leadId:'b1b2c3d4-1234-4123-8123-123456789abc'}));
              const {mountMenuForm}=await import('/assets/menu-client.mjs');
              mountMenuForm(fresh,{endpoint,basePath:'/nfc-card-website',locale:'uk',pathname:'/nfc-card-website/solutions/menu-card'});
            }""", {'oldState': old_state, 'oldKey': old_key, 'endpoint': endpoint})
            page.locator('[data-menu-new-request]').click()
            assert not page.locator('.menu-form [type="submit"]').is_disabled()
            page.locator('.menu-form [name="name"]').fill('Тест')
            page.locator('.menu-form [name="phone"]').fill('+380671234567')
            page.locator('.menu-form [name="messenger"][value="telegram"]').check()
            page.locator('.menu-form [name="menu-variant"]').first.select_option('square_100_black')
            page.locator('.menu-form [name="menu-status"][value="needs_development"]').check()
            page.locator('.menu-form [name="consent"]').check()
            page.locator('.menu-form [type="submit"]').click()
            page.locator('.menu-form .form-result[data-status="success"]').wait_for(timeout=10000)
            assert len(sent) == 1
            assert sent[0]['key'] != old_key
            assert sent[0]['body']['product_id'] == 'nfc-menu-card'
            assert 'offer' not in sent[0]['body']
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
