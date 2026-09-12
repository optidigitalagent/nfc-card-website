"""HTTP tests use a loopback server, synthetic site files, new SQLite and mocks."""
import http.client
import json
import re
import sys
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import preview
from preview import Handler, REDIRECTS, MAX_BODY, MAX_V6_BODY
from leads import LeadService, MockNotifier
from test_leads import payload, stored


@pytest.fixture
def server(tmp_path, monkeypatch):
    site = tmp_path / 'synthetic-site'
    site.mkdir()
    markup = ('<!doctype html><html lang="uk"><title>Synthetic HTTP fixture</title>'
              '<form action="/api/leads" method="post">'
              '<input type="hidden" name="requestToken" value=""></form></html>')
    (site / 'index.html').write_text(markup, encoding='utf-8')
    (site / 'order').mkdir()
    (site / 'order' / 'index.html').write_text(markup, encoding='utf-8')
    monkeypatch.setattr(preview, 'SITE', site)
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    http.leads = LeadService(tmp_path / 'synthetic-http.sqlite', telegram=MockNotifier())
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield http
    http.shutdown()
    http.server_close()
    thread.join(timeout=3)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def request(server, data=None, headers=None, path='/api/leads', method=None, raw=None):
    origin = f'http://127.0.0.1:{server.server_port}'
    headers = {'Content-Type': 'application/json', 'Origin': origin, **(headers or {})}
    body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(origin + path, data=body, headers=headers, method=method)
    try:
        response = urllib.request.build_opener(NoRedirect).open(req, timeout=4)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, response.headers, response.read()


def test_http_success_then_duplicate(server):
    data = payload()
    a, b = request(server, data), request(server, data)
    assert a[0] == 201 and b[0] == 200
    first, retry = json.loads(a[2]), json.loads(b[2])
    assert first['ok'] and first['receipt']['id'] == retry['receipt']['id']
    assert first['receipt']['quote']['amount'] == 1500 and retry['receipt']['duplicate']
    assert len(server.leads.telegram.calls) == 1
    for private in ['phone', 'name', 'comment', 'businessUrl', 'attribution', 'requestToken']:
        assert private not in json.dumps(first)


@pytest.mark.parametrize('origin', ['https://evil.test', 'null', 'http://localhost:8765', ''])
def test_cross_origin_requests_rejected(server, origin):
    assert request(server, payload(), {'Origin': origin})[0] == 403


def test_dns_rebinding_host_rejected(server):
    assert request(server, payload(), {'Host': 'evil.test'})[0] == 403


@pytest.mark.parametrize('path', [
    '/api/leads', '/private/test-leads.sqlite', '/../private/test-leads.sqlite',
    '/%2e%2e/private/test-leads.sqlite', '/server/leads.py', '/.env',
])
@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_private_records_and_source_not_exposed(server, path, method):
    status, _, body = request(server, path=path, method=method)
    assert status == 404
    if method == 'HEAD':
        assert body == b''


def test_security_headers(server):
    status, headers, _ = request(server, path='/')
    assert status == 200 and headers['X-Content-Type-Options'] == 'nosniff'
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
    assert headers['X-Robots-Tag'] == 'noindex, nofollow'
    assert headers['Cache-Control'] == 'no-store'
    assert 'Access-Control-Allow-Origin' not in headers


@pytest.mark.parametrize('source,target', list(REDIRECTS.items()))
@pytest.mark.parametrize('method', ['GET', 'HEAD'])
@pytest.mark.parametrize('suffix', ['', '/', '?synthetic=private'])
def test_retired_routes_return_real_permanent_redirect(server, source, target, method, suffix):
    status, headers, body = request(server, path=source + suffix, method=method)
    assert status == 301 and headers['Location'] == target
    assert headers['Content-Length'] == '0' and body == b''
    assert 'synthetic' not in headers['Location']


def test_unknown_url_cannot_choose_redirect_target(server):
    status, headers, _ = request(server, path='/order?next=https://evil.test')
    assert status == 200 and 'Location' not in headers


@pytest.mark.parametrize('data,status', [
    ({'contractVersion': 6, 'locale': []}, 400),
    ([], 400), (None, 400), ('invalid', 400),
])
def test_json_shape_has_controlled_client_error(server, data, status):
    result = request(server, raw=json.dumps(data).encode(), method='POST')
    assert result[0] == status
    assert json.loads(result[2])['ok'] is False


def test_non_scalar_locale_is_422_with_valid_token(server):
    assert request(server, payload(locale=[]))[0] == 422


@pytest.mark.parametrize('raw', [
    b'{broken', b'{"contractVersion":6,"contractVersion":6}', b'{"amount":NaN}',
    b'[' * 1500 + b']' * 1500,
])
def test_malformed_or_ambiguous_json_rejected(server, raw):
    status, _, body = request(server, raw=raw, method='POST')
    assert status == 400 and json.loads(body)['ok'] is False


def test_unsupported_content_type(server):
    assert request(server, raw=b'hello', headers={'Content-Type': 'text/plain'})[0] == 415


def test_v6_payload_size_limit(server):
    data = payload(displayed_price='x' * MAX_V6_BODY)
    assert request(server, data)[0] == 413
    with server.leads.connect() as db:
        assert db.execute('SELECT count(*) FROM leads').fetchone()[0] == 0


def test_oversized_length_rejected_without_reading_body(server):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
    try:
        connection.putrequest('POST', '/api/leads')
        connection.putheader('Origin', f'http://127.0.0.1:{server.server_port}')
        connection.putheader('Content-Type', 'application/json')
        connection.putheader('Content-Length', str(MAX_BODY + 1))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413 and json.loads(response.read())['ok'] is False
    finally:
        connection.close()


def test_chunked_body_rejected(server):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
    try:
        connection.request('POST', '/api/leads', body=b'0\r\n\r\n', headers={
            'Origin': f'http://127.0.0.1:{server.server_port}',
            'Transfer-Encoding': 'chunked', 'Content-Type': 'application/json'})
        response = connection.getresponse()
        assert response.status == 400
        response.read()
    finally:
        connection.close()


def test_storage_failure_is_not_success_or_private_error(server):
    class Broken:
        def submit(self, *_):
            raise OSError('synthetic private detail must not leak')
    server.leads = Broken()
    status, _, body = request(server, payload())
    assert status == 503 and json.loads(body)['ok'] is False
    assert b'private detail' not in body


def test_native_form_get_supplies_stable_submit_token_without_pii(server):
    a = request(server, path='/order')[2].decode()
    b = request(server, path='/order')[2].decode()
    first = re.search(r'name="requestToken" value="([^"]+)"', a)[1]
    second = re.search(r'name="requestToken" value="([^"]+)"', b)[1]
    assert first != second and len(first) == len(second) == 36
    data = payload(requestToken=first)
    native = {k: str(v) for k, v in data.items() if k != 'attribution'}
    native.update(consent='yes', differentContact='false')
    body = urlencode(native).encode()
    a = request(server, raw=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    b = request(server, raw=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert a[0] == 201 and b[0] == 200
    assert 'text/html' in a[1]['Content-Type']
    text = a[2].decode()
    assert '1500 UAH' in text and 'Review Card' in text
    assert data['name'] not in text and data['phone'] not in text
    assert 'NFC-' in text
    with server.leads.connect() as db:
        assert db.execute('SELECT count(*) FROM leads').fetchone()[0] == 1
    assert len(server.leads.telegram.calls) == 1


def test_multipart_file_is_rejected(server):
    raw = (b'--synthetic\r\nContent-Disposition: form-data; name="logo"; filename="x.png"'
           b'\r\nContent-Type: image/png\r\n\r\nnot-an-image\r\n--synthetic--\r\n')
    status, _, body = request(server, raw=raw,
                             headers={'Content-Type': 'multipart/form-data; boundary=synthetic'})
    assert status == 422 and json.loads(body)['code'] == 'files_not_supported'


def test_duplicate_native_fields_are_rejected(server):
    status, _, body = request(server, raw=b'consent=yes&consent=no',
                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert status == 400 and json.loads(body)['ok'] is False


@pytest.mark.parametrize('locale,label', [('uk', 'Посилання на бізнес'), ('en', 'Business page link')])
def test_native_validation_is_localized_and_does_not_echo_pii(server, locale, label):
    data = payload(locale=locale, variant='branded', businessUrl='javascript:invalid')
    native = {k: str(v) for k, v in data.items() if k != 'attribution'}
    native.update(consent='yes', differentContact='false')
    status, headers, body = request(server, raw=urlencode(native).encode(),
                                   headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert status == 422 and 'text/html' in headers['Content-Type']
    text = body.decode()
    assert label in text and data['name'] not in text and data['phone'] not in text


def test_nonfield_rate_error_does_not_return_empty_validation_map(server):
    server.leads.rate_limit = 1
    request(server, payload())
    status, _, body = request(server, payload())
    value = json.loads(body)
    assert status == 429 and value['code'] == 'rate_limited' and 'errors' not in value
