"""Loopback NFC CARD preview and HTTP lead boundary. All notifications are mocked."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qsl, urlencode
import argparse
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.review_http import ReviewHTTP,Request as ReviewRequest
from server.review_config import configure
from server.routing import product_redirect
import html
import io
import json
import re
import uuid
from email.parser import BytesParser
from email.policy import default

try:
    from .leads import LeadService, LeadError, MockNotifier
except ImportError:
    from leads import LeadService, LeadError, MockNotifier

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
MAX_BODY = 14 * 1024 * 1024  # Replay of an already-saved v1 logo request only.
MAX_V6_BODY = 64 * 1024


def load_redirects():
    data = json.loads((ROOT / 'src' / 'redirects.json').read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('invalid_redirect_configuration')
    for source, target in data.items():
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError('invalid_redirect_configuration')
        if (not source.startswith('/') or source.startswith('//') or
                not target.startswith('/') or target.startswith('//') or
                any(ch in source for ch in ('?', '#', '\\', '\r', '\n')) or
                any(ch in target for ch in ('?', '\\', '\r', '\n'))):
            raise ValueError('invalid_redirect_configuration')
    return data


REDIRECTS = load_redirects()


def hydrate_native_form(source, request_path, commerce, content=None):
    """Prefill only allowlisted product/query values; never reflect arbitrary HTML."""
    parsed = urlsplit(request_path)
    try:
        query = dict(parse_qsl(parsed.query[:4096], keep_blank_values=True, max_num_fields=40))
    except ValueError:
        query = {}
    routes = ['/', '/solutions', '/solutions/review-card', '/solutions/branded-review-card', '/order', '/contact',
              '/delivery-and-payment', '/warranty-and-returns', '/privacy', '/terms', '/thank-you']
    routes += ['/en' + ('' if r == '/' else r) for r in routes[:]]
    referrer = query.get('source') if query.get('source') in routes else parsed.path
    attribution = {k: v for k, v in query.items()
                   if k in {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'}
                   and len(v) <= 200}

    def fill(match):
        form = match[0]
        preset = re.search(r'\bdata-variant="([^"]*)"', form)
        variant = preset[1] if preset and preset[1] in commerce['variants'] else query.get('variant', preset[1] if preset else '')
        if variant not in commerce['interests']:
            variant = ''
        quantity = query.get('quantity', '1')
        if quantity not in commerce['quantities']:
            quantity = '1'
        if variant == 'bulk':
            quantity = 'more'
        for name, value in [('variant', variant), ('quantity', quantity)]:
            def select(m):
                options = re.sub(r'\sselected(?:="[^"]*")?', '', m[0])
                return options.replace(f'<option value="{value}"', f'<option selected value="{value}"', 1)
            form = re.sub(r'<select\b[^>]*\bname="' + name + r'"[^>]*>.*?</select>', select, form, flags=re.S)
        amount = commerce['variants'].get(variant, {}).get('prices', {}).get(quantity)
        en = parsed.path == '/en' or parsed.path.startswith('/en/')
        price = (('UAH ' + f'{amount:,}') if en else f'{amount:,}'.replace(',', ' ') + ' грн') if amount else ('Individual quote' if en else 'Індивідуальний розрахунок')
        if not variant:
            price = 'Choose a variant to see the price' if en else 'Оберіть варіант для розрахунку'
        form = re.sub(r'(<p\b[^>]*\bdata-form-price[^>]*>).*?(</p>)', lambda m: m[1] + html.escape(price) + m[2], form, flags=re.S)
        for name, value in [('displayed_price', price if variant else ''), ('source', referrer)]:
            form = re.sub(r'(<input\b[^>]*\bname="' + name + r'"[^>]*\bvalue=")[^"]*(")', lambda m: m[1] + html.escape(value, quote=True) + m[2], form)
        if attribution:
            field = '<input type="hidden" name="attribution" value="' + html.escape(json.dumps(attribution), quote=True) + '">'
            form = form.replace('</form>', field + '</form>')
        return form
    source = re.sub(r'<form class="lead-form(?: commerce-form)?".*?</form>', fill, source, flags=re.S)
    # Keep GET navigation useful without JavaScript; carry only bounded campaign fields.
    def navigation(match):
        href = html.unescape(match[1])
        target = urlsplit(href)
        if target.scheme or target.netloc or target.path not in routes or not target.path.endswith(('/order', '/solutions/review-card')):
            return match[0]
        values = dict(parse_qsl(target.query, keep_blank_values=True))
        values.update(attribution)
        if target.path.endswith('/order'):
            values['source'] = referrer
        return 'href="' + html.escape(target.path + '?' + urlencode(values) + ('#' + target.fragment if target.fragment else ''), quote=True) + '"'
    source = re.sub(r'href="([^"]*)"', navigation, source)
    product = re.search(r'data-product="(standard|branded)"', source)
    if product:
        variant=product[1];quantity=query.get('quantity','1')
        if quantity not in commerce['quantities']:quantity='1'
        en=parsed.path.startswith('/en/')
        amount=commerce['variants'][variant]['prices'].get(quantity)
        price=('UAH '+f'{amount:,}' if en else f'{amount:,}'.replace(',',' ')+' грн') if amount else ('Custom quote' if en else 'Індивідуальний розрахунок')
        source=re.sub(r'(<(?:p|span)\b[^>]*data-(?:current|sticky)-price[^>]*>).*?(</(?:p|span)>)',lambda m:m[1]+price+m[2],source,flags=re.S)
        def top_select(m):
            options=re.sub(r'\sselected(?:="[^"]*")?','',m[0])
            return options.replace(f'<option value="{quantity}"',f'<option selected value="{quantity}"',1)
        source=re.sub(r'<select\b[^>]*id="purchase-quantity"[^>]*>.*?</select>',top_select,source,flags=re.S)
    if 'class="product-order"' in source:
        variant = query.get('variant', 'standard')
        if variant not in commerce['variants']:
            variant = 'standard'
        quantity = query.get('quantity', '1')
        if quantity not in commerce['quantities']:
            quantity = '1'
        en = parsed.path.startswith('/en/')
        locale = 'en' if en else 'uk'
        def money(amount):
            return 'UAH ' + f'{amount:,}' if en else f'{amount:,}'.replace(',', ' ') + ' грн'
        prices = commerce['variants'][variant]['prices']
        total = money(prices[quantity]) if quantity in prices else 'Individual quote' if en else 'Індивідуальний розрахунок'
        def purchase(match):
            form = match[0]
            def radio(m):
                tag = re.sub(r'\schecked(?:="[^"]*")?', '', m[0])
                return tag[:-1] + (' checked>' if f'value="{variant}"' in tag else '>')
            form = re.sub(r'<input\b[^>]*\bname="variant"[^>]*>', radio, form)
            def select(m):
                options = re.sub(r'\sselected(?:="[^"]*")?', '', m[0])
                return options.replace(f'<option value="{quantity}"', f'<option selected value="{quantity}"', 1)
            form = re.sub(r'<select\b[^>]*\bname="quantity"[^>]*>.*?</select>', select, form, flags=re.S)
            for q in ('1', '2'):
                form = re.sub(r'(<dd\b[^>]*data-quantity-price="' + q + r'"[^>]*>).*?(</dd>)', lambda m: m[1] + money(prices[q]) + m[2], form)
            form = re.sub(r'(<p\b[^>]*data-product-price[^>]*>).*?(</p>)', lambda m: m[1] + total + m[2], form)
            hidden = ''.join('<input type="hidden" name="' + k + '" value="' + html.escape(v, quote=True) + '">' for k, v in attribution.items())
            return form.replace('</form>', hidden + '</form>')
        source = re.sub(r'<form class="product-order".*?</form>', purchase, source, flags=re.S)
        selected = next((v for v in (content or {}).get('variants', []) if v['id'] == variant), {})
        cta_label = ('Request a quote' if en else 'Розрахувати замовлення') if quantity == 'more' else selected.get('cta', {}).get(locale)
        name = selected.get('name', 'Branded Review Card' if variant == 'branded' else 'Review Card')
        source = re.sub(r'(<h1\b[^>]*data-variant-title[^>]*>).*?(</h1>)', lambda m: m[1] + html.escape(name) + m[2], source)
        for attribute, tag, value in [('data-variant-description', 'p', selected.get('description', {}).get(locale)), ('data-product-cta', 'button', cta_label)]:
            if value:
                source = re.sub(r'(<' + tag + r'\b[^>]*' + attribute + r'[^>]*>).*?(</' + tag + '>)', lambda m: m[1] + html.escape(value) + m[2], source)
        if variant == 'branded':
            source = re.sub(r'(<p\b[^>]*data-branded-note) hidden', r'\1', source)
        def sticky(match):
            block = match[0]
            path = ('/en' if en else '') + '/order'
            href = path + '?' + urlencode({'variant': variant, 'quantity': quantity, 'source': parsed.path, **attribution})
            return re.sub(r'(<a href=")[^"]*(" class="button[^>]*>).*?(</a>)', lambda m: m[1] + html.escape(href, quote=True) + m[2] + html.escape(cta_label or 'NFC CARD') + m[3], block, count=1)
        source = re.sub(r'<div class="sticky-order">.*?</div>', sticky, source, flags=re.S)
    return source


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_fields')
        result[key] = value
    return result


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def translate_path(self, value):
        relative = unquote(urlsplit(value).path).lstrip('/')
        target = (SITE / relative).resolve()
        if not target.is_relative_to(SITE.resolve()):
            return str(SITE / '__missing__')
        if target.is_dir():
            target = target / 'index.html'
        return str(target)

    def end_headers(self):
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        super().end_headers()

    def response_json(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        if status == 429:
            self.send_header('Retry-After', '60')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def redirect(self):
        path = unquote(urlsplit(self.path).path)
        target = product_redirect(self.path) or REDIRECTS.get(path.rstrip('/'))
        if not target:
            return False
        self.send_response(301)
        self.send_header('Location', target)  # Fixed config only; query is deliberately discarded.
        self.send_header('Content-Length', '0')
        self.end_headers()
        return True

    def review_request(self):
        if not ReviewHTTP.handles(self.path):return False
        dispatcher=getattr(self.server,'reviews',None)
        if dispatcher is None:
            self.close_connection=True;self.response_json(503,{'ok':False,'code':'reviews_not_configured'});return True
        raw=b''
        if self.command=='POST':
            lengths=self.headers.get_all('Content-Length',[])
            if self.headers.get('Transfer-Encoding') or len(lengths)!=1 or not re.fullmatch(r'[0-9]{1,9}',lengths[0]):
                self.close_connection=True;self.response_json(400,{'ok':False,'code':'invalid_length'});return True
            size=int(lengths[0])
            if not 0<size<=dispatcher.runtime.service.images.max_bytes+65536:
                self.close_connection=True;self.response_json(413,{'ok':False,'code':'payload_too_large'});return True
            self.connection.settimeout(15)
            try:raw=self.rfile.read(size)
            except (OSError,TimeoutError):
                self.close_connection=True;self.response_json(408,{'ok':False,'code':'request_timeout'});return True
            if len(raw)!=size:
                self.close_connection=True;self.response_json(400,{'ok':False,'code':'incomplete_payload'});return True
        response=dispatcher.dispatch(ReviewRequest(self.command,self.path,{k.lower():v for k,v in self.headers.items()},raw,self.client_address[0]))
        self.send_response(response.status)
        for key,value in response.headers.items():self.send_header(key,value)
        self.send_header('Content-Length',str(len(response.body)));self.end_headers()
        if self.command!='HEAD':self.wfile.write(response.body)
        return True

    def do_GET(self):
        if self.review_request():return
        if self.redirect():
            return
        if urlsplit(self.path).path.startswith('/api/'):
            return self.response_json(404, {'ok': False, 'code': 'not_found'})
        return super().do_GET()

    def do_HEAD(self):
        if self.review_request():return
        if self.redirect():
            return
        if urlsplit(self.path).path.startswith('/api/'):
            return self.response_json(404, {'ok': False, 'code': 'not_found'})
        return super().do_HEAD()

    def send_head(self):
        target = Path(self.translate_path(self.path))
        if target.is_file() and target.suffix == '.html':
            source = target.read_text(encoding='utf-8')
            # Per-render non-PII token makes native form back/retry idempotent too.
            source = re.sub(r'(<input\b[^>]*\bname="requestToken"[^>]*\bvalue=")[^"]*(")',
                            lambda m: m[1] + str(uuid.uuid4()) + m[2], source)
            content_file = SITE / 'assets/content.json'
            content = json.loads(content_file.read_text('utf-8')) if content_file.is_file() else None
            source = hydrate_native_form(source, self.path, self.server.leads.commerce, content)
            data = source.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            return io.BytesIO(data)
        return super().send_head()

    def read_payload(self):
        if self.headers.get('Transfer-Encoding'):
            self.close_connection = True
            raise LeadError(400, 'unsupported_transfer_encoding')
        lengths = self.headers.get_all('Content-Length', [])
        if len(lengths) != 1 or not re.fullmatch(r'[0-9]+', lengths[0]):
            self.close_connection = True
            raise LeadError(400, 'invalid_length')
        size = int(lengths[0])
        if size <= 0 or size > MAX_BODY:
            self.close_connection = True
            raise LeadError(413, 'payload_too_large')
        self.connection.settimeout(15)
        try:
            raw = self.rfile.read(size)
        except (OSError, TimeoutError):
            self.close_connection = True
            raise LeadError(408, 'request_timeout') from None
        if len(raw) != size:
            self.close_connection = True
            raise LeadError(400, 'incomplete_payload')
        content_type = self.headers.get('Content-Type', '')
        mime = content_type.split(';', 1)[0].strip().lower()
        native = mime in {'multipart/form-data', 'application/x-www-form-urlencoded'}
        if mime == 'application/json':
            payload = json.loads(raw, object_pairs_hook=no_duplicate_keys,
                                 parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        elif native:
            if size > MAX_V6_BODY:
                raise LeadError(413, 'payload_too_large')
            if mime == 'application/x-www-form-urlencoded':
                pairs = parse_qsl(raw.decode('utf-8'), keep_blank_values=True,
                                  max_num_fields=40, encoding='utf-8', errors='strict')
            else:
                message = BytesParser(policy=default).parsebytes(
                    ('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + raw)
                if not message.is_multipart():
                    raise LeadError(400, 'invalid_payload')
                pairs = []
                for part in message.iter_parts():
                    name = part.get_param('name', header='content-disposition')
                    if not name:
                        continue
                    if part.get_filename() is not None or part.is_multipart():
                        raise LeadError(422, 'files_not_supported', {'logo': 'logo'})
                    pairs.append((name, part.get_payload(decode=True).decode('utf-8')))
                if len(pairs) > 40:
                    raise LeadError(400, 'invalid_payload')
            payload = no_duplicate_keys(pairs)
            payload['contractVersion'] = 6 if payload.get('contractVersion') == '6' else 0
            payload['consent'] = payload.get('consent') in {'yes', 'on', 'true'}
            payload['differentContact'] = payload.get('differentContact') in {'yes', 'on', 'true'}
            if 'attribution' in payload:
                payload['attribution'] = json.loads(payload['attribution'], object_pairs_hook=no_duplicate_keys)
        else:
            raise LeadError(415, 'unsupported_content_type')
        if isinstance(payload, dict) and payload.get('contractVersion') == 6 and size > MAX_V6_BODY:
            raise LeadError(413, 'payload_too_large')
        return payload, native

    def native_success(self, value, locale):
        item = value['receipt']
        en = locale == 'en'
        title = 'Test request saved locally' if en else 'Тестову заявку збережено локально'
        variant = {'standard': 'Review Card', 'branded': 'Branded Review Card',
                   'bulk': 'Business cards' if en else 'Картки для бізнесу',
                   'consultation': 'Consultation' if en else 'Консультація'}.get(item['variant'], '')
        quote = item.get('quote')
        amount = ''
        if quote:
            amount = (str(quote['amount']) + ' UAH' if quote['status'] == 'fixed'
                      else 'Custom quote' if en else 'Індивідуальний прорахунок')
        body = (
            '<!doctype html><html lang="' + ('en' if en else 'uk') + '"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>' + title + '</title>'
            '<link rel="stylesheet" href="/assets/style.css"><main class="section prose-page">'
            '<h1>' + title + '</h1><p>' +
            ('No notifications were sent.' if en else 'Повідомлення не надсилалися.') +
            '</p><p>' + html.escape(item['id']) + '</p><p>' + html.escape(variant) +
            '</p><p>' + html.escape(str(item.get('quantity') or '')) + '</p><p>' +
            html.escape(amount) + '</p><a class="button" href="' +
            ('/en/solutions' if en else '/solutions') + '">' +
            ('Back to catalog' if en else 'Повернутися до каталогу') + '</a></main></html>'
        ).encode()
        self.send_response(200 if item['duplicate'] else 201)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def native_error(self, error, locale):
        en = locale == 'en'
        title = 'Check the request details' if en else 'Перевірте дані заявки'
        message = ('Use your browser’s Back button to return to the form and correct the fields.'
                   if en else 'Поверніться до форми кнопкою браузера «Назад» і виправте поля.')
        names = {
            'name': ('Ім’я', 'Name'), 'phone': ('Номер телефону', 'Phone number'),
            'messenger': ('Зручний месенджер', 'Preferred messenger'),
            'messengerContact': ('Інший контакт', 'Different contact'),
            'differentContact': ('Інший контакт', 'Different contact'),
            'variant': ('Варіант картки', 'Card variant'), 'quantity': ('Кількість', 'Quantity'),
            'maps': ('Посилання на Google Maps', 'Google Maps link'),
            'businessUrl': ('Посилання на бізнес', 'Business page link'),
            'consent': ('Згода з обробкою даних', 'Privacy consent'),
        }
        if error.status == 429:
            message = ('Too many attempts. Wait a minute, then return to your form.' if en else
                       'Забагато спроб. Зачекайте хвилину та поверніться до форми.')
        fields = ''.join('<li>' + names[key][int(en)] + '</li>' for key in error.fields if key in names)
        body = ('<!doctype html><html lang="' + ('en' if en else 'uk') + '">'
                '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<meta name="robots" content="noindex,nofollow"><title>' + title + '</title>'
                '<link rel="stylesheet" href="/assets/style.css"><main class="section prose-page">'
                '<h1>' + title + '</h1><p>' + message + '</p><ul>' + fields + '</ul></main></html>').encode()
        self.send_response(error.status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        if error.status == 429:
            self.send_header('Retry-After', '60')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.review_request():return
        if urlsplit(self.path).path != '/api/leads':
            self.close_connection = True
            return self.response_json(404, {'ok': False, 'code': 'not_found'})
        port = self.server.server_port
        if (self.headers.get('Origin') != f'http://127.0.0.1:{port}' or
                self.headers.get('Host') != f'127.0.0.1:{port}'):
            self.close_connection = True
            return self.response_json(403, {'ok': False, 'code': 'origin_rejected'})
        native, payload = False, None
        try:
            payload, native = self.read_payload()
            result = self.server.leads.submit(payload, self.client_address[0])
            if native:
                return self.native_success(result, payload.get('locale'))
            return self.response_json(200 if result['receipt']['duplicate'] else 201, result)
        except LeadError as exc:
            if native and isinstance(payload, dict):
                return self.native_error(exc, payload.get('locale'))
            result = {'ok': False, 'code': exc.code}
            if exc.fields:
                result['errors'] = exc.fields
            self.response_json(exc.status, result)
        except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError):
            self.response_json(400, {'ok': False, 'code': 'invalid_payload'})
        except Exception:
            self.response_json(503, {'ok': False, 'code': 'storage_unavailable'})

    def log_message(self, *args):
        pass  # No query strings, request payloads or personal details in HTTP logs.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--db', type=Path, default=ROOT / 'private' / 'test-leads.sqlite')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    if os.environ.get('NFC_DATABASE_URL'):
        runtime=configure()
        from server.commerce_repository import PostgresLeadService
        server.leads=PostgresLeadService(runtime.service.repo,secret=runtime.service.secret,mode=runtime.mode)
        server.reviews=ReviewHTTP(runtime,lambda lang:(ROOT/'server/templates'/f'admin-{lang}.html').read_text('utf-8'))
    else:server.leads = LeadService(args.db, telegram=MockNotifier())
    print(f'NFC CARD Local: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
