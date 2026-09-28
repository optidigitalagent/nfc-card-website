"""Owner PLN contract across rendered Pages and browser display calculators."""
import json
from pathlib import Path
import re
import subprocess

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
CONTRACT = json.loads((ROOT / 'src/poland-commerce.json').read_text())


def test_exact_owner_contract_and_product_structured_data():
    assert CONTRACT['contractId'] == 'NFC-CARD-PL-2026-09-v28'
    prices = {
        'review-card': [129, 219], 'branded-review-card': [169, 299],
        'instagram-card': [129, 219], 'review-card-3d': [349], 'menu-card': [89],
    }
    for route, expected in prices.items():
        soup = BeautifulSoup((SITE / 'pl/solutions' / route / 'index.html').read_text(), 'html.parser')
        product = next(json.loads(script.string) for script in soup.select('script[type="application/ld+json"]')
                       if json.loads(script.string).get('@type') == 'Product')
        offers = product['offers'] if isinstance(product['offers'], list) else [product['offers']]
        assert [offer['price'] for offer in offers] == expected
        assert all(offer['priceCurrency'] == 'PLN' and offer['eligibleRegion'] == 'PL' for offer in offers)
        assert 'UAH' not in soup.get_text(' ', strip=True)
    for page in (SITE / 'pl').rglob('index.html'):
        soup = BeautifulSoup(page.read_text(), 'html.parser')
        assert not re.search(r'\bUAH\b|грн|Nova Poshta|Dla biznesu', soup.get_text(' ', strip=True)), page


def test_pl_quote_boundaries_and_ua_en_regression():
    source = """
import assert from 'node:assert/strict';
import commerce from './src/commerce.json' with {type:'json'};
import poland from './src/poland-commerce.json' with {type:'json'};
import {selectionQuote,review3dQuote} from './src/commerce-contract.mjs';
import {menuQuote,MENU_VARIANTS} from './src/menu-contract.mjs';
const c={...commerce,poland};
for(const [variant,a,b] of [['standard',129,219],['branded',169,299],['instagram',129,219]]){
  for(const [q,amount] of [['1',a],['2',b]]){
    const quote=selectionQuote(c,variant,q,'pl');
    assert.deepEqual([quote.amount,quote.currency,quote.deposit],[amount,'PLN',20]);
  }
}
for(const [variant,q] of [['standard','more'],['branded','more'],['bulk','more'],['consultation','1']]){
  const quote=selectionQuote(c,variant,q,'pl');
  assert.deepEqual([quote.valid,quote.amount,quote.currency,quote.deposit,quote.pricingRevision],
    [true,null,'PLN',20,poland.contractId]);
}
for(const [q,total,balance] of [[1,349,329],[2,698,678]]){
  const quote=review3dQuote(c,q,'pl');
  assert.deepEqual([quote.amount,quote.deposit,quote.balance,quote.currency],[total,20,balance,'PLN']);
}
for(const [q,total] of [[1,89],[4,356],[5,345],[6,414],[9,621],[10,550],[24,1320],[25,1125],[26,1170]]){
  const quote=menuQuote([{variant_id:MENU_VARIANTS[0],quantity:q}],'card_order',poland);
  assert.deepEqual([quote.amount,quote.deposit,quote.balance,quote.currency],[total,20,total-20,'PLN']);
}
const mixed=menuQuote(MENU_VARIANTS.slice(0,3).map(variant_id=>({variant_id,quantity:2})),'card_order',poland);
assert.deepEqual([mixed.quantity,mixed.amount,mixed.deposit],[6,414,20]);
const consult=menuQuote([],'menu_consultation',poland);
assert.deepEqual([consult.amount,consult.deposit,consult.balance,consult.currency],[null,null,null,'PLN']);
assert.deepEqual([selectionQuote(c,'standard','1','uk').amount,selectionQuote(c,'standard','1','en').amount],[1500,1500]);
assert.deepEqual([review3dQuote(c,1,'uk').amount,menuQuote([{variant_id:MENU_VARIANTS[0],quantity:1}]).amount],[4000,1000]);
"""
    result = subprocess.run(['node', '--input-type=module'], cwd=ROOT, input=source, text=True,
                            capture_output=True)
    assert result.returncode == 0, result.stderr
