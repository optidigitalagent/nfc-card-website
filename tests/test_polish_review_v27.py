"""Polish public review flow uses only an isolated local database and loopback HTTP."""
from playwright.sync_api import expect

from test_v12_reviews import service, repo, submission, review_id, enrich
from test_v12_browser import web, browser, ready, block_external


def test_polish_review_durable_submission_and_no_mixed_language_fallback(service):
    service.submit(submission(locale='pl'))
    with service.repo.transaction() as db:
        row = db.execute('SELECT locale,status FROM client_reviews').fetchone()
    assert row == {'locale': 'pl', 'status': 'pending'}
    assert service.public_list('pl')['items'] == []


def test_populated_review_migration_preserves_existing_record_and_checksums(service):
    service.submit(submission())
    with service.repo.transaction() as db:
        before = db.execute("SELECT name,checksum FROM nfc_review_migrations WHERE name<>'004_polish_reviews.sql' ORDER BY name").fetchall()
        db.execute("ALTER TABLE client_reviews DROP CONSTRAINT client_reviews_locale_check, ADD CONSTRAINT client_reviews_locale_check CHECK(locale IN ('uk','en'))")
        db.execute("ALTER TABLE client_review_translations DROP CONSTRAINT client_review_translations_locale_check, ADD CONSTRAINT client_review_translations_locale_check CHECK(locale IN ('uk','en'))")
        db.execute("DELETE FROM nfc_review_migrations WHERE name='004_polish_reviews.sql'")
    service.repo.migrate()
    with service.repo.transaction() as db:
        assert db.execute("SELECT name,checksum FROM nfc_review_migrations WHERE name<>'004_polish_reviews.sql' ORDER BY name").fetchall() == before
        assert db.execute("SELECT count(*) n FROM client_reviews WHERE locale='uk' AND status='pending'").fetchone()['n'] == 1
        assert db.execute("SELECT count(*) n FROM review_notification_outbox").fetchone()['n'] == 1
    service.submit(submission(locale='pl', reviewText='Druga syntetyczna opinia w języku polskim wyłącznie dla testu migracji.'))
    with service.repo.transaction() as db:
        assert db.execute("SELECT count(*) n FROM client_reviews WHERE locale='pl'").fetchone()['n'] == 1


def test_polish_review_list_requires_approved_polish_copy(service):
    service.submit(submission())
    identifier = review_id(service)
    row = enrich(service, identifier)
    row = service.action(identifier, 'publish', row['version'])
    assert service.public_list('uk')['items']
    assert service.public_list('pl')['items'] == []
    row = service.action(identifier, 'unpublish', row['version'])
    row = service.update(identifier, {'version': row['version'], 'translations': [{
        'locale': 'pl', 'publicReviewText': 'Syntetyczna polska opinia użyta wyłącznie w izolowanym teście.',
        'primaryAlt': 'Karta NFC w syntetycznym teście',
        'secondaryAlt': 'Miejsce użycia karty w syntetycznym teście', 'approved': True,
    }]})
    row = service.action(identifier, 'publish', row['version'])
    item = service.public_list('pl')['items'][0]
    assert item['reviewText'].startswith('Syntetyczna polska opinia')
    assert item['primaryImage']['alt'] == 'Karta NFC w syntetycznym teście'


def test_polish_review_form_validation_and_local_receipt(web, browser):
    origin, server = web
    context = browser.new_context(viewport={'width': 393, 'height': 844}, reduced_motion='reduce')
    block_external(context, origin)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    response = page.goto(origin + '/pl/reviews/new')
    assert response.status == 200
    ready(page)
    assert page.locator('html').get_attribute('lang') == 'pl'
    page.locator('.review-form [type=submit]').click()
    expect(page.locator('.error-summary')).to_contain_text('Sprawdź pola formularza opinii')
    page.locator('#review-rating-4').check()
    page.locator('#review-text').fill('Syntetyczny lokalny test polskiego formularza opinii NFC CARD.')
    page.locator('#review-instagram').fill('@isolated_test')
    page.locator('#review-consent').check()
    page.locator('.review-form [type=submit]').click()
    expect(page.locator('.form-result')).to_have_attribute('data-status', 'success')
    expect(page.locator('.form-result')).to_contain_text('wysłana do weryfikacji')
    with server.reviews.runtime.service.repo.transaction() as db:
        row = db.execute('SELECT locale,status FROM client_reviews').fetchone()
    assert row == {'locale': 'pl', 'status': 'pending'}
    assert not errors
    context.close()
