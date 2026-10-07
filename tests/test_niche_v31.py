"""v31 Beauty/Restaurant Mini products: rendered content, media and payload contracts."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import subprocess
from threading import Thread

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
LANGS = ('uk', 'en', 'pl')
PRODUCTS = {
    'beauty': ('beauty-review-card', 'beauty', 'ready'),
    'brandedBeauty': ('branded-beauty-review-card', 'beauty', 'branded'),
    'restaurant': ('restaurant-review-card', 'restaurant', 'ready'),
    'brandedRestaurant': ('branded-restaurant-review-card', 'restaurant', 'branded'),
}
QUANTITIES = (1, 2, 4, 10)
TOTALS = {
    'ready': (900, 1440, 2600, 4400),
    'branded': (900, 1800, 3000, 5000),
}
PHOTOS = {
    'beauty': ('front-hand', 'group-hand', 'group-front', 'edge-thickness', 'back-mounting'),
    'restaurant': ('front-hand', 'group-hand', 'group-front', 'edge-thickness', 'back-mounting'),
}


def route(lang, slug):
    prefix = '' if lang == 'uk' else lang + '/'
    return SITE / prefix / 'solutions' / slug / 'index.html'


def soup_at(lang, slug):
    return BeautifulSoup(route(lang, slug).read_text('utf-8'), 'html.parser')


def product_schema(soup):
    nodes = [json.loads(node.string) for node in soup.select('script[type="application/ld+json"]')]
    return next(node for node in nodes if node['@type'] == 'Product')


def test_twelve_mini_pages_keep_distinct_products_and_exact_market_prices():
    for lang in LANGS:
        content = json.loads((ROOT / f'src/niche-content.{lang}.json').read_text('utf-8'))
        for kind, (slug, niche, design) in PRODUCTS.items():
            product = content['products'][kind]
            soup = soup_at(lang, slug)
            main = soup.select_one('.niche-product')
            assert main and main['data-niche-page'] == slug
            assert soup.h1.get_text(' ', strip=True) == product['h1']
            assert soup.title.string == product['seo_title']
            assert soup.select_one('meta[name=description]')['content'] == product['seo_description']
            text = main.get_text(' ', strip=True)
            for key in ('lead', 'final_heading', 'final_body', 'form_heading', 'form_intro'):
                assert product[key] in text, (lang, slug, key)
            assert len(main.select('.niche-hero .product-promise')) == 1
            assert len(main.select('.niche-hero .niche-descriptor')) == 0
            for section in product['sections']:
                assert section['heading'] in text, (lang, slug, section['id'])
            faq = [(node.summary.get_text(' ', strip=True), node.p.get_text(' ', strip=True))
                   for node in main.select('.faq-list details')]
            assert faq == [(item['question'], item['answer']) for item in product['faq']]
            schema = product_schema(soup)
            assert schema['name'] == product['name']
            assert len(schema['image']) == 5
            if lang == 'pl':
                assert not schema.get('offers')
                assert 'UAH' not in text and 'грн' not in text
                assert main.select_one('.niche-pricing .price-rows dd').get_text(' ', strip=True) == 'Wycena indywidualna'
            else:
                offers = schema['offers']
                assert [o['eligibleQuantity']['minValue'] for o in offers] == list(QUANTITIES)
                assert [(int(o['price']), o['priceCurrency']) for o in offers] == [
                    (amount, 'UAH') for amount in TOTALS[design]]
                pricing = main.select('.niche-pricing .price-rows dd')
                assert len(pricing) == 5
                for amount, row in zip(TOTALS[design], pricing):
                    assert str(amount) in row.get_text(' ', strip=True)
            assert len(soup.select('link[hreflang]')) == 4
            form = main.select_one('[data-niche-form]')
            assert form['data-solution'] == slug and form['data-design-mode'] == design
            assert form['data-product-family'] == 'nfc-review-card-mini'
            assert form.select_one('[name=variant]')['value'] == ('branded' if design == 'branded' else 'standard')
            expected_options = (['concepts'] if design == 'branded' else []) + ['1', '2', '4', '10', 'other', 'advice']
            assert [option['value'] for option in form.select('[name=quantity] option')] == expected_options
            if design == 'ready':
                assert not form.select('[name=brandLink],[name=logoNote],[name=brandStyle],[name=designSplitNote]')
                own_offer = ' '.join(node.get_text(' ', strip=True) for node in
                                     main.select('.niche-hero,.niche-request,.niche-detail'))
                assert not re.search(r'first (?:free )?mockup|3[–-]4 initial concepts', own_offer, re.I)
            else:
                assert {node['name'] for node in form.select('input[name]')} >= {
                    'brandLink', 'logoNote', 'brandStyle', 'designSplitNote'}
                assert '3–4' in text
            assert not re.search(r'(?:10\s*[×x]\s*10|6\s*[×x]\s*6)\s*(?:cm|см)', text, re.I)
            assert not re.search(r'\+\s*40\s*%|50\s*%\s*(?:refund|повернен|zwrot)', text, re.I)


def test_v32_mini_copy_intent_market_terms_and_polish_gallery_are_rendered():
    for lang in LANGS:
        for slug, _, design in PRODUCTS.values():
            soup = soup_at(lang, slug)
            hero = soup.select_one('.niche-hero .commerce-purchase')
            assert len(hero.select('.product-promise')) == 1
            assert not hero.select('.niche-descriptor')
            pricing = soup.select_one('.niche-pricing').get_text(' ', strip=True)
            if lang == 'pl':
                assert 'Zamówienie wysyłamy z Ukrainy' in pricing
                assert 'Koszt dostawy pokrywa klient' in pricing
                assert 'potwierdzenia nadania' in pricing
                assert soup.select_one('[data-niche-form] [name=phone]')['placeholder'] == '+48 ___ ___ ___'
                assert soup.select_one('.niche-hero .breadcrumbs')['aria-label'] == 'Ścieżka nawigacji'
                gallery = soup.select_one('.niche-hero .commerce-gallery')
                assert gallery.select_one('.gallery-hint').get_text(' ', strip=True) == 'Przeglądaj zdjęcia'
                assert gallery.select_one('.image-lightbox')['aria-label'] == 'Podgląd zdjęć karty'
                assert gallery.select_one('[data-lightbox-close]')['aria-label'] == 'Zamknij podgląd'
            else:
                assert ('Новою поштою по Україні' if lang == 'uk' else 'Nova Poshta delivery in Ukraine is free') in pricing
                assert ('ТТН' if lang == 'uk' else 'tracking number') in pricing
            if design == 'branded':
                assert soup.select_one('[data-niche-form] [name=quantity] option[selected]')['value'] == 'concepts'
                assert soup.select_one('.niche-hero a[data-niche-intent=concepts]')['href'].endswith('/?intent=concepts#request')
                assert soup.select_one('.final-conversion a[data-niche-intent=concepts]')


def test_ten_owner_photos_are_separated_and_branded_gallery_marks_ready_artwork_as_example():
    manifest = json.loads((ROOT / 'src/media-manifest.json').read_text('utf-8'))
    for niche in PHOTOS:
        primaries = [item for item in manifest if item.get('managed_by') == 'v29_niche_media_import'
                     and item.get('product_id') == f'{niche}-review-card' and 'derivative_of' not in item]
        assert [item['gallery_order'] for item in primaries] == [1, 2, 3, 4, 5]
        names = [f'{niche}-review-card-{suffix}.webp' for suffix in PHOTOS[niche]]
        assert [item['url'].split('/')[-1] for item in primaries] == names
        assert all(item['provenance'] == 'user_provided_business_asset' and
                   item['not_customer_case_evidence'] and item['responsive'] and item['avif'] for item in primaries)
        for lang in LANGS:
            for design in ('ready', 'branded'):
                slug = f'{"branded-" if design == "branded" else ""}{niche}-review-card'
                soup = soup_at(lang, slug)
                slides = soup.select('.niche-hero .commerce-gallery [data-slide]')
                assert len(slides) == 5
                assert [slide.img['src'].split('/')[-1] for slide in slides] == names
                for item, slide in zip(primaries, slides):
                    assert slide.select_one('source[type="image/avif"]')
                    assert slide.img['srcset']
                    assert slide.img['alt'] == item['alt_' + ('ua' if lang == 'uk' else lang)]
                    caption = slide['data-caption']
                    if design == 'ready':
                        assert caption == item['caption_' + ('ua' if lang == 'uk' else lang)]
                    else:
                        assert caption != item['caption_' + ('ua' if lang == 'uk' else lang)]
                        assert {'uk': 'фізичного формату', 'en': 'physical-format example',
                                'pl': 'fizycznego formatu'}[lang] in caption
                        assert {'uk': 'окремо', 'en': 'separately', 'pl': 'osobno'}[lang] in caption
                assert 'customer case' not in soup.select_one('.commerce-gallery').get_text(' ', strip=True).lower()


def test_four_catalog_cards_use_photos_only_for_ready_products():
    for lang in LANGS:
        prefix = '' if lang == 'uk' else lang + '/'
        for surface in ('index.html', 'solutions/index.html'):
            soup = BeautifulSoup((SITE / prefix / surface).read_text('utf-8'), 'html.parser')
            cards = soup.select('.catalog .niche-card')
            assert [card['data-solution'] for card in cards] == [value[0] for value in PRODUCTS.values()]
            for card, (_, niche, design) in zip(cards, PRODUCTS.values()):
                if design == 'ready':
                    assert niche in card.select_one('img.catalog-product-image')['src']
                else:
                    assert card.select_one('[data-design-role="custom_layout_example"]')
                    assert not card.select_one('img.catalog-product-image')
                    assert 'Branded Review Card</text>' not in str(card)


def test_twelve_routes_in_sitemap_and_no_guarantee_claim():
    sitemap = (SITE / 'sitemap.xml').read_text('utf-8')
    for lang in LANGS:
        prefix = '' if lang == 'uk' else '/' + lang
        for slug, _, _ in PRODUCTS.values():
            assert f'{prefix}/solutions/{slug}' in sitemap
    for page in SITE.rglob('*.html'):
        assert not re.search(r'\+\s*40\s*%|50\s*%\s*(?:refund|повернен|zwrot)', page.read_text('utf-8'), re.I)


def test_mini_quote_and_payload_preserve_niche_design_quantity_mode_without_client_amount():
    script = r'''
      import assert from 'node:assert/strict';
      import {miniQuote,MINI_PRODUCTS} from './src/mini-contract.mjs';
      import {leadPayload} from './src/pages.mjs';
      const totals={ready:{1:900,2:1440,4:2600,10:4400},branded:{1:900,2:1800,4:3000,10:5000}};
      for(const [id,product] of Object.entries(MINI_PRODUCTS))for(const locale of ['uk','en','pl']){
        const prefix=locale==='uk'?'':'/'+locale;
        const pathname='/nfc-card-website'+prefix+'/solutions/'+id+'/';
        const base={name:'Example',phone:'+380980421619',messenger:'telegram',consent:true,locale,
          productFamily:'nfc-review-card-mini',
          variant:product.designMode==='branded'?'branded':'standard',solution:id,
          brandLink:'',logoNote:'',brandStyle:'',designSplitNote:''};
        const make=fields=>leadPayload({...base,...fields},{basePath:'/nfc-card-website',pathname});
        for(const [quantity,amount] of Object.entries(totals[product.designMode])){
          const quote=miniQuote(id,Number(quantity),locale);
          assert.equal(quote.amount,locale==='pl'?null:amount);
          assert.equal(quote.deposit,locale==='pl'?null:200);
          assert.equal(quote.depositDueNow,false);
          const payload=make({quantity});
          assert.equal(payload.product,'nfc-review-card-mini');
          assert.equal(payload.quantity,Number(quantity));
          assert.equal(payload.solution.product_family,'nfc-review-card-mini');
          assert.equal(payload.solution.solution_id,id);
          assert.equal(payload.solution.niche,product.niche);
          assert.equal(payload.solution.design_mode,product.designMode);
          assert.equal(payload.solution.quantity_mode,locale==='pl'?'custom_quote':'fixed_bundle');
          for(const key of ['amount','unitPrice','currency','deposit','total'])assert.equal(Object.hasOwn(payload,key),false);
        }
        for(const quantity of [3,5,9,11]){
          const quote=miniQuote(id,quantity,locale);
          assert.equal(quote.amount,null);
          assert.equal(quote.deposit,null);
          assert.equal(quote.quantityMode,'custom_quote');
          const payload=make({quantity:'other',customQuantity:String(quantity)});
          assert.equal(payload.quantity,quantity);
          assert.equal(payload.solution.quantity_mode,'custom_quote');
        }
        const advice=make({quantity:'advice'});
        assert.equal(Object.hasOwn(advice,'quantity'),false);
        assert.equal(advice.solution.quantity_mode,'advice');
        if(product.designMode==='branded'){
          const concepts=make({quantity:'concepts',brandLink:'https://example.com',logoNote:'logo',brandStyle:'pink',designSplitNote:'5 + 5'});
          assert.equal(Object.hasOwn(concepts,'quantity'),false);
          assert.equal(concepts.solution.quantity_mode,'free_design_concepts');
          assert.deepEqual(concepts.solution.brand_inputs,{logo_note:'logo',website_or_instagram:'https://example.com',style_note:'pink'});
          assert.equal(concepts.solution.design_split_note,'5 + 5');
          assert.equal(miniQuote(id,null,locale,'free_design_concepts').amount,null);
        } else {
          assert.throws(()=>make({quantity:'concepts'}));
          assert.throws(()=>make({quantity:'1',logoNote:'custom logo'}));
        }
        assert.throws(()=>make({quantity:'3'}));
        assert.throws(()=>leadPayload({...base,quantity:'1'},{basePath:'/nfc-card-website',pathname:'/nfc-card-website/order/'}));
      }
      for(const id of ['beauty-review-card','restaurant-review-card']){
        const old=leadPayload({name:'Example',phone:'+380980421619',messenger:'telegram',consent:true,
          locale:'uk',variant:'branded',solution:id,quantity:'2'},
          {basePath:'/nfc-card-website',pathname:'/nfc-card-website/solutions/'+id+'/'});
        assert.equal(old.product,'branded-review-card');
        assert.equal(old.solution.schemaVersion,1);
        assert.equal(old.solution.request_type,'free_first_mockup');
      }
    '''
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr


def test_mini_pages_browser_selector_and_layout_without_external_requests():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(SITE)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for width in (320, 1280):
                context = browser.new_context(viewport={'width': width, 'height': 900})
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin)
                              else route.abort())
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                for lang in LANGS:
                    prefix = '' if lang == 'uk' else '/' + lang
                    for slug, _, design in PRODUCTS.values():
                        response = page.goto(origin + prefix + '/solutions/' + slug + '/', wait_until='networkidle')
                        assert response.status == 200
                        form = page.locator('[data-niche-form]')
                        assert form.get_attribute('data-enhanced') == 'true'
                        assert page.locator('.commerce-gallery [data-slide]').count() == 5
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (lang, slug, width)
                        form.locator('[name=quantity]').select_option('10')
                        summary = form.locator('[data-niche-price]').inner_text()
                        assert ('5000' if design == 'branded' else '4400') in summary if lang != 'pl' else 'Wycena' in summary
                        form.locator('[name=quantity]').select_option('other')
                        custom = form.locator('[name=customQuantity]')
                        assert custom.is_visible() and custom.is_enabled()
                        assert 'quote' in form.locator('[data-niche-price]').inner_text().lower() if lang == 'en' else True
                        if design == 'branded':
                            form.locator('[name=quantity]').select_option('concepts')
                            assert '3–4' in form.locator('[data-niche-price]').inner_text()
                            form.locator('[name=name]').fill('Synthetic draft')
                            form.locator('[name=quantity]').select_option('10')
                            page.locator('.niche-hero [data-niche-intent=concepts]').click()
                            assert form.locator('[name=quantity]').input_value() == 'concepts'
                            assert form.locator('[name=name]').input_value() == 'Synthetic draft'
                            assert page.url.split('?', 1)[0].endswith('/solutions/' + slug + '/')
                        assert not errors, (lang, slug, width, errors)
                context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
