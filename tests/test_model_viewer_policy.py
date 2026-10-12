"""Keep the model decoder's WASM permission off forms and unrelated routes."""
import pytest

from server.model_viewer_policy import model_viewer_script_policy


@pytest.mark.parametrize('path', [
    '/solutions/review-card', '/solutions/review-card/',
    '/solutions/review-card/?quantity=1', '/en/solutions/review-card',
    '/pl/solutions/review-card/',
])
def test_model_pages_allow_wasm_without_general_eval(path):
    policy = model_viewer_script_policy(path)
    assert "'wasm-unsafe-eval'" in policy
    assert "'unsafe-eval'" not in policy
    assert "'unsafe-inline'" not in policy


@pytest.mark.parametrize('path', [
    '/', '/solutions/branded-review-card', '/solutions/review-card-3d',
    '/reviews/new', '/pl/reviews/new', '/admin/reviews', '/api/leads',
    '/en/order', '/assets/model-viewer.min.js',
    '/solutions/review-card/other', '/other/en/solutions/review-card',
    '/reviews/new?next=/solutions/review-card',
])
def test_other_routes_keep_strict_script_policy(path):
    assert model_viewer_script_policy(path) == "script-src 'self'"


@pytest.mark.parametrize('path', [
    '/solutions/review-card/?quantity=1', '/en/solutions/review-card', '/pl/solutions/review-card/',
])
def test_model_pages_allow_only_pinned_styles_and_blob_textures(path):
    from server.model_viewer_policy import model_viewer_style_policy, model_viewer_preview_image_policy, model_viewer_connect_policy, MODEL_VIEWER_STYLE_HASH
    assert model_viewer_style_policy(path) == "style-src 'self' '" + MODEL_VIEWER_STYLE_HASH + "'"
    assert model_viewer_preview_image_policy(path) == "img-src 'self' data: blob:"
    assert model_viewer_connect_policy(path) == "connect-src 'self' blob:"


@pytest.mark.parametrize('path', ['/reviews/new', '/admin/reviews', '/api/leads', '/', '/solutions/review-card/other'])
def test_other_routes_keep_strict_style_and_preview_image_policy(path):
    from server.model_viewer_policy import model_viewer_style_policy, model_viewer_preview_image_policy, model_viewer_connect_policy
    assert model_viewer_style_policy(path) == "style-src 'self'"
    assert model_viewer_preview_image_policy(path) == "img-src 'self' data:"
    assert model_viewer_connect_policy(path) == "connect-src 'self'"


def test_pinned_vendor_stylesheet_matches_csp_hash():
    import base64
    import hashlib
    import os
    import re
    from pathlib import Path
    from server.model_viewer_policy import MODEL_VIEWER_STYLE_HASH
    roots = [Path(__file__).resolve().parents[1] / 'node_modules']
    roots += [Path(p) for p in os.environ.get('NODE_PATH', '').split(os.pathsep) if p]
    bundle = next(root / '@google/model-viewer/dist/model-viewer.min.js' for root in roots
                  if (root / '@google/model-viewer/dist/model-viewer.min.js').exists())
    styles = re.findall(r'<style>(.*?)</style>', bundle.read_text(), re.S)
    assert len(styles) == 1
    assert '${' not in styles[0]
    digest = base64.b64encode(hashlib.sha256(styles[0].encode()).digest()).decode()
    assert 'sha256-' + digest == MODEL_VIEWER_STYLE_HASH
