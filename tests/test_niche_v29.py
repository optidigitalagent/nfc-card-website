"""Beauty and Restaurant public solution contracts, including market inheritance."""
import json
from pathlib import Path
import re
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
KINDS = ('beauty', 'restaurant')
LANGS = ('uk', 'en', 'pl')
EXPECTED = {'uk': (2000, 3600, 'UAH'), 'en': (2000, 3600, 'UAH'), 'pl': (169, 299, 'PLN')}


def route(lang, kind):
    prefix = '' if lang == 'uk' else lang + '/'
    return SITE / prefix / 'solutions' / f'{kind}-review-card' / 'index.html'


def test_six_pages_exact_product_content_and_schema():
    for lang in LANGS:
        content = json.loads((ROOT / f'src/niche-content.{lang}.json').read_text())
        for kind in KINDS:
            product = content['products'][kind]
            soup = BeautifulSoup(route(lang, kind).read_text(), 'html.parser')
            text = soup.get_text(' ', strip=True)
            assert soup.h1.get_text(' ', strip=True) == product['h1']
            assert soup.title.string == product['seo_title']
            assert soup.select_one('meta[name=description]')['content'] == product['seo_description']
            for key in ('headline', 'lead', 'summary', 'final_heading', 'final_body', 'form_heading', 'form_intro'):
                assert product[key] in text, (lang, kind, key)
            for section in product['sections']:
                assert section['heading'] in text
                assert all(value in text for value in section.get('paragraphs', []))
                assert all(value in text for value in section.get('items', []))
            visible_faq = [(node.summary.get_text(' ', strip=True), node.p.get_text(' ', strip=True))
                           for node in soup.select('.niche-product .faq-list details')]
            assert visible_faq == [(item['question'], item['answer']) for item in product['faq']]
            nodes = [json.loads(node.string) for node in soup.select('script[type="application/ld+json"]')]
            schema = next(node for node in nodes if node['@type'] == 'Product')
            assert schema['name'] == product['name']
            assert [(int(o['price']), o['priceCurrency']) for o in schema['offers']] == [
                (EXPECTED[lang][0], EXPECTED[lang][2]), (EXPECTED[lang][1], EXPECTED[lang][2])]
            schema_faq = next(node for node in nodes if node['@type'] == 'FAQPage')['mainEntity']
            assert [(f['name'], f['acceptedAnswer']['text']) for f in schema_faq] == visible_faq
            assert not any(key in text for key in ('catalog_description', 'form_success_body', '[S1]', '[S8]'))
            assert len(soup.select('link[hreflang]')) == 4
            assert soup.select_one('[data-niche-form] [name=variant]')['value'] == 'branded'
            assert [o['value'] for o in soup.select('[data-niche-form] [name=quantity] option')] == ['1', '2', 'more', 'advice']


def test_ten_owner_photos_correctly_partitioned_and_optimized():
    manifest = json.loads((ROOT / 'src/media-manifest.json').read_text())
    for kind in KINDS:
        primaries = [item for item in manifest if item.get('managed_by') == 'v29_niche_media_import'
                     and item.get('product_id') == f'{kind}-review-card' and 'derivative_of' not in item]
        assert len(primaries) == 5
        for lang in LANGS:
            soup = BeautifulSoup(route(lang, kind).read_text(), 'html.parser')
            slides = soup.select('.niche-hero .commerce-gallery [data-slide]')
            assert len(slides) == 5
            names = [slide.img['src'].split('/')[-1] for slide in slides]
            assert names == [item['url'].split('/')[-1] for item in primaries]
            assert all(slide.img['srcset'] and slide.select_one('source[type="image/avif"]') for slide in slides)
            assert all(slide.img['alt'] == primaries[i][{'uk':'alt_ua','en':'alt_en','pl':'alt_pl'}[lang]] for i,slide in enumerate(slides))
            assert not any('customer case' in slide.img['alt'].lower() for slide in slides)


def test_sitewide_routes_and_guarantee_hold():
    sitemap = (SITE / 'sitemap.xml').read_text()
    for lang in LANGS:
        prefix = '' if lang == 'uk' else '/' + lang
        for kind in KINDS:
            path = f'{prefix}/solutions/{kind}-review-card'
            assert path in sitemap
            for surface in ('index.html', 'solutions/index.html', 'contact/index.html', 'order/index.html'):
                page = SITE / ('' if lang == 'uk' else lang) / surface
                assert path in page.read_text(), (lang, kind, surface)
    for page in SITE.rglob('*.html'):
        html = page.read_text()
        assert not re.search(r'\+\s*40\s*%|50\s*%\s*(?:refund|повернен|zwrot)', html, re.I)


def test_payload_preserves_solution_and_quantity_advice_without_purchase():
    script = '''
      import {leadPayload} from './src/pages.mjs';
      import assert from 'node:assert/strict';
      const base={name:'Example',phone:'+380980421619',messenger:'telegram',consent:true,locale:'uk',variant:'branded'};
      for(const [id,niche] of [['beauty-review-card','beauty_salon'],['restaurant-review-card','restaurant']]){
        const path='/nfc-card-website/solutions/'+id+'/';
        for(const q of ['1','2','more','advice']){
          const value=leadPayload({...base,solution:id,quantity:q},{basePath:'/nfc-card-website',pathname:path});
          assert.equal(value.product,'branded-review-card');
          assert.deepEqual(value.solution,{schemaVersion:1,solution_id:id,niche,request_type:'free_first_mockup'});
          assert.equal(value.selection.variant,'branded');
          if(q==='advice')assert.equal(Object.hasOwn(value,'quantity'),false);
          else assert.equal(value.quantity,q==='more'?3:Number(q));
        }
      }
      assert.throws(()=>leadPayload({...base,solution:'unknown',quantity:'1'},{basePath:'/nfc-card-website',pathname:'/nfc-card-website/order/'}));
    '''
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
