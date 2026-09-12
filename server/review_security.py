"""Bounded plain text, safe links and typed review errors."""
import hashlib,hmac,re,uuid,ipaddress
from urllib.parse import urlsplit,urlunsplit

class ReviewError(Exception):
    def __init__(self,status,code,fields=None,reference=None):
        super().__init__(code);self.status=status;self.code=code;self.fields=fields or {};self.reference=reference

def digest(secret,value):return hmac.new(secret.encode(),value.encode(),hashlib.sha256).hexdigest()
def identifier(value):
    try:return str(uuid.UUID(str(value)))
    except (ValueError,TypeError,AttributeError):raise ReviewError(404,'not_found') from None

def plain(value,field,minimum=0,maximum=2000):
    if not isinstance(value,str) or not minimum<=len(value.strip())<=maximum or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',value):raise ReviewError(422,'validation',{field:field})
    # Store plain text only. Raw opinions remain exact; markup is rejected, never silently rewritten.
    if re.search(r'<\s*/?\s*[a-z!][^>]*>',value,re.I):raise ReviewError(422,'validation',{field:field})
    return value.strip()

def web_url(value,field,kind='website',optional=False):
    if optional and value in ('',None):return None
    value=plain(value,field,2,2048)
    if re.search(r'[\s\\]|%0[ad]|%00',value,re.I):raise ReviewError(422,'validation',{field:field})
    try:
        p=urlsplit(value);host=p.hostname or ''
        if p.scheme!='https' or p.username or p.password or p.port not in (None,443) or p.fragment:raise ValueError()
        if kind=='maps':
            short=host in ('maps.app.goo.gl','g.page') and len(p.path)>1
            google=host in ('google.com','www.google.com','google.com.ua','www.google.com.ua','maps.google.com','maps.google.com.ua','google.co.uk','www.google.co.uk') and (p.path=='/maps' or p.path.startswith('/maps/') or host.startswith('maps.'))
            legacy=host=='goo.gl' and p.path.startswith('/maps/') and len(p.path)>6
            if not (short or google or legacy):raise ValueError()
        else:
            if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?',host) or '.' not in host or host.endswith(('.localhost','.local','.internal')):raise ValueError()
            try:
                if not ipaddress.ip_address(host).is_global:raise ValueError()
            except ValueError as exc:
                if re.fullmatch(r'[\d.]+',host):raise exc
        return urlunsplit(('https',host,p.path or '/',p.query,''))
    except (ValueError,UnicodeError):raise ReviewError(422,'validation',{field:field}) from None

def instagram(value):
    value=plain(value,'instagram',2,300)
    if value.startswith('@'):handle=value[1:]
    elif '://' not in value:handle=value
    else:
        try:
            p=urlsplit(value)
            if p.scheme!='https' or p.hostname not in ('instagram.com','www.instagram.com') or p.username or p.password or p.port not in (None,443) or p.query or p.fragment:raise ValueError()
            handle=p.path.strip('/')
        except ValueError:raise ReviewError(422,'validation',{'instagram':'instagram'}) from None
    if not re.fullmatch(r'[A-Za-z0-9_](?:[A-Za-z0-9_.]{0,28}[A-Za-z0-9_])?',handle) or '..' in handle or handle.lower() in ('p','reel','reels','stories','explore','accounts','direct'):raise ReviewError(422,'validation',{'instagram':'instagram'})
    return 'https://www.instagram.com/'+handle.lower()+'/'

def public_submission(payload):
    allowed={'rating','reviewText','instagram','consent','locale','honeypot','clientRequestId'}
    if not isinstance(payload,dict) or set(payload)-allowed:raise ReviewError(422,'unsupported_fields')
    if type(payload.get('rating')) is not int or not 1<=payload['rating']<=5:raise ReviewError(422,'validation',{'rating':'rating'})
    if payload.get('consent') is not True:raise ReviewError(422,'validation',{'consent':'consent'})
    if payload.get('locale') not in ('uk','en'):raise ReviewError(422,'validation',{'locale':'locale'})
    if payload.get('honeypot','')!='':raise ReviewError(422,'spam_rejected')
    return {'rating':payload['rating'],'raw_review_text':plain(payload.get('reviewText'),'reviewText',10,2000),'instagram_url':instagram(payload.get('instagram')),'locale':payload['locale'],'request_id':plain(payload.get('clientRequestId') or str(uuid.uuid4()),'clientRequestId',8,100)}
