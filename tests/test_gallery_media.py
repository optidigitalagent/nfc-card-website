"""Owner media replacement: playback and gallery isolation, without public submissions."""
import pytest
from playwright.sync_api import expect
from test_v12_browser import browser, web, repo, service, block_external, ready


@pytest.mark.parametrize('width', [320, 393, 1440])
@pytest.mark.parametrize('prefix', ['', '/en'])
def test_manual_video_gallery_and_image_zoom(web, browser, width, prefix):
    origin, _ = web
    context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
    block_external(context, origin)
    page = context.new_page()
    requests, errors = [], []
    page.on('request', lambda request: requests.append(request.url))
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(origin + prefix + '/solutions/review-card', wait_until='networkidle')
    ready(page)
    expect(page.locator('[data-thumb-to]')).to_have_count(13)
    assert not any('.mp4' in url for url in requests), 'Videos must not download on arrival'
    assert page.locator('[data-slide] video[src]').count() == 0
    for index in (6, 7, 8):
        page.locator(f'[data-thumb-to="{index}"]').click()
        video = page.locator(f'[data-slide="{index}"] video')
        video.scroll_into_view_if_needed()
        expect(video).to_be_visible()
        assert video.evaluate('(v)=>v.paused && v.controls && v.playsInline && !v.autoplay && !v.muted')
        # Native controls must remain reachable below the corner expand button.
        assert video.evaluate('''v=>{const r=v.getBoundingClientRect();
            return document.elementFromPoint(r.x+r.width/2,r.bottom-24)===v}''')
        # Headless macOS may freeze the media clock without an audio sink.
        # Check actual frame advancement with audio muted only in this test.
        video.evaluate('(v)=>{v.muted=true;return v.play()}')
        page.wait_for_function('''()=>{const v=document.querySelector('[data-slide]:not([hidden]) video');
            return v.currentTime>0 && v.videoWidth===320 && v.videoHeight===568 && !v.paused}''')
        video.evaluate('(v)=>v.muted=false')
        video.focus()
        page.keyboard.press('ArrowRight')
        expect(page.locator('[data-gallery-count]')).to_have_text(f'{index+1} / 13')
        page.locator('[data-zoom]').click()
        assert video.evaluate('(v)=>v.paused')
        modal = page.locator('.lightbox-scroll video')
        expect(modal).to_be_visible()
        expect(page.locator('[data-lightbox-zoom]')).to_have_count(0)
        assert not modal.evaluate('(v)=>v.muted'), 'The public player must retain audio'
        # The headless macOS audio sink can hold an audible video's media clock
        # at zero. Mute only in this browser test so decoded-frame playback is
        # measurable; restore the real player's audio setting before closing.
        modal.evaluate('(v)=>{v.muted=true;return v.play()}')
        page.wait_for_function("()=>document.querySelector('.lightbox-scroll video').currentTime>0")
        if index == 8:
            assert modal.locator('track').count() == 2
            page.wait_for_function("()=>[...document.querySelector('.lightbox-scroll video').textTracks].some(t=>t.mode==='showing' && t.cues?.length===5)")
        modal.evaluate('(v)=>v.muted=false')
        page.keyboard.press('Escape')
        expect(page.locator('dialog.image-lightbox')).not_to_be_visible()
        assert modal.evaluate('(v)=>v.paused') and video.evaluate('(v)=>v.paused')
        video.scroll_into_view_if_needed()
        video.evaluate('(v)=>v.play()')
        page.locator('[data-gallery-next]').click()
        assert video.evaluate('(v)=>v.paused'), 'A hidden video must stop playing'
    page.locator('[data-thumb-to="1"]').click()
    page.locator('[data-zoom]').click()
    expect(page.locator('.lightbox-scroll video')).to_be_hidden()
    expect(page.locator('.lightbox-scroll img')).to_be_visible()
    page.locator('.lightbox-scroll').dblclick()
    expect(page.locator('dialog.image-lightbox')).to_have_attribute('data-zoomed', 'true')
    page.keyboard.press('Escape')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('[data-thumb-to="10"]').click()
    page.locator('[data-zoom]').click()
    caption=page.locator('.lightbox-caption')
    expect(caption).to_be_visible()
    expect(caption).to_contain_text('examples' if prefix else 'умовні')
    expect(page.locator('.image-lightbox')).to_have_attribute('aria-describedby', 'gallery-viewer-caption')
    page.locator('[data-lightbox-next]').focus()
    page.keyboard.press('End')
    assert page.evaluate("window.nfcAnalyticsEvents.some(e=>e.event==='product_gallery_view'&&e.asset_index===12)")
    assert not errors
    context.close()
