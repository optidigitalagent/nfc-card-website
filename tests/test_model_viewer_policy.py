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
