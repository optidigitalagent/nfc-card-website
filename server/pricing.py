"""Server pricing reads the same canonical JSON as the Node renderer."""
import json
from pathlib import Path

COMMERCE_PATH = Path(__file__).resolve().parents[1] / 'src' / 'commerce.json'
MENU_VARIANTS = ('square_100_black', 'square_100_white', 'square_60_black',
                 'square_60_white', 'round_70_black', 'round_70_white')


def menu_quote(rows, intent='card_order'):
    """Mirror the Menu display quote; the deployed gateway recalculates it."""
    if intent == 'menu_consultation':
        if rows:
            raise ValueError('invalid_menu_rows')
        return {'quantity': 0, 'unitPrice': None, 'amount': None,
                'deposit': None, 'balance': None, 'items': []}
    if intent != 'card_order' or not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError('invalid_menu_rows')
    merged = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'variant_id', 'quantity'} or
                row['variant_id'] not in MENU_VARIANTS or type(row['quantity']) is not int or
                not 1 <= row['quantity'] <= 10000):
            raise ValueError('invalid_menu_rows')
        variant = row['variant_id']
        merged[variant] = merged.get(variant, 0) + row['quantity']
        if merged[variant] > 10000:
            raise ValueError('invalid_menu_rows')
    items = [{'variant_id': variant, 'quantity': merged[variant]}
             for variant in MENU_VARIANTS if variant in merged]
    quantity = sum(item['quantity'] for item in items)
    if quantity > 10000:
        raise ValueError('invalid_menu_rows')
    unit = 500 if quantity >= 25 else 600 if quantity >= 10 else 750 if quantity >= 5 else 1000
    amount = quantity * unit
    return {'quantity': quantity, 'unitPrice': unit, 'amount': amount,
            'deposit': 200, 'balance': amount - 200, 'items': items}


def review3d_quote(quantity, commerce):
    """Mirror the public quote; the gateway is authoritative at submission."""
    offer = commerce['products']['nfc-review-card-3d']['offers']['fixed']
    if type(quantity) is not int or not offer['quantityMin'] <= quantity <= offer['quantityMax']:
        raise ValueError('invalid_review3d_quantity')
    amount = quantity * offer['unitUah']
    return {'quantity': quantity, 'unitPrice': offer['unitUah'], 'amount': amount,
            'deposit': offer['depositUahPerOrder'], 'balance': amount - offer['depositUahPerOrder']}


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
                 and set(products) == {'nfc-review-card', 'nfc-instagram-card', 'nfc-menu-card', 'nfc-review-card-3d'}
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
        menu = products['nfc-menu-card']
        review3d = products['nfc-review-card-3d']
        fixed3d = review3d['offers']['fixed']
        valid = valid and (
            review3d['category'] == 'GOOGLE_REVIEW'
            and review3d['pricingRevision'] == 'NFC-REVIEW-3D-UA-2026-09-v26'
            and isinstance(review3d['evidence'], str) and bool(review3d['evidence'])
            and set(review3d['offers']) == {'fixed'}
            and fixed3d == {'unitUah': 4000, 'depositUahPerOrder': 200,
                            'depositIncluded': True, 'customDesign': False,
                            'prototype': True, 'madeToOrder': True,
                            'quantityMin': 1, 'quantityMax': 10000}
        )
        menu_ready = menu['offers']['ready']
        valid = valid and (
            menu['pricingRevision'] == 'NFC-MENU-UA-2026-09-v23'
            and menu['category'] == 'ONLINE_MENU'
            and menu_ready['readyMadeOnly'] is True
            and menu_ready['customDesign'] is False
            and menu_ready['qr'] == 'not_included'
            and menu_ready['depositUahPerOrder'] == 200
            and menu_ready['depositIncluded'] is True
            and menu_ready['mixVariants'] is True
            and menu_ready['tiers'] == [
                {'min': 1, 'max': 4, 'unitUah': 1000},
                {'min': 5, 'max': 9, 'unitUah': 750},
                {'min': 10, 'max': 24, 'unitUah': 600},
                {'min': 25, 'max': None, 'unitUah': 500},
            ]
        )
        for key, (product, offer) in expected.items():
            valid = valid and data['selections'][key] == {'product_id': product, 'offer': offer}
        for key in ['standard', 'branded']:
            valid = valid and products['nfc-review-card']['offers'][key]['legacyPriceKey'] == key
        if not valid:
            raise ValueError('invalid_commerce_configuration')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('invalid_commerce_configuration') from exc
