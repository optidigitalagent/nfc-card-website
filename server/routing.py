"""Canonical product routing with a small, shared query allowlist."""
from urllib.parse import urlsplit,parse_qsl,urlencode,unquote
import re
PRODUCTS={'standard':'/solutions/review-card','branded':'/solutions/branded-review-card'}
def product_redirect(target):
    parts=urlsplit(target);path=unquote(parts.path).rstrip('/');prefix='/en' if path.startswith('/en/') else '';route=path.removeprefix(prefix)
    if route not in PRODUCTS.values():return None
    try:query=dict(parse_qsl(parts.query,max_num_fields=40))
    except ValueError:query={}
    if 'variant' not in query:return None
    chosen=query.get('variant');variant=chosen if chosen in PRODUCTS else 'branded' if 'branded-' in route else 'standard'
    safe={k:v for k,v in query.items() if k in ('utm_source','utm_medium','utm_campaign','utm_content','utm_term') and len(v)<=200 and not re.search(r'[\x00-\x1f\x7f]',v)}
    if query.get('quantity') in ('1','2','more'):safe['quantity']=query['quantity']
    source=query.get('source','')
    if re.fullmatch(r'/(?:en/)?(?:solutions(?:/(?:branded-)?review-card)?|order|contact)?',source):safe['source']=source
    return prefix+PRODUCTS[variant]+('?' + urlencode(safe) if safe else '')
