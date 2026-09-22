"""Corrective-release regressions for the complete Instagram product pages."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from test_pages_v17 import build, source


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "locale,expected",
    [
        ("uk", [
            "NFC Instagram Card працює за тим самим принципом, що й NFC Review Card",
            "Що стає простішим",
            "Від посилання до готової картки",
            "Що входить",
            "Характеристики",
            "Де розмістити картку",
            "Чесне уточнення",
            "Оплата й доставка",
            "FAQ — NFC Instagram Card",
            "NFC Review Card відкриває форму відгуку конкретної Google-точки",
        ]),
        ("en", [
            "NFC Instagram Card works the same way as NFC Review Card",
            "What becomes easier",
            "From your link to a ready-to-use card",
            "What is included",
            "Specifications",
            "Where to place the card",
            "An honest clarification",
            "Payment and delivery",
            "FAQ — NFC Instagram Card",
            "NFC Review Card opens the review form for a specific Google location",
        ]),
    ],
)
def test_commercial_copy_is_complete_and_visible_without_master_accordion(source, locale, expected):
    site = build(source)
    prefix = "en/" if locale == "en" else ""
    soup = BeautifulSoup((site / prefix / "solutions/instagram-card/index.html").read_text("utf-8"), "html.parser")
    content = soup.select_one(".instagram-product-content")
    assert content is not None
    assert not soup.select("#product-details.product-disclosure,[data-details-control]")
    text = soup.select_one("main").get_text(" ", strip=True)
    for item in expected:
        assert item in text
    assert len(content.select(".instagram-product-benefits .meaning-rows > div")) == 4
    assert len(content.select(".instagram-product-steps .steps > li")) == 4
    assert len(content.select(".instagram-product-included li")) == 7
    assert len(content.select(".instagram-product-specs li")) == 7
    assert len(content.select(".instagram-product-faq .faq-list > details")) == 9


def test_product_detail_ink_override_keeps_secondary_tokens_scoped():
    commerce = (ROOT / "src/commerce.css").read_text("utf-8")
    instagram = (ROOT / "src/instagram.css").read_text("utf-8")
    assert ".product-detail p,.product-detail li{color:var(--nfc-ink)" in commerce
    assert ".instagram-product-content>.field-hint" in instagram
    assert ".instagram-info-content .section p:not(.eyebrow):not(.field-hint)" in instagram
    assert ".commerce-product[data-product=instagram] .product-promise" in instagram
    assert "color:var(--muted)" in instagram


def test_commercial_mechanism_requires_notification_action(source):
    site = build(source)
    for relative, phrase in [
        ("solutions/instagram-card/index.html", "Клієнт натискає сповіщення"),
        ("en/solutions/instagram-card/index.html", "The customer taps the notification"),
    ]:
        soup = BeautifulSoup((site / relative).read_text("utf-8"), "html.parser")
        step = soup.select(".instagram-product-steps .steps > li")[3].get_text(" ", strip=True)
        assert phrase in step


def test_approved_gallery_has_five_images_and_zoom_control(source):
    site = build(source)
    for relative in ["solutions/instagram-card/index.html", "en/solutions/instagram-card/index.html"]:
        soup = BeautifulSoup((site / relative).read_text("utf-8"), "html.parser")
        assert not soup.select("[data-placeholder]")
        assert len(soup.select("[data-slide]")) == 5
        assert len(soup.select(".gallery-open,[data-zoom]")) == 1


def test_repository_scoped_release_policy_is_persistent():
    policy = (ROOT / "AGENTS.md").read_text("utf-8")
    for phrase in ["push it to the existing `main`", "wait for green CI", "GitHub Pages deployment", "without force"]:
        assert phrase in policy
