"""Permit only the pinned model viewer's requirements on product routes."""
from urllib.parse import urlsplit

MODEL_VIEWER_STYLE_HASH = "sha256-PXtZZkJMMyc18o/DN1ZEFOJ2qEGq95IQbVaJFMOXOb0="
_MODEL_ROUTES = {'/solutions/review-card', '/en/solutions/review-card', '/pl/solutions/review-card'}


def _uses_model_viewer(target):
    return urlsplit(target).path.rstrip('/') in _MODEL_ROUTES


def model_viewer_script_policy(target):
    return "script-src 'self' 'wasm-unsafe-eval'" if _uses_model_viewer(target) else "script-src 'self'"


def model_viewer_style_policy(target):
    # Exact static shadow stylesheet from pinned @google/model-viewer 4.4.0.
    return "style-src 'self' '" + MODEL_VIEWER_STYLE_HASH + "'" if _uses_model_viewer(target) else "style-src 'self'"


def model_viewer_preview_image_policy(target):
    return "img-src 'self' data: blob:" if _uses_model_viewer(target) else "img-src 'self' data:"


def model_viewer_connect_policy(target):
    return "connect-src 'self' blob:" if _uses_model_viewer(target) else "connect-src 'self'"
