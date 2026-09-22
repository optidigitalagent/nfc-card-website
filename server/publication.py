"""Publication policy compiled by the frontend build; never inferred from request headers."""
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib
import json
import os

PREVIEW = 'PUBLIC_PREVIEW'
INDEXABLE = 'PUBLIC_INDEXABLE'
BASE_ROUTES = ('/', '/about', '/solutions', '/solutions/review-card',
               '/solutions/branded-review-card', '/solutions/instagram-card', '/instagram-card', '/delivery-and-payment',
               '/warranty-and-returns', '/privacy', '/terms')
PUBLIC_ROUTES = frozenset(p for route in BASE_ROUTES for p in
                         (route, '/en' + (route if route != '/' else '')))



def content_hash(root):
    digest = hashlib.sha256()
    for name in sorted(p.relative_to(root).as_posix() for p in (root / 'src').rglob('*')
                       if p.is_file() and p.name != 'publication-approval.json'):
        digest.update((name + '\0').encode())
        digest.update((root / name).read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


@dataclass(frozen=True)
class PublicationPolicy:
    mode: str = PREVIEW
    origin: str = ''
    indexable_routes: frozenset = frozenset()

    @classmethod
    def from_build(cls, root, runtime, env=None):
        env = os.environ if env is None else env
        mode = env.get('NFC_PUBLICATION_MODE') or PREVIEW
        if mode not in (PREVIEW, INDEXABLE):
            raise ValueError('invalid_publication_mode')
        if runtime.mode != 'production':
            if mode != PREVIEW:
                raise ValueError('indexing_requires_production_runtime')
            return cls(PREVIEW, runtime.origin)
        data = json.loads((root / 'server/templates/publication.json').read_text('utf-8'))
        if (data.get('schemaVersion') != 1 or data.get('mode') != mode or
                data.get('origin') != runtime.origin or data.get('contentHash') != content_hash(root)):
            raise ValueError('publication_build_runtime_mismatch')
        routes = data.get('indexableRoutes')
        if not isinstance(routes, list) or any(not isinstance(p, str) for p in routes):
            raise ValueError('invalid_indexable_routes')
        selected = frozenset(routes)
        if not selected.issubset(PUBLIC_ROUTES) or (mode == PREVIEW and selected):
            raise ValueError('private_route_indexing_forbidden')
        if mode == INDEXABLE:
            approval = json.loads((root / 'src/publication-approval.json').read_text('utf-8'))
            if (selected != PUBLIC_ROUTES or approval.get('ownerAuthorizedIndexing') is not True or
                    approval.get('publicationInputsConfirmed') is not True or
                    not isinstance(approval.get('approvalReference'), str) or
                    not approval['approvalReference'].strip() or
                    approval.get('reviewedContentSha256') != data['contentHash']):
                raise ValueError('indexing_not_authorized')
        return cls(mode, runtime.origin, selected)

    def robots(self, request_path, status, mime):
        path = unquote(urlsplit(request_path).path)
        # Direct index.html aliases, malformed paths, errors and stateful routes stay noindex.
        if path != '/':
            path = path.rstrip('/')
        if (self.mode == INDEXABLE and status == 200 and mime.startswith('text/html') and
                path in self.indexable_routes):
            return 'index, follow'
        return 'noindex, nofollow'


def cache_control(request_path, response):
    path = unquote(urlsplit(request_path).path)
    if response.status == 200 and 'Set-Cookie' not in response.headers:
        if path.startswith('/assets/') and response.headers.get('Content-Type', '').split(';')[0] != 'text/html':
            return 'public, max-age=3600'
        if path in ('/robots.txt', '/sitemap.xml'):
            return 'public, max-age=300'
    # The accepted renderer hydrates forms on multiple public pages. Never cache their tokens.
    return 'no-store, private'
