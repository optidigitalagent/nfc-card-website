"""Route-scoped WebAssembly permission for the NFC product model."""
from urllib.parse import urlsplit

def model_viewer_script_policy(target):
    # Permit the model decoder only on localized product pages using the viewer.
    path=urlsplit(target).path.rstrip('/')
    routes={'/solutions/review-card','/en/solutions/review-card','/pl/solutions/review-card'}
    return "script-src 'self' 'wasm-unsafe-eval'" if path in routes else "script-src 'self'"

