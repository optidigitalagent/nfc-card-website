"""Focused v25 acceptance on the existing product routes and local fake gateway."""
from pathlib import Path
import subprocess

from bs4 import BeautifulSoup
from playwright.sync_api import expect
import pytest

from test_v12_browser import browser, web, repo, service, block_external, ready


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
PRODUCTS = ('review-card', 'instagram-card', 'menu-card')
LABELS = {'review-card': 'NFC Review Card', 'instagram-card': 'NFC Instagram Card', 'menu-card': 'NFC Menu Card'}
HEADINGS = {'review-card': 'Review Card', 'instagram-card': 'NFC Instagram Card', 'menu-card': 'NFC Menu Card'}


@pytest.mark.parametrize('prefix,locale', [('', 'uk'), ('/en', 'en')])
def test_direct_product_navigation_and_targeted_copy(prefix, locale):
    def page(route):
        return BeautifulSoup((SITE / (prefix + route).lstrip('/') / 'index.html').read_text(), 'html.parser')

    home = page('/')
    for selector in ('.desktop-nav', '#mobile-menu nav'):
        links = {a['href']: a.get_text(' ', strip=True) for a in home.select(selector + ' a[href]')}
        for product in PRODUCTS:
            path = prefix + '/solutions/' + product
            assert links[path] == LABELS[product]
    assert home.select_one('.commerce-card[data-variant="branded"]')
    for product, count in zip(PRODUCTS, (13, 5, 10)):
        product_page = page('/solutions/' + product)
        assert product_page.h1.get_text(' ', strip=True) == HEADINGS[product]
        assert len(product_page.select('.commerce-gallery [data-slide]')) == count
        assert not product_page.select('[data-lightbox-zoom], [data-lightbox-to], .thumb-index, .thumb-check')
    privacy = (ROOT / 'src/public-legal.mjs').read_text()
    if locale == 'uk':
        assert 'Коментар із форми Review Card або Branded Review Card не передається' in privacy
        assert 'Для NFC Instagram Card також передаємо посилання на Instagram-профіль і необов’язковий коментар' in privacy
        assert 'Будемо вдячні, якщо поділитеся враженнями про візит у Google' in home.get_text(' ', strip=True)
        assert 'потрібну форму Google-відгуку, Instagram-профіль або онлайн-меню' in page('/delivery-and-payment').get_text(' ', strip=True)
    else:
        assert 'The Review Card or Branded Review Card form comment is not transmitted' in privacy
        assert 'For NFC Instagram Card, we also send the Instagram profile URL and optional comment' in privacy
        assert 'We would appreciate your feedback about your visit on Google' in home.get_text(' ', strip=True)
        assert 'intended Google review form, Instagram profile or online menu' in page('/delivery-and-payment').get_text(' ', strip=True)
    assert 'NFC Menu Card' in page('/solutions/menu-card').h1.get_text(' ', strip=True)


def test_comment_payload_boundary_stays_honest():
    source = r"""
      import assert from 'node:assert/strict';
      import {leadPayload} from './src/pages.mjs';
      import {menuLeadPayload} from './src/menu-client.mjs';
      const common={locale:'uk',name:'Synthetic QA',phone:'+380671234567',messenger:'telegram',
        quantity:'1',comment:'Synthetic comment',consent:true,website:''};
      for(const variant of ['standard','branded']) {
        const route=variant==='standard'?'/solutions/review-card':'/solutions/branded-review-card';
        const lead=leadPayload({...common,variant},{pathname:route});
        assert.equal('comment' in lead,false);
      }
      const instagram=leadPayload({...common,variant:'instagram',instagramUrl:'https://www.instagram.com/example/'},
        {pathname:'/solutions/instagram-card'});
      assert.equal(instagram.comment,'Synthetic comment');
      const menu=menuLeadPayload({locale:'uk',name:'Synthetic QA',phone:'+380671234567',messenger:'telegram',
        consent:true,website:'',comment:'Synthetic comment',intent:'card_order',menu_status:'needs_development',
        menu_url:'',items:[{variant_id:'square_100_black',quantity:1}]},{pathname:'/solutions/menu-card'});
      assert.equal(menu.comment,'Synthetic comment');
    """
    subprocess.run(['node', '--input-type=module', '-e', source], cwd=ROOT, check=True, capture_output=True, text=True)


@pytest.mark.parametrize('prefix', ['', '/en'])
def test_explicit_menu_cta_wins_over_restored_consultation_and_preserves_rows(web, browser, prefix):
    origin, _ = web
    context = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True)
    block_external(context, origin)
    page = context.new_page()
    page.goto(origin + prefix + '/solutions/menu-card/', wait_until='networkidle')
    ready(page)
    variants = ('square_100_black', 'square_60_white', 'round_70_black')
    for index, variant in enumerate(variants):
        if index:
            page.locator('[data-menu-add]').click()
        page.locator('[name=menu-variant]').nth(index).select_option(variant)
        page.locator('[name=menu-quantity]').nth(index).fill('2')
    page.locator('[name=menu-intent][value=menu_consultation]').check()
    page.goto(origin + prefix + '/menu-card/', wait_until='networkidle')
    page.locator('.menu-info-page a[href*="intent=card_order"]').click()
    expect(page.locator('[name=menu-intent][value=card_order]')).to_be_checked()
    expect(page.locator('[name=menu-status][value=existing]')).to_be_checked()
    assert page.locator('[name=menu-url]').is_visible()
    assert page.locator('[name=menu-url]').evaluate('(e)=>e.required&&!e.disabled')
    assert page.locator('[name=menu-variant]').evaluate_all('els=>els.map(e=>e.value)') == list(variants)
    assert '4500' in page.locator('[data-menu-subtotal]').inner_text().replace('\u00a0', '').replace(' ', '').replace(',', '')
    page.locator('[name=menu-status][value=needs_development]').check()
    assert not page.locator('[name=menu-url]').is_visible()
    assert page.locator('[name=menu-variant]').evaluate_all('els=>els.map(e=>e.value)') == list(variants)
    page.locator('[name=menu-intent][value=menu_consultation]').check()
    assert page.locator('[data-menu-configuration]').is_hidden()
    assert page.locator('[data-menu-subtotal]').inner_text().strip() == '—'
    page.goto(origin + prefix + '/solutions/menu-card/?intent=invalid&menu_status=existing', wait_until='networkidle')
    expect(page.locator('[name=menu-intent][value=menu_consultation]')).to_be_checked()
    context.close()


@pytest.mark.parametrize('prefix', ['', '/en'])
@pytest.mark.parametrize('state', ['uncertain', 'complete'])
def test_explicit_menu_cta_requires_new_request_for_locked_attempt(web, browser, prefix, state):
    origin, _ = web
    context = browser.new_context(viewport={'width': 390, 'height': 844})
    block_external(context, origin)
    page = context.new_page()
    page.goto(origin + prefix + '/menu-card/', wait_until='networkidle')
    target_path = page.locator('.menu-info-page a[href*="intent=card_order"]').evaluate('(a)=>new URL(a.href).pathname')
    page.evaluate('''({path,state})=>{
      sessionStorage.setItem('nfc-menu-v23-config',JSON.stringify({intent:'menu_consultation',
        menu_status:'needs_development',items:[{variant_id:'square_100_black',quantity:2}]}));
      sessionStorage.setItem('nfc-menu-v23-attempt:'+path,JSON.stringify({
        key:'a1b2c3d4-1234-4123-8123-123456789abc',state,
        leadId:'b1b2c3d4-1234-4123-8123-123456789abc'}));
    }''', {'path': target_path, 'state': state})
    page.locator('.menu-info-page a[href*="intent=card_order"]').click()
    expect(page.locator('[data-menu-new-request]')).to_be_visible()
    expect(page.locator('[name=menu-intent][value=menu_consultation]')).to_be_checked()
    assert page.locator('.menu-form [type=submit]').is_disabled()
    page.locator('[data-menu-new-request]').click()
    expect(page.locator('[name=menu-intent][value=card_order]')).to_be_checked()
    expect(page.locator('[name=menu-status][value=existing]')).to_be_checked()
    assert page.locator('[name=menu-url]').evaluate('(e)=>e.required&&!e.disabled')
    assert page.locator('[name=menu-variant]').first.input_value() == 'square_100_black'
    assert page.evaluate('(path)=>sessionStorage.getItem("nfc-menu-v23-attempt:"+path)', target_path) is None
    context.close()


@pytest.mark.parametrize('prefix', ['', '/en'])
def test_order_and_contact_menu_launcher_remains_local(web, browser, prefix):
    origin, _ = web
    context = browser.new_context(viewport={'width': 390, 'height': 844})
    block_external(context, origin)
    page = context.new_page()
    for route in ('/order', '/contact'):
        page.goto(origin + prefix + route, wait_until='networkidle')
        page.locator('[data-menu-activate]').click()
        expect(page.locator('[data-menu-inline]')).to_be_visible()
        assert page.locator('[data-commerce-form]').is_hidden()
        assert page.locator('[data-menu-inline] [data-menu-form]').count() == 1
    context.close()
