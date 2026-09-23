"""PUBLIC release configuration; isolated builds, never a live gateway call."""
import json
import os
import subprocess
import pytest
from bs4 import BeautifulSoup
from test_pages_v17 import source, build, ORIGIN, BASE, ENDPOINT


def test_public_requires_content_bound_owner_receipt_and_real_endpoint(source):
    env = {k: v for k, v in os.environ.items() if not k.startswith('NFC_')}
    env.update(NFC_ENV='production', NFC_DEPLOYMENT_TARGET='github-pages', NFC_PUBLICATION_MODE='PUBLIC',
               NFC_PUBLIC_ORIGIN=ORIGIN, NFC_PUBLIC_BASE_PATH=BASE)
    missing = subprocess.run(['node', 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert missing.returncode != 0 and 'PUBLIC requires' in missing.stderr
    approval = source / 'src/publication-approval.json'
    data = json.loads(approval.read_text())
    data['publicLaunch']['ownerAuthorizedPublication'] = False
    approval.write_text(json.dumps(data))
    env['NFC_LEAD_ENDPOINT'] = ENDPOINT
    blocked = subprocess.run(['node', 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert blocked.returncode != 0 and 'Indexing blocked' in blocked.stderr


def test_public_marketing_indexed_forms_enabled_after_mount_and_no_preview_badge(source):
    # Exercise PUBLIC in a disposable fixture; the real v24 checkout has a
    # content-bound approval, while any later source edit must still invalidate it.
    from server.publication import content_hash
    approval = source / 'src/publication-approval.json'
    data = json.loads(approval.read_text())
    data['publicLaunch']['reviewedContentSha256'] = content_hash(source)
    approval.write_text(json.dumps(data))
    site = build(source, NFC_PUBLICATION_MODE='PUBLIC', NFC_LEAD_ENDPOINT=ENDPOINT, NFC_TELEGRAM_ENABLED='true')
    for relative in ['index.html', 'en/index.html', 'about/index.html', 'en/about/index.html',
                     'solutions/review-card/index.html', 'solutions/branded-review-card/index.html',
                     'privacy/index.html', 'terms/index.html', 'warranty-and-returns/index.html']:
        soup = BeautifulSoup((site / relative).read_text(), 'html.parser')
        assert soup.html['data-publication-mode'] == 'PUBLIC'
        assert soup.html['data-lead-endpoint'] == ENDPOINT
        assert soup.select_one('meta[name=robots]')['content'] == 'index,follow'
        assert not soup.select('.preview-badge')
        assert 'PUBLIC PREVIEW' not in soup.get_text()
        assert 'temporarily unavailable' not in soup.get_text()
        assert soup.select_one('link[rel=canonical]')['href'].startswith(ORIGIN + BASE)
        for form in soup.select('.lead-form'):
            assert form['method'] == 'dialog' and form['action'] == ''
    for locale in ['', 'en/']:
        privacy = BeautifulSoup((site / (locale + 'privacy/index.html')).read_text(), 'html.parser')
        assert 'Draft' not in privacy.get_text() and 'Чернетка' not in privacy.get_text()
        assert ('Artem Antonov' if locale else 'Артем Антонов') in privacy.get_text()
        assert 'PostgreSQL' in privacy.get_text() and 'Telegram' in privacy.get_text()
    robots = (site / 'robots.txt').read_text()
    assert 'Disallow: /\n' not in robots
    assert 'Sitemap: ' + ORIGIN + BASE + '/sitemap.xml' in robots
    assert len(BeautifulSoup((site / 'sitemap.xml').read_text(), 'xml').select('loc')) == 26
    assert not (site / 'admin').exists()
    assert not (site / 'api').exists()


@pytest.mark.parametrize('filename', ['public-legal.mjs', 'commerce-view.mjs', 'about-view.mjs', 'about-content.json', 'commerce.json'])
def test_public_content_change_invalidates_owner_receipt(source, filename):
    legal = source / 'src' / filename
    legal.write_text(legal.read_text() + '\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith('NFC_')}
    env.update(NFC_ENV='production', NFC_DEPLOYMENT_TARGET='github-pages', NFC_PUBLICATION_MODE='PUBLIC',
               NFC_PUBLIC_ORIGIN=ORIGIN, NFC_PUBLIC_BASE_PATH=BASE, NFC_LEAD_ENDPOINT=ENDPOINT)
    result = subprocess.run(['node', 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert result.returncode != 0 and 'Indexing blocked' in result.stderr
