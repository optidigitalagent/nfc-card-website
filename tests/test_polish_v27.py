"""Polish route and rendered-output contract in an isolated Pages artifact."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://optidigitalagent.github.io/nfc-card-website"
PUBLIC_ROUTES = (
    "", "about", "solutions", "solutions/review-card",
    "solutions/branded-review-card", "solutions/review-card-3d",
    "solutions/instagram-card", "instagram-card", "solutions/menu-card",
    "menu-card", "order", "contact", "delivery-and-payment",
    "warranty-and-returns", "thank-you", "privacy", "terms",
)


def _build_pages(tmp_path):
    shutil.copytree(ROOT / "src", tmp_path / "src")
    historical = tmp_path / "refinements/instagram-v18"
    historical.mkdir(parents=True)
    shutil.copyfile(ROOT / "refinements/instagram-v18/routes.json", historical / "routes.json")
    env = {key: value for key, value in os.environ.items() if not key.startswith("NFC_")}
    env.update(NFC_DEPLOYMENT_TARGET="github-pages", NFC_PUBLIC_ORIGIN="https://optidigitalagent.github.io",
               NFC_PUBLIC_BASE_PATH="/nfc-card-website", NFC_PUBLICATION_MODE="PUBLIC_PREVIEW")
    result = subprocess.run(["node", "src/build.mjs"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return tmp_path / "site"


def test_polish_pages_are_complete_and_reciprocal(tmp_path):
    site = _build_pages(tmp_path)
    assert len(PUBLIC_ROUTES) == 17
    for route in PUBLIC_ROUTES:
        suffix = route + "/" if route else ""
        urls = {
            "uk": BASE + "/" + suffix,
            "en": BASE + "/en/" + suffix,
            "pl": BASE + "/pl/" + suffix,
        }
        for locale, prefix in (("uk", ""), ("en", "en"), ("pl", "pl")):
            page = site / prefix / route / "index.html"
            assert page.is_file(), page
            soup = BeautifulSoup(page.read_text(), "html.parser")
            assert soup.html["lang"] == locale
            assert soup.select_one('link[rel="canonical"]')["href"].rstrip("/") == urls[locale].rstrip("/")
            alternates = {el["hreflang"]: el["href"] for el in soup.select('link[rel="alternate"][hreflang]')}
            assert {key: value.rstrip("/") for key, value in alternates.items()} == {
                **{key: value.rstrip("/") for key, value in urls.items()},
                "x-default": urls["uk"].rstrip("/"),
            }
            assert soup.select_one('meta[property="og:locale"]')["content"] == {"uk": "uk_UA", "en": "en_GB", "pl": "pl_PL"}[locale]
            if locale == "pl":
                assert soup.title and soup.title.string.strip()
                assert soup.select_one('meta[name="description"]')["content"].strip()
                assert all(not re.search(r"[А-Яа-яІіЇїЄєҐґ]", node)
                           for node in soup.stripped_strings), page
                assert all(not re.search(r"[А-Яа-яІіЇїЄєҐґ]", img.get("alt", "")) for img in soup.select("img")), page
                for script in soup.select('script[type="application/ld+json"]'):
                    node = json.loads(script.string)
                    if node.get("@type") != "Organization":
                        assert node["inLanguage"] == "pl"
    pl_product = BeautifulSoup((site / "pl/solutions/review-card-3d/index.html").read_text(), "html.parser")
    product = next(json.loads(script.string) for script in pl_product.select('script[type="application/ld+json"]')
                   if json.loads(script.string).get("@type") == "Product")
    assert product["offers"]["price"] == 4000 and product["offers"]["priceCurrency"] == "UAH"
    assert "PLN" not in pl_product.get_text(" ")
    assert (site / "pl/index.html").is_file()  # Direct Pages reload target.


def test_polish_plural_and_safe_language_switch():
    source = """
import assert from 'node:assert/strict';
import {polishPlural} from './src/locale.mjs';
for(const [n,expected] of [[1,'karta'],[2,'karty'],[4,'karty'],[5,'kart'],[12,'kart'],[22,'karty'],[25,'kart']])
  assert.equal(polishPlural(n,'karta','karty','kart'),expected);
globalThis.location={origin:'https://optidigitalagent.github.io',href:'https://optidigitalagent.github.io/nfc-card-website/order/?quantity=22&name=Secret&phone=123#request'};
globalThis.document={getElementById:id=>id==='request'?{}:null};
globalThis.window={};
await import('./src/localization-client.js');
const switched=window.nfcSwitchLocaleURL('https://optidigitalagent.github.io/nfc-card-website/pl/order/');
assert.equal(switched,'/nfc-card-website/pl/order/?quantity=22#request');
"""
    result = subprocess.run(["node", "--input-type=module"], cwd=ROOT, input=source, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
