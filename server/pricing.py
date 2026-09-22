"""Server pricing reads the same canonical JSON as the Node renderer."""
import json
from pathlib import Path

COMMERCE_PATH = Path(__file__).resolve().parents[1] / 'src' / 'commerce.json'


def load_commerce(path=COMMERCE_PATH):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    try:
        valid = (
            type(data['schemaVersion']) is int and data['schemaVersion'] == 6
            and isinstance(data['revision'], str) and 1 <= len(data['revision']) <= 120
            and data['physicalProduct']['id'] == 'nfc-review-card'
            and data['currency'] == 'UAH' and data['market'] == 'UA'
            and type(data['deposit']) is int and data['deposit'] == 200
            and data['depositIncluded'] is True
            and set(data['variants']) == {'standard', 'branded'}
            and data['interests'] == ['standard', 'branded', 'bulk', 'consultation', 'instagram']
            and data['quantities'] == ['1', '2', 'more']
            and data['customQuoteInterests'] == ['bulk', 'consultation']
            and data['bulkQuantity'] == 'more'
        )
        if not valid:
            raise ValueError('invalid_commerce_configuration')
        validate_products(data)
        for variant in data['variants'].values():
            if (set(variant['prices']) != {'1', '2'} or
                    not all(type(p) is int and data['deposit'] <= p < 100000000
                            for p in variant['prices'].values())):
                raise ValueError('invalid_commerce_configuration')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('invalid_commerce_configuration') from exc
    return data


def canonical_quote(variant, quantity, commerce):
    if variant not in commerce['interests'] or quantity not in commerce['quantities']:
        raise ValueError('invalid_quote_combination')
    if variant == 'instagram' and quantity not in {'1', '2'}:
        raise ValueError('invalid_quote_combination')
    prices = (commerce['products']['nfc-instagram-card']['offers']['ready']['prices']
              if variant == 'instagram' else commerce['variants'].get(variant, {}).get('prices', {}))
    custom = quantity == 'more' or variant in commerce['customQuoteInterests']
    return {
        'status': 'custom' if custom else 'fixed',
        'amount': None if custom else prices[quantity],
        'currency': commerce['currency'],
        'deposit': commerce['deposit'],
        'depositIncluded': commerce['depositIncluded'],
        'pricingRevision': (commerce['products']['nfc-instagram-card']['pricingRevision']
                            if variant == 'instagram' else commerce['revision']),
    }


def validate_products(data):
    """Validate the additive product schema; Review Card remains a separate family."""
    expected = {'standard': ('nfc-review-card', 'standard'),
                'branded': ('nfc-review-card', 'branded'),
                'bulk': ('nfc-review-card', 'custom'),
                'consultation': ('nfc-review-card', 'consultation'),
                'instagram': ('nfc-instagram-card', 'ready')}
    try:
        products = data['products']
        ig = products['nfc-instagram-card']
        ready = ig['offers']['ready']
        valid = (type(data['productSchemaVersion']) is int and data['productSchemaVersion'] == 1
                 and set(products) == {'nfc-review-card', 'nfc-instagram-card'}
                 and set(products['nfc-review-card']['offers']) == {'standard', 'branded'}
                 and ig['pricingRevision'] == 'NFC-INSTAGRAM-UA-2026-09-v18'
                 and isinstance(ig['evidence'], str) and bool(ig['evidence'])
                 and ig['sku'] == 'NFC-IG-READY' and ig['category'] == 'INSTAGRAM'
                 and set(ig['offers']) == {'ready'}
                 and ready['qr'] == 'not_included' and ready['customDesign'] is False
                 and ready['quantities'] == ['1', '2']
                 and ready['prices'] == {'1': 1500, '2': 2600}
                 and all(type(n) is int for n in ready['prices'].values())
                 and set(data['selections']) == set(expected))
        for key, (product, offer) in expected.items():
            valid = valid and data['selections'][key] == {'product_id': product, 'offer': offer}
        for key in ['standard', 'branded']:
            valid = valid and products['nfc-review-card']['offers'][key]['legacyPriceKey'] == key
        if not valid:
            raise ValueError('invalid_commerce_configuration')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('invalid_commerce_configuration') from exc
