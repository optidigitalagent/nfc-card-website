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
            and type(data['deposit']) is int and data['deposit'] > 0
            and data['depositIncluded'] is True
            and set(data['variants']) == {'standard', 'branded'}
            and data['interests'] == ['standard', 'branded', 'bulk', 'consultation']
            and data['quantities'] == ['1', '2', 'more']
            and data['customQuoteInterests'] == ['bulk', 'consultation']
            and data['bulkQuantity'] == 'more'
        )
        if not valid:
            raise ValueError('invalid_commerce_configuration')
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
    custom = quantity == 'more' or variant in commerce['customQuoteInterests']
    return {
        'status': 'custom' if custom else 'fixed',
        'amount': None if custom else commerce['variants'][variant]['prices'][quantity],
        'currency': commerce['currency'],
        'deposit': commerce['deposit'],
        'depositIncluded': commerce['depositIncluded'],
        'pricingRevision': commerce['revision'],
    }
