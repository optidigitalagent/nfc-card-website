"""Release regressions. HTTPS/approval fixtures are synthetic and never deployed."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import pytest

from server.publication import PublicationPolicy, PREVIEW, INDEXABLE, PUBLIC_ROUTES, content_hash
from server.wsgi import Application
from test_v12_reviews import repo, service, http

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://preview.nfc.example'


@pytest.fixture
def source(tmp_path):
    shutil.copytree(ROOT / 'src', tmp_path / 'src')
    dest = tmp_path / 'refinements/instagram-v18'
    dest.mkdir(parents=True)
    shutil.copyfile(ROOT / 'refinements/instagram-v18/routes.json', dest / 'routes.json')
    return tmp_path


def build(source, **values):
    env = {k: v for k, v in os.environ.items() if not k.startswith('NFC_')}
    env.update(NFC_ENV='production', NFC_PUBLIC_ORIGIN=ORIGIN, **values)
    return subprocess.run(['node', 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)


def authorize_synthetic_content(source, final_documents=True):
    """Only a disposable test copy is approved. Real repository approval stays false."""
    model = source / 'src/model.mjs'
    text = model.read_text().replace('"publicationReady": false', '"publicationReady": true')
    for key in ('identity', 'address', 'registration'):
        text = text.replace(f'"{key}": null', f'"{key}": "Synthetic test-only legal {key}"')
    text = text.replace('"privacyApproved": false', '"privacyApproved": true').replace('"termsApproved": false', '"termsApproved": true')
    model.write_text(text)
    flags_path = source / 'src/verification.json'
    flags = json.loads(flags_path.read_text())
    for key in ('legal_identity_confirmed', 'warranty_policy_confirmed', 'personalized_returns_policy_confirmed'):
        flags[key] = True
    flags_path.write_text(json.dumps(flags))
    if final_documents:
        builder = source / 'src/build.mjs'
        lines = builder.read_text().splitlines()
        lines = ["function legalPage(route){return '<h1>Synthetic final policy fixture</h1><p>Only for isolated release regression tests.</p>';}" if line.startswith('function legalPage(') else line for line in lines]
        builder.write_text('\n'.join(lines).replace('Чернетка документа до погодження власником.', 'Synthetic final policy fixture.').replace('Draft document awaiting owner approval.', 'Synthetic final policy fixture.'))
    approval = {'schemaVersion': 1, 'ownerAuthorizedIndexing': True, 'publicationInputsConfirmed': True,
                'approvalReference': 'Synthetic test-only approval; never an owner authorization',
                'reviewedContentSha256': content_hash(source)}
    (source / 'src/publication-approval.json').write_text(json.dumps(approval))


def test_https_preview_metadata_and_crawl_boundaries(source):
    result = build(source)
    assert result.returncode == 0, result.stderr
    pages = list((source / 'site').rglob('*.html'))
    assert len(pages) == 34
    for page in pages:
        soup = BeautifulSoup(page.read_text(), 'html.parser')
        assert soup.select_one('meta[name=robots]')['content'] == 'noindex,nofollow'
        urls = [item['href'] for item in soup.select('link[rel=canonical],link[hreflang]')]
        urls += [soup.select_one('meta[property="og:url"]')['content']]
        assert all(urlsplit(url).scheme == 'https' and urlsplit(url).netloc == 'preview.nfc.example' for url in urls)
        assert '127.0.0.1' not in str(soup.select('script[type="application/ld+json"]'))
    assert (source / 'site/robots.txt').read_text() == 'User-agent: *\nDisallow: /\n'
    sitemap = BeautifulSoup((source / 'site/sitemap.xml').read_text(), 'xml')
    urls = [item.text for item in sitemap.find_all('loc')]
    assert len(urls) == 22 and all(url.startswith(ORIGIN + '/') for url in urls)
    assert all(not any(part in url for part in ('/order', '/contact', '/reviews/new', '/thank-you', '/privacy', '/terms', '/admin', '/api')) for url in urls)
    assert PublicationPolicy.from_build(source, SimpleNamespace(mode='production', origin=ORIGIN), {}).mode == PREVIEW


@pytest.mark.parametrize('origin', ['', 'http://127.0.0.1:8765', 'https://localhost', 'https://127.0.0.1',
                                    'https://[::1]', 'https://private.internal', 'https://host.example/path',
                                    'https://host.example?x=1', 'https://host.example#fragment', 'https://user@host.example',
                                    'https://localhost.', 'https://private.localhost.', 'https://private.internal.'])
def test_production_origin_rejected(source, origin):
    env = dict(os.environ, NFC_ENV='production', NFC_PUBLIC_ORIGIN=origin)
    result = subprocess.run(['node', 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert result.returncode != 0


def test_indexing_cannot_be_enabled_with_env_flag_alone(source):
    result = build(source, NFC_PUBLICATION_MODE=INDEXABLE)
    assert result.returncode != 0 and 'Indexing blocked' in result.stderr


def test_unknown_publication_mode_rejected(source):
    result = build(source, NFC_PUBLICATION_MODE='INDEX')
    assert result.returncode != 0 and 'Invalid NFC_PUBLICATION_MODE' in result.stderr


def test_indexing_requires_final_documents_even_with_content_receipt(source):
    authorize_synthetic_content(source, final_documents=False)
    result = build(source, NFC_PUBLICATION_MODE=INDEXABLE)
    assert result.returncode != 0 and 'still a draft' in result.stderr


def test_indexable_build_and_runtime_allow_only_public_routes(source):
    authorize_synthetic_content(source)
    result = build(source, NFC_PUBLICATION_MODE=INDEXABLE)
    assert result.returncode == 0, result.stderr
    policy = PublicationPolicy.from_build(source, SimpleNamespace(mode='production', origin=ORIGIN), {'NFC_PUBLICATION_MODE': INDEXABLE})
    assert policy.indexable_routes == PUBLIC_ROUTES
    for page in (source / 'site').rglob('*.html'):
        route = '/' + page.parent.relative_to(source / 'site').as_posix()
        if route == '/.': route = '/'
        soup = BeautifulSoup(page.read_text(), 'html.parser')
        assert soup.select_one('meta[name=robots]')['content'] == ('index,follow' if route in PUBLIC_ROUTES else 'noindex,nofollow')
        assert policy.robots(route, 200, 'text/html') == ('index, follow' if route in PUBLIC_ROUTES else 'noindex, nofollow')
    for route in ('/admin/login', '/en/admin/reviews', '/api/reviews', '/api/admin/session', '/api/leads', '/thank-you', '/en/thank-you', '/reviews/new', '/order', '/contact', '/healthz', '/about/index.html'):
        assert policy.robots(route, 200, 'text/html') == 'noindex, nofollow'
    assert policy.robots('/about', 404, 'text/html') == 'noindex, nofollow'
    sitemap = BeautifulSoup((source / 'site/sitemap.xml').read_text(), 'xml')
    assert {urlsplit(item.text).path for item in sitemap.find_all('loc')} == PUBLIC_ROUTES
    robots = (source / 'site/robots.txt').read_text()
    assert 'Disallow: /admin\n' in robots and 'Disallow: /api\n' in robots
    assert 'Sitemap: ' + ORIGIN + '/sitemap.xml' in robots


@pytest.mark.parametrize('change', ['origin', 'mode', 'source', 'private_route', 'approval'])
def test_production_rejects_mismatched_or_unapproved_build(source, change):
    authorize_synthetic_content(source)
    assert build(source, NFC_PUBLICATION_MODE=INDEXABLE).returncode == 0
    runtime = SimpleNamespace(mode='production', origin=ORIGIN)
    env = {'NFC_PUBLICATION_MODE': INDEXABLE}
    if change == 'origin': runtime.origin = 'https://another.nfc.example'
    if change == 'mode': env['NFC_PUBLICATION_MODE'] = PREVIEW
    if change == 'source':
        p = source / 'src/model.mjs'; p.write_text(p.read_text() + '\n// changed after approval\n')
    if change == 'private_route':
        p = source / 'server/templates/publication.json'; d = json.loads(p.read_text()); d['indexableRoutes'].append('/admin/reviews'); p.write_text(json.dumps(d))
    if change == 'approval':
        p = source / 'src/publication-approval.json'; d = json.loads(p.read_text()); d['ownerAuthorizedIndexing'] = False; p.write_text(json.dumps(d))
    with pytest.raises(ValueError): PublicationPolicy.from_build(source, runtime, env)


def call(app, route, host='127.0.0.1:8767', method='GET'):
    captured = []
    body = b''.join(app({'REQUEST_METHOD': method, 'PATH_INFO': route, 'HTTP_HOST': host,
                        'wsgi.input': io.BytesIO()}, lambda s, h: captured.append((s, dict(h)))))
    return captured[0], body


def test_wsgi_caches_only_static_assets_and_protects_form_tokens(http):
    app = Application(http.runtime)
    (status, headers), first = call(app, '/order')
    assert status == '200 OK' and 'no-store' in headers['Cache-Control'] and 'noindex' in headers['X-Robots-Tag']
    _, second = call(app, '/order')
    a = BeautifulSoup(first, 'html.parser').select_one('[name=requestToken]')['value']
    b = BeautifulSoup(second, 'html.parser').select_one('[name=requestToken]')['value']
    assert a != b
    for route in ('/api/reviews', '/admin/login', '/healthz', '/missing-route'):
        (_, headers), _ = call(app, route)
        assert 'no-store' in headers['Cache-Control'] and 'noindex' in headers['X-Robots-Tag']
    (status, headers), _ = call(app, '/assets/style.css')
    assert status == '200 OK' and headers['Cache-Control'] == 'public, max-age=3600'
    (status, headers), body = call(app, '/healthz')
    assert status == '200 OK' and json.loads(body)['database'] == 'ready'
    assert json.loads(body)['storage'] == 'configured_not_probed'


@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_railway_health_host_is_limited_to_read_only_probe(http, monkeypatch, method):
    app = Application(http.runtime)
    (status, headers), body = call(app, '/healthz', 'healthcheck.railway.app', method)
    assert status == '200 OK'
    assert 'no-store' in headers['Cache-Control'] and 'noindex' in headers['X-Robots-Tag']
    assert (body == b'') if method == 'HEAD' else json.loads(body)['database'] == 'ready'
    for host, route, verb in [('attacker.example', '/healthz', method),
                             ('healthcheck.railway.app', '/healthz', 'POST'),
                             *[('healthcheck.railway.app', p, method) for p in
                               ('/', '/order', '/admin/login', '/api/admin/session', '/api/leads')]]:
        (status, _), _ = call(app, route, host, verb)
        assert status == '403 Forbidden', (route, verb, status)
    monkeypatch.setattr(http.runtime.service.repo, 'ready', lambda: False)
    (status, _), body = call(app, '/healthz', 'healthcheck.railway.app', method)
    assert status == '503 Service Unavailable'


def test_missing_configuration_fails_honestly_without_exposing_details(monkeypatch):
    import server.wsgi as wsgi
    monkeypatch.setattr(wsgi, '_configured', None)
    monkeypatch.setattr(wsgi, 'create_application', lambda: (_ for _ in ()).throw(ValueError('synthetic confidential error')))
    (status, headers), body = call(wsgi.application, '/')
    assert status == '503 Service Unavailable'
    assert body == b'{"ok":false,"code":"service_unavailable"}'
    assert 'no-store' in headers['Cache-Control'] and 'noindex' in headers['X-Robots-Tag']
