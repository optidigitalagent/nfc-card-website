"""V13 user-feedback contracts; accepted pricing/reviews/security stay unchanged.

These checks compare output with owner-authorized source evidence. Layout and
interaction quality require the separate browser tests and independent critics.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
TASK = ROOT / 'refinements/visual-about-v13'
PIN = '013bd2d904d5be143a0e203d0005c29f25db729f'
PHOTO_ORDER = ['portrait', 'hockey-team', 'hockey-puck', 'gopro', 'jetski', 'boat', 'urban']


def read_json(path):
    return json.loads(path.read_text('utf-8'))


def page(route):
    return BeautifulSoup((SITE / route.lstrip('/') / 'index.html').read_text('utf-8'), 'html.parser')


def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()


def leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from leaves(child)
    elif isinstance(value, list):
        for child in value:
            yield from leaves(child)


def test_protected_v11_implementation_matches_recovery_bytes():
    snapshot = read_json(TASK / 'RECOVERY_SNAPSHOT.json')['files']
    protected = [p for p in snapshot if p.startswith('server/') and not p.startswith('server/templates/')]
    protected += ['src/commerce.json', 'src/display.mjs', 'src/redirects.json',
                  'src/review-view.mjs', 'src/reviews.js', 'src/reviews-renderer.js', 'src/admin-reviews.js']
    for path in protected:
        if path == 'server/wsgi.py':
            # v16 explicitly changes publication headers, initialization and
            # adds /healthz. Preserve the remaining accepted WSGI AST instead
            # of falsely requiring its old global-noindex file bytes.
            import ast
            tree = ast.parse((ROOT / path).read_text())
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Application')
            methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
            assert set(methods) == {'__init__', 'route', '__call__'}
            init = [s for s in methods['__init__'].body if isinstance(s, ast.Assign)
                    and any(ast.unparse(t) == 'self.publication' for t in s.targets)]
            assert len(init) == 1
            assert ast.unparse(init[0]) == 'self.publication = PublicationPolicy.from_build(ROOT, runtime)'
            methods['__init__'].body.remove(init[0])
            health = [s for s in methods['route'].body if isinstance(s, ast.If)
                      and "'/healthz'" in ast.unparse(s.test)]
            allowed = ["path == '/healthz' and request.method in ('GET', 'HEAD')",
                       "request.path == '/healthz' and request.method in ('GET', 'HEAD') and request.headers.get('host') == 'healthcheck.railway.app'"]
            assert len(health) == 2
            assert {ast.dump(s.test) for s in health} == {ast.dump(ast.parse(s, mode='eval').body) for s in allowed}
            methods['route'].body = [s for s in methods['route'].body if s not in health]
            for statement in methods['__call__'].body:
                if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                        and ast.unparse(statement.value.func) == 'response.headers.update'):
                    headers = statement.value.args[0]
                    pairs = [(k, v) for k, v in zip(headers.keys, headers.values)
                             if k.value not in ('Cache-Control', 'X-Robots-Tag')]
                    headers.keys = [k for k, _ in pairs]
                    headers.values = [v for _, v in pairs]
            # Independently derived from the sealed handoff's original WSGI AST,
            # with exactly those same release-only positions normalized.
            expected = {
                '__init__': 'f9c6d9dc37da67bb4b813f26a672544a3e8d8fd72c3cc0b9e25af8933772a34f',
                'route': '21983e1da9d1b3a0d5b1b8f2f526329f06a96bfc60a0d843d0bf866ebdebff11',
                '__call__': '4c404b229cf59d86e272d3810c32a99b1317fc9e5bc381a4ed87375a9117cd6d',
            }
            assert {name: hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                    for name, node in methods.items()} == expected
            continue
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == snapshot[path], path


@pytest.mark.parametrize('locale', ['uk', 'en'])
def test_about_preserves_pinned_founder_facts_and_limits_product_adaptation(locale):
    original = read_json(TASK / 'about-source' / f'resolved-pinned-{locale}.json')
    current = read_json(ROOT / 'src/about-content.json')[locale]
    # Product-specific copy can change; biography, dates and company facts cannot.
    assert current['behind']['title'] == original['behind']['title']
    assert current['behind']['paragraphs'][1:] == original['behind']['paragraphs'][1:]
    founder = deepcopy(current['founder'])
    founder['timeline'][6]['title'] = original['founder']['timeline'][6]['title']
    assert founder == original['founder']
    assert current['founder']['timeline'][5] == original['founder']['timeline'][5]
    assert current['founder']['timeline'][6]['title'] == (
        '20 серпня 2026 — NFC CARD' if locale == 'uk' else '20 August 2026 — NFC CARD')
    assert current['company']['paragraphs'] == original['company']['paragraphs']
    expected_items = deepcopy(original['company']['items'])
    expected_items[1]['title'] = 'NFC CARD'
    assert current['company']['items'] == [expected_items[1], expected_items[0], *expected_items[2:]]
    assert current['company']['productParagraphs'] != original['company']['productParagraphs']
    assert current['why'] != original['why'] and current['formula'] != original['formula']
    assert '{{product}}' not in json.dumps(current)


@pytest.mark.parametrize('locale', ['uk', 'en'])
def test_about_renders_complete_authorized_story_and_nfc_mission(locale):
    current = read_json(ROOT / 'src/about-content.json')[locale]
    soup = page('/about' if locale == 'uk' else '/en/about')
    text = normalized(soup.main.get_text(' ', strip=True))
    for key in ['behind', 'founder', 'company', 'why', 'formula']:
        for fact in leaves(current[key]):
            assert normalized(fact) in text, (locale, key, fact)
    for section in ['about-founder-story', 'founder-timeline', 'founder-hockey', 'founder-water',
                    'founder-competencies', 'company-principles', 'founder-philosophy', 'ecosystem', 'why-nfc-card']:
        node = soup.find(id=section)
        assert node and node.find('h2') and node.get('aria-labelledby')
    assert 'Review Card' in text and 'Branded Review Card' in text and 'Google' in text
    assert not soup.select('#client-reviews,[data-case-id],.cases')
    assert not soup.select('a[href^="mailto:"],img[src^="https:"],source[srcset^="https:"]')
    assert soup.select_one('.locale-switch')['href'] == ('/en/about' if locale == 'uk' else '/about')


def test_about_media_are_exact_pinned_privacy_reviewed_derivatives():
    manifest = read_json(TASK / 'about-source/source-manifest.json')
    assert manifest['pinnedCommit'] == PIN and manifest['sourceHead'] == PIN
    pinned = {item['sourcePath']: item for item in manifest['files']}
    originals = read_json(TASK / 'about-source/pinned/docs/founder-media-manifest.json')
    media = {item['url']: item for item in read_json(ROOT / 'src/media-manifest.json')}
    expected = {'/assets' + output['file'] for item in originals for output in item['outputs']}
    assert len(expected) == 28
    assert {url for url in media if url.startswith('/assets/media/founder/')} == expected
    original_hashes = {item['sourceSha256'] for item in originals}
    for item in originals:
        for output in item['outputs']:
            record = media['/assets' + output['file']]
            source_path = 'public' + output['file']
            assert record['source_commit'] == PIN and record['source_path'] == source_path
            assert record['sha256'] == pinned[source_path]['sha256']
            assert record['provenance'] == 'verified_official_business_asset'
            assert record['crop'] == output['crop']
            assert record['width'] == output['width'] and record['height'] == output['height']
            assert hashlib.sha256((SITE / record['url'].lstrip('/')).read_bytes()).hexdigest() == record['sha256']
    # No original uncropped founder upload can silently enter the public asset tree.
    assert not original_hashes.intersection(hashlib.sha256(p.read_bytes()).hexdigest() for p in (SITE / 'assets/media').rglob('*') if p.is_file())


def test_product_derivatives_are_bounded_and_preserve_source_ratio_and_identity():
    media = {item['url']: item for item in read_json(ROOT / 'src/media-manifest.json')}
    names = ['01-review-card-design-render', '02-review-card-real-front', '03-review-card-real-in-hand',
             '04-review-card-real-back', '05-promo-direct-review-form']
    expected = {f'/assets/media/v13/{name}-{size}.webp' for name in names for size in [160,480,800]}
    expected.add('/assets/media/v13/branded-catalog.svg')
    assert {url for url in media if '/media/v13/' in url} == expected
    for name in names:
        original = media[f'/assets/media/v9/{name}.webp']
        for size in [160,480,800]:
            derived = media[f'/assets/media/v13/{name}-{size}.webp']
            assert derived['derivative_of'] == original['url']
            assert derived['provenance'] == original['provenance'] and derived['claim_role'] == original['claim_role']
            with Image.open(SITE / derived['url'].lstrip('/')) as image:
                assert image.width == size
                assert abs(image.width/image.height - int(original['width'])/int(original['height'])) < .01
                assert not image.getexif()
    branded = media['/assets/media/v13/branded-catalog.svg']
    assert branded['derivative_of'] == '/assets/media/v11/branded-review-card-neutral-placeholder.svg'
    svg = BeautifulSoup((SITE / branded['url'].lstrip('/')).read_text('utf-8'), 'xml')
    assert not svg.select('script,foreignObject,image,use')
    assert not any(key.lower().startswith('on') for el in svg.find_all() for key in el.attrs)


@pytest.mark.parametrize('locale', ['uk', 'en'])
def test_about_photo_order_alts_and_responsive_variants(locale):
    soup = page('/about' if locale == 'uk' else '/en/about')
    media = read_json(ROOT / 'src/about-media.json')
    figures = soup.select('[data-founder-photo]')
    assert not soup.select('[style],style'), 'About must work under the accepted self-only style CSP.'
    assert [f['data-founder-photo'] for f in figures] == PHOTO_ORDER
    for figure in figures:
        asset = media[figure['data-founder-photo']]
        img = figure.select_one('img')
        assert img['alt'] == asset['alt'][locale] and img['loading'] == 'lazy'
        assert int(img['width']) > 0 and int(img['height']) > 0
        sources = figure.select('picture>source')
        assert len(sources) == 4
        assert {s['srcset'].split()[0] for s in sources} == {v['file'] for v in asset['variants']}
        assert {s['type'] for s in sources} == {'image/avif', 'image/webp'}
        assert all(s.get('media') and s.get('width') and s.get('height') for s in sources)


@pytest.mark.parametrize('prefix', ['', '/en'])
def test_about_navigation_and_final_home_conversion_target(prefix):
    home = page(prefix or '/')
    about = prefix + '/about'
    for scope in [home.header, home.select_one('#mobile-menu'), home.footer, home.select_one('#about')]:
        assert scope and scope.find('a', href=about)
    sections = home.main.find_all('section', recursive=False)
    last = sections[-1]
    assert 'final-conversion' in last.get('class', [])
    assert not home.select('.lead-form')
    assert last.find('a', href=prefix + '/order')
    assert home.main.find_next_sibling().name == 'footer'
    # A compact footer has essential destinations, rather than another request form.
    assert not home.footer.select('form,input,textarea')
    links = {a['href'] for a in home.footer.select('a[href]')}
    assert {about, prefix+'/privacy', prefix+'/terms'} <= links
    assert not any(urlsplit(url).hostname in {'localhost'} for url in links)


@pytest.mark.parametrize('prefix', ['', '/en'])
def test_final_cta_analytics_follow_the_actual_destination(prefix):
    home = page(prefix or '/').select_one('main>.final-conversion')
    primary = home.select_one('.button')
    secondary = home.select_one('.text-action')
    assert primary['href'] == prefix+'/order' and primary.get('data-event') == 'order_start'
    assert secondary['href'] == 'https://t.me/TijGabumG' and secondary.get('data-event') == 'telegram_click'
    about = page(prefix+'/about').select_one('.about-page>.final-conversion')
    primary = about.select_one('.button')
    secondary = about.select_one('.text-action')
    assert primary['href'] == prefix+'/solutions' and primary.get('data-event') != 'order_start'
    assert secondary['href'] == prefix+'/contact' and secondary.get('data-event') != 'telegram_click'


@pytest.mark.parametrize('prefix', ['', '/en'])
@pytest.mark.parametrize('variant,count', [('standard', 5), ('branded', 3)])
def test_marketplace_gallery_has_real_thumbnail_buttons_and_shared_lightbox(prefix, variant, count):
    path = prefix + '/solutions/' + ('review-card' if variant == 'standard' else 'branded-review-card')
    soup = page(path)
    slides = soup.select('[data-slide]')
    thumbs = soup.select('[data-thumb-to]')
    assert len(slides) == len(thumbs) == count
    assert [int(t['data-thumb-to']) for t in thumbs] == list(range(count))
    assert len(soup.select('[data-zoom]')) == 1
    for thumb in thumbs:
        assert thumb.name == 'button' and thumb.get('type') == 'button'
        assert thumb.get('aria-label') and thumb.select_one('img[width][height]')
        img = thumb.select_one('img')
        if not img['src'].endswith('.svg'):
            assert '-160.webp' in img['src']
            with Image.open(SITE / img['src'].lstrip('/')) as decoded:
                # Derivative suffixes are responsive widths; portrait height keeps its ratio.
                assert decoded.width == 160 and decoded.height <= 214
    dialog = soup.select_one('dialog.image-lightbox')
    assert dialog and dialog.get('aria-label')
    assert dialog.select_one('[data-lightbox-prev]') and dialog.select_one('[data-lightbox-next]')
    assert len(dialog.select('[data-lightbox-to]')) == count


@pytest.mark.parametrize('prefix', ['', '/en'])
def test_messenger_radios_use_the_pinned_recognizable_brand_paths(prefix):
    soup = page(prefix+'/order')
    form = soup.select_one('.commerce-form')
    radios = form.select('input[type=radio][name=messenger]')
    assert {radio['value'] for radio in radios} == {'telegram', 'whatsapp', 'viber'}
    for radio in radios:
        label = radio.find_parent('label')
        assert label and radio.has_attr('required')
        original = BeautifulSoup((TASK/'icon-source'/f'{radio["value"]}.svg').read_text('utf-8'), 'xml')
        actual = label.select_one('svg')
        assert actual and actual.get('aria-hidden') == 'true'
        assert [p['d'] for p in actual.select('path')] == [p['d'] for p in original.select('path')]
        assert radio['value'].lower() in label.get_text().lower()
    assert form.select_one('fieldset.messenger-field legend')


def test_held_reference_media_and_legacy_evidence_do_not_leak():
    media_hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in (SITE/'assets/media').rglob('*') if p.is_file()}
    held = ROOT/'src/media/v9/06-promo-qr-vs-nfc.webp'
    assert hashlib.sha256(held.read_bytes()).hexdigest() not in media_hashes
    references = TASK/'inputs/nfc_card_v13_pack/references/current-site'
    for screenshot in references.glob('*.png'):
        assert hashlib.sha256(screenshot.read_bytes()).hexdigest() not in media_hashes
    for path in SITE.rglob('*'):
        if path.is_file() and path.suffix in {'.html', '.js', '.css', '.json'}:
            assert 'refinements/commerce-v12' not in path.read_text('utf-8')
