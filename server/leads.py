"""V6 durable lead boundary. No dotenv, implicit transports or private read API."""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit, urlunsplit

try:
    from .errors import LeadError
    from .legacy import normalize_legacy, maps_url, clean_logo, valid_contact, legacy_telegram_message
    from .pricing import COMMERCE_PATH, load_commerce, canonical_quote
except ImportError:
    from errors import LeadError
    from legacy import normalize_legacy, maps_url, clean_logo, valid_contact, legacy_telegram_message
    from pricing import COMMERCE_PATH, load_commerce, canonical_quote

CONSENT_VERSION = 'nfc-card-local-privacy-draft-v6'
VARIANTS = {'standard', 'branded', 'bulk', 'consultation', 'instagram'}
QUANTITIES = {'1', '2', 'more'}
MESSENGERS = {'telegram', 'whatsapp', 'viber'}
LIMITS = {'name': 120, 'phone': 80, 'messengerContact': 250, 'business': 200,
          'maps': 2048, 'businessUrl': 2048, 'comment': 2000, 'source': 250}
ALLOWED = set(LIMITS) | {'contractVersion', 'requestToken', 'variant', 'quantity',
                       'messenger', 'differentContact', 'consent', 'locale',
                       'attribution', 'website', 'displayed_price', 'logo',
                       'productSchemaVersion', 'product_id', 'offer', 'instagramUrl'}
ATTRIBUTION_KEYS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content',
                    'utm_term', 'referrer', 'landing'}
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def fingerprint(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def request_key(payload):
    """A stable client UUID is a nonce; server owns its namespaced storage key."""
    if not isinstance(payload, dict):
        return None
    if type(payload.get('contractVersion')) is int and payload['contractVersion'] == 6:
        token = payload.get('requestToken')
        if not isinstance(token, str) or len(token) != 36:
            return None
        try:
            parsed = uuid.UUID(token)
        except ValueError:
            return None
        if parsed.version != 4 or str(parsed) != token.lower():
            return None
        return 'v6:' + hashlib.sha256(parsed.bytes).hexdigest()
    if 'contractVersion' not in payload:
        key = payload.get('idempotencyKey')
        if isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9_-]{16,80}', key):
            return key
    return None


def normalized_phone(value):
    if not isinstance(value, str) or not re.fullmatch(r'\+?[0-9 ()-]+', value.strip()):
        return None
    digits = re.sub(r'[^0-9]', '', value)
    if not 7 <= len(digits) <= 15:
        return None
    # A supplied Ukrainian domestic number has one unambiguous international form.
    if len(digits) == 10 and digits.startswith('0'):
        digits = '38' + digits
    return '+' + digits


def business_url(value):
    if not isinstance(value, str) or re.search(r'[\s\\]', value):
        return False
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password:
            return False
        if not parsed.hostname or parsed.port not in (None, 80, 443):
            return False
        host = parsed.hostname.encode('idna').decode('ascii')
        return bool('.' in host and re.fullmatch(r'[A-Za-z0-9.-]{1,253}', host))
    except (ValueError, UnicodeError):
        return False


def instagram_profile_url(value):
    if not isinstance(value, str) or len(value) > 250:
        return None
    match = re.fullmatch(r'https://(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})/?', value, re.IGNORECASE | re.ASCII)
    if not match:
        return None
    name = match.group(1).lower()
    reserved = {'p', 'reel', 'reels', 'stories', 'explore', 'accounts', 'direct', 'about',
                'legal', 'developer', 'developers', 'web', 'api', 'challenge', 'oauth', 'tv'}
    if name.startswith('.') or name.endswith('.') or '..' in name or name in reserved:
        return None
    return 'https://www.instagram.com/' + name + '/'


def instagram_telegram_message(lead_id, created, lead):
    # Private notifier only, called after durable lead/outbox commit. Never logged.
    lines = ['NEW NFC CARD LEAD', 'Product: NFC Instagram Card', 'SKU: NFC-IG-READY',
             'Offer: ready', f'Order ID: {lead_id}',
             f'Created: {datetime.fromtimestamp(created, timezone.utc).isoformat()}',
             f'Language: {lead["locale"]}', f'Quantity: {lead["quantity"]}',
             f'Canonical price: {lead["quote"]["amount"]} UAH',
             f'Instagram profile: {lead["instagramUrl"]}',
             f'Name: {lead["name"]}', f'Phone: {lead["phone"]}',
             f'Preferred messenger: {lead["messenger"]}', f'Comment: {lead["comment"]}',
             f'Source page: {lead["source"]}',
             f'Consent: true; {lead["consentVersion"]}; {lead["consentAcceptedAt"]}']
    message = '\n'.join(lines)
    return message.encode('utf-8')[:3900].decode('utf-8', errors='ignore')


def normalize(payload):
    """Normalize intent only. No time, quote, request token or client price enters its hash."""
    if not isinstance(payload, dict):
        raise LeadError(400, 'invalid_payload')
    if payload.get('website'):
        raise LeadError(422, 'spam_rejected')
    if type(payload.get('contractVersion')) is not int or payload['contractVersion'] != 6:
        raise LeadError(422, 'contract_version')
    key = request_key(payload)
    if not key:
        raise LeadError(400, 'invalid_request_token', {'requestToken': 'requestToken'})
    if set(payload) - ALLOWED:
        raise LeadError(422, 'unsupported_fields')
    if payload.get('logo') is not None:
        raise LeadError(422, 'files_not_supported', {'logo': 'logo'})

    result = {'contractVersion': 6}
    errors = {}
    for field, limit in LIMITS.items():
        value = payload.get(field, '')
        if not isinstance(value, str) or len(value) > limit:
            errors[field] = field
        else:
            result[field] = CONTROL.sub('', value).strip()
    for field, allowed in [('locale', {'uk', 'en'}), ('variant', VARIANTS),
                           ('quantity', QUANTITIES), ('messenger', MESSENGERS)]:
        value = payload.get(field)
        if not isinstance(value, str) or value not in allowed:
            errors[field] = field
        else:
            result[field] = value
    if not result.get('name'):
        errors['name'] = 'name'
    phone = normalized_phone(result.get('phone'))
    if phone is None:
        errors['phone'] = 'phone'
    else:
        result['phone'] = phone

    different = payload.get('differentContact', False)
    if type(different) is not bool:
        errors['differentContact'] = 'differentContact'
    result['differentContact'] = different
    if different is True:
        contact = result.get('messengerContact', '')
        messenger = result.get('messenger')
        telephone = normalized_phone(contact)
        handle = bool(re.fullmatch(r'@[A-Za-z][A-Za-z0-9_]{4,31}', contact) or
                      re.fullmatch(r'https://t\.me/[A-Za-z][A-Za-z0-9_]{4,31}', contact))
        if not telephone and not (messenger == 'telegram' and handle):
            errors['messengerContact'] = 'messengerContact'
        else:
            result['messengerContact'] = telephone or contact
    else:
        result['messengerContact'] = phone or ''
        errors.pop('messengerContact', None)  # Hidden stale values cannot control contact.

    if result.get('maps') and not maps_url(result['maps']):
        errors['maps'] = 'maps'
    if result.get('businessUrl') and not business_url(result['businessUrl']):
        errors['businessUrl'] = 'businessUrl'
    if result.get('variant') == 'bulk' and result.get('quantity') != 'more':
        errors['quantity'] = 'quantity'
    if result.get('variant') == 'instagram':
        if (type(payload.get('productSchemaVersion')) is not int or payload['productSchemaVersion'] != 1
                or payload.get('product_id') != 'nfc-instagram-card' or payload.get('offer') != 'ready'):
            errors['variant'] = 'variant'
        profile = instagram_profile_url(payload.get('instagramUrl'))
        if not profile:
            errors['instagramUrl'] = 'instagramUrl'
        else:
            result['instagramUrl'] = profile
        if result.get('quantity') not in {'1', '2'}:
            errors['quantity'] = 'quantity'
        if any(payload.get(key) for key in ['maps', 'businessUrl', 'business', 'logo']):
            errors['variant'] = 'variant'
        result.update(productSchemaVersion=1, product_id='nfc-instagram-card', offer='ready', sku='NFC-IG-READY')
    elif any(key in payload for key in ['productSchemaVersion', 'product_id', 'offer', 'instagramUrl']):
        # Reject stale destination/product data; keep old v6 fingerprints unchanged.
        errors['variant'] = 'variant'
    if payload.get('consent') is not True:
        errors['consent'] = 'consent'
    result['consent'] = True

    source = result.get('source', '')
    if (not source.startswith('/') or source.startswith('//') or
            any(ch in source for ch in ('?', '#', '\\', '\r', '\n'))):
        source = '/'
    result['source'] = source
    attribution = payload.get('attribution', {})
    if not isinstance(attribution, dict) or len(attribution) > 12:
        raise LeadError(422, 'invalid_attribution', {'attribution': 'attribution'})
    result['attribution'] = {}
    for attr, value in attribution.items():
        if attr not in ATTRIBUTION_KEYS:
            continue
        limit = 2048 if attr == 'referrer' else 250 if attr == 'landing' else 200
        if not isinstance(value, str) or len(value) > limit:
            errors['attribution'] = 'attribution'
            continue
        value = CONTROL.sub('', value).strip()
        if attr == 'referrer':
            if not value:
                continue
            if not business_url(value):
                errors['attribution'] = 'attribution'
                continue
            parsed = urlsplit(value)
            value = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
        if attr == 'landing' and (not value.startswith('/') or value.startswith('//')
                                  or any(x in value for x in ('?', '#', '\\', '\r', '\n'))):
            errors['attribution'] = 'attribution'
            continue
        result['attribution'][attr] = value
    if errors:
        raise LeadError(422, 'validation', errors)
    return key, result


def receipt(lead_id, lead, duplicate):
    return {'id': lead_id, 'variant': lead['variant'], 'quantity': lead['quantity'],
            'quote': lead['quote'], 'mode': 'local_test', 'duplicate': duplicate,
            **({'product_id': lead['product_id'], 'offer': lead['offer']} if lead.get('product_id') else {})}


def displayed_price_observation(value):
    """Bounded, untrusted UI observation; never part of intent or canonical pricing."""
    if type(value) in (int, float):
        return str(value) if 0 <= value <= 1_000_000_000 else None
    if not isinstance(value, str) or len(value) > 80:
        return None
    value = ' '.join(value.split())
    if value in {'Individual quote', 'Custom quote', 'Індивідуальний розрахунок', 'Індивідуальний прорахунок'}:
        return value
    if re.fullmatch(r'(?:UAH\s*)?[\d\s,.]{1,32}(?:\s*(?:UAH|грн))?', value):
        return value
    return None


def telegram_message(lead_id, created, lead):
    """A bounded plain-text notification. Full PII remains in private storage only."""
    if lead.get('contractVersion') != 6:
        message = legacy_telegram_message(lead_id, created, lead)
    else:
        if lead.get('product_id') == 'nfc-instagram-card':
            return instagram_telegram_message(lead_id, created, lead)
        stamp = datetime.fromtimestamp(created, timezone.utc).isoformat()
        price = lead['quote']['amount'] if lead['quote']['status'] == 'fixed' else 'custom'
        message = '\n'.join([
            'NEW NFC CARD LEAD',
            f'Order ID: {lead_id}', f'Created: {stamp}',
            f'Language: {"UA" if lead["locale"] == "uk" else "EN"}',
            f'Source page: {lead["source"]}',
            f'UTM/source: {encode(lead["attribution"])}', '',
            f'Product: {lead["variant"]}', f'Quantity: {lead["quantity"]}',
            f'Canonical price: {price}', f'Currency: {lead["quote"]["currency"]}',
            f'Displayed price (untrusted): {lead.get("displayed_price") or "not provided"}', '',
            f'Name: {lead["name"]}', f'Phone: {lead["phone"]}',
            f'Preferred messenger: {lead["messenger"]}',
            f'Messenger contact: {lead["messengerContact"]}',
            f'Business name: {lead["business"]}', f'Google Maps URL: {lead["maps"]}',
            f'Instagram/website: {lead["businessUrl"]}', f'Comment: {lead["comment"]}',
            f'Consent: true; {lead["consentVersion"]}; {lead["consentAcceptedAt"]}',
        ])
    if len(message.encode('utf-8')) > 3900:
        message = message.encode('utf-8')[:3600].decode('utf-8', errors='ignore')
        message += '\n[Truncated; full record retained privately. Order ' + lead_id + ']'
    return message


class MockNotifier:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def send(self, lead_id, message):
        self.calls.append(lead_id)
        if self.fail:
            raise RuntimeError('simulated_notification_failure')
        return 'mock-accepted'


class LeadService:
    def __init__(self, db_path, telegram=None, email=None, clock=time.time,
                 rate_limit=10, commerce_path=COMMERCE_PATH):
        self.commerce = load_commerce(commerce_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.telegram, self.email = telegram, email
        self.clock, self.rate_limit = clock, rate_limit
        self._lock = RLock()
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS leads(id TEXT PRIMARY KEY, idem TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL, created REAL NOT NULL, payload TEXT NOT NULL, notification TEXT NOT NULL DEFAULT 'pending');
            CREATE TABLE IF NOT EXISTS logos(lead_id TEXT PRIMARY KEY REFERENCES leads(id), mime TEXT NOT NULL, content BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS rate_hits(client TEXT NOT NULL, created REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS rate_client ON rate_hits(client,created);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def submit(self, payload, client='127.0.0.1'):
        with self._lock:
            return self._submit(payload, client)

    def _throttle(self, payload, client):
        now = self.clock()
        key = request_key(payload)
        client_hash = hashlib.sha256(client.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT id FROM leads WHERE idem=?', (key,)).fetchone() if key else None
            bucket = client_hash + (':retry' if prior else ':new')
            allowance = max(20, self.rate_limit * 3) if prior else self.rate_limit
            db.execute('DELETE FROM rate_hits WHERE created < ?', (now - 60,))
            count = db.execute('SELECT count(*) FROM rate_hits WHERE client=? AND created>=?',
                               (bucket, now - 60)).fetchone()[0]
            if count >= allowance:
                raise LeadError(429, 'rate_limited')
            db.execute('INSERT INTO rate_hits VALUES(?,?)', (bucket, now))
        return bool(prior)

    def _legacy_retry(self, payload):
        key, intent, _logo = normalize_legacy(payload)
        with self.connect() as db:
            row = db.execute('SELECT id,fingerprint FROM leads WHERE idem=?', (key,)).fetchone()
        if not row:
            raise LeadError(422, 'legacy_contract_retired')
        if row[1] != fingerprint(intent):
            raise LeadError(409, 'idempotency_conflict')
        # Compatibility response only for an already-saved v1 retry; no remapping or notification.
        return {'ok': True, 'leadId': row[0], 'duplicate': True, 'mode': 'local_test',
                'notification': 'not_sent_live',
                'receipt': {'id': row[0], 'variant': None, 'quantity': None, 'quote': None,
                            'mode': 'legacy_local_test', 'duplicate': True}}

    def _submit(self, payload, client):
        existing = self._throttle(payload, client)
        if isinstance(payload, dict) and 'contractVersion' not in payload:
            if not existing:
                raise LeadError(422, 'legacy_contract_retired')
            return self._legacy_retry(payload)
        key, intent = normalize(payload)
        digest = fingerprint(intent)
        now = self.clock()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT id,fingerprint,payload FROM leads WHERE idem=?', (key,)).fetchone()
            if prior:
                if prior[1] != digest:
                    raise LeadError(409, 'idempotency_conflict')
                return {'ok': True, 'receipt': receipt(prior[0], json.loads(prior[2]), True)}
            lead_id = 'NFC-' + uuid.uuid4().hex[:20].upper()
            lead = {
                **intent, 'quote': canonical_quote(intent['variant'], intent['quantity'], self.commerce),
                'displayed_price': displayed_price_observation(payload.get('displayed_price')),
                'physicalProduct': intent.get('product_id', self.commerce['physicalProduct']['id']),
                'consentVersion': CONSENT_VERSION,
                'consentAcceptedAt': datetime.fromtimestamp(now, timezone.utc).isoformat(),
                'is_test': True,
            }
            db.execute('INSERT INTO leads(id,idem,fingerprint,created,payload) VALUES(?,?,?,?,?)',
                       (lead_id, key, digest, now, encode(lead)))
        # Commit precedes both notification and success. Notification errors cannot undo it.
        try:
            self.dispatch(lead_id, now, lead)
        except Exception:
            pass  # A pending/attempting record remains recoverable; no PII/error text escapes.
        return {'ok': True, 'receipt': receipt(lead_id, lead, False)}

    def dispatch(self, lead_id, created, lead):
        with self.connect() as db:
            claimed = db.execute(
                "UPDATE leads SET notification='attempting' WHERE id=? AND notification='pending'",
                (lead_id,)).rowcount
        if not claimed:
            return
        status = 'IMPLEMENTED_NOT_CONFIGURED'
        if self.telegram:
            try:
                self.telegram.send(lead_id, telegram_message(lead_id, created, lead))
                status = 'mock_telegram_accepted'
            except Exception:
                status = 'telegram_failed_lead_saved'
                if self.email:
                    try:
                        self.email.send(lead_id, telegram_message(lead_id, created, lead))
                        status = 'mock_email_fallback_accepted'
                    except Exception:
                        status = 'notifications_failed_lead_saved'
        with self.connect() as db:
            db.execute('UPDATE leads SET notification=? WHERE id=?', (status, lead_id))
