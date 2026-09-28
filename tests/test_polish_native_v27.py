"""Polish no-JavaScript fallback stays local to the disposable test gateway."""
from playwright.sync_api import expect

from test_v12_reviews import repo, service
from test_v12_browser import web, browser, block_external


def fill_native_contact(page):
    page.fill('#f-name', 'Synthetic local Polish QA')
    page.fill('#f-phone', '+380001234567')
    page.locator('.lead-form:not([data-menu-form]) [name=messenger][value=telegram]').check(force=True)
    page.locator('#f-consent').check(force=True)


def test_polish_native_instagram_error_names_the_field(web, browser):
    origin, _ = web
    context = browser.new_context(java_script_enabled=False, reduced_motion='reduce')
    block_external(context, origin)
    page = context.new_page()
    page.goto(origin + '/pl/order?variant=instagram&quantity=1')
    fill_native_contact(page)
    page.fill('#f-instagramUrl', 'https://instagram.com/p/')
    page.locator('.lead-form:not([data-menu-form]) [type=submit]').click()
    expect(page.locator('h1')).to_have_text('Sprawdź dane zgłoszenia')
    expect(page.locator('main li')).to_contain_text('Link do profilu na Instagramie')
    assert page.locator('html').get_attribute('lang') == 'pl'
    context.close()


def test_polish_native_custom_quantity_receipt_uses_words(web, browser):
    origin, server = web
    context = browser.new_context(java_script_enabled=False, reduced_motion='reduce')
    block_external(context, origin)
    page = context.new_page()
    page.goto(origin + '/pl/order?variant=bulk&quantity=more')
    fill_native_contact(page)
    page.locator('.lead-form:not([data-menu-form]) [type=submit]').click()
    expect(page.locator('h1')).to_contain_text('lokalnie')
    expect(page.locator('main')).to_contain_text('Co najmniej 3 karty')
    assert 'more' not in page.locator('main').inner_text()
    with server.leads.repo.transaction() as db:
        row = db.execute('SELECT payload FROM commerce_leads').fetchone()
    assert row['payload']['locale'] == 'pl'
    assert row['payload']['quote']['currency'] == 'PLN'
    context.close()
