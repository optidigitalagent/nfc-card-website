"""Shared HTTP policy used by loopback preview and production WSGI adapters."""
from dataclasses import dataclass,field
from email.parser import BytesParser
from email.policy import default
from urllib.parse import urlsplit,parse_qs,unquote
from datetime import datetime
from uuid import UUID
import json,re
from .review_security import ReviewError

@dataclass
class Request:
    method:str;path:str;headers:dict;body:bytes=b'';identity:str='loopback'
@dataclass
class Response:
    status:int=200;body:bytes=b'';headers:dict=field(default_factory=dict)

def serial(value):
    if isinstance(value,(datetime,UUID)):return value.isoformat() if isinstance(value,datetime) else str(value)
    raise TypeError()
def json_response(value,status=200,headers=None):return Response(status,json.dumps(value,ensure_ascii=False,default=serial).encode(),{'Content-Type':'application/json; charset=utf-8',**(headers or {})})
def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate_fields')
        result[key]=value
    return result
def parse_body(request,max_bytes):
    if len(request.body)>max_bytes:raise ReviewError(413,'payload_too_large')
    ctype=request.headers.get('content-type','')
    if ctype.split(';')[0]=='application/json':
        if len(request.body)>32*1024:raise ReviewError(413,'payload_too_large')
        return json.loads(request.body,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError())),None,''
    if not ctype.startswith('multipart/form-data;'):raise ReviewError(415,'unsupported_content_type')
    message=BytesParser(policy=default).parsebytes(('Content-Type: '+ctype+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+request.body)
    if not message.is_multipart() or message.defects:raise ReviewError(400,'invalid_payload')
    fields={};image=None;filename=''
    for part in message.iter_parts():
        name=part.get_param('name',header='content-disposition')
        if name not in ('metadata','image') or name in fields or part.is_multipart() or part.defects:raise ReviewError(400,'invalid_payload')
        raw=part.get_payload(decode=True);fields[name]=True
        if name=='metadata':
            if len(raw)>32*1024 or part.get_filename():raise ReviewError(400,'invalid_payload')
            payload=json.loads(raw,object_pairs_hook=unique)
        else:
            if part.get_filename() is None:raise ReviewError(400,'invalid_payload')
            image=raw;filename=part.get_filename()
    if 'metadata' not in fields:raise ReviewError(400,'invalid_payload')
    return payload,image,filename

class ReviewHTTP:
    def __init__(self,runtime,admin_html):self.runtime=runtime;self.admin_html=admin_html
    @staticmethod
    def handles(path):
        p=unquote(urlsplit(path).path)
        return p.startswith(('/api/reviews','/api/admin','/admin','/en/admin'))
    def dispatch(self,request):
        try:response=self.route(request)
        except ReviewError as error:
            data={'ok':False,'code':error.code}
            if error.fields:data['errors']=error.fields
            if error.reference:data['reference']=error.reference
            response=json_response(data,error.status)
        except (ValueError,UnicodeError,KeyError,TypeError,json.JSONDecodeError,RecursionError):response=json_response({'ok':False,'code':'invalid_payload'},400)
        except Exception:response=json_response({'ok':False,'code':'service_unavailable'},503)
        response.headers.update({'Cache-Control':'no-store, private','X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        if response.status==429:response.headers['Retry-After']='60'
        return response
    def route(self,request):
        runtime=self.runtime;service=runtime.service;auth=runtime.auth;parts=urlsplit(request.path);path=unquote(parts.path).rstrip('/');headers=request.headers
        if '\\' in path or '..' in path.split('/') or len(request.path)>4096:raise ReviewError(400,'invalid_path')
        if headers.get('host')!=urlsplit(runtime.origin).netloc:raise ReviewError(403,'host_rejected')
        if not runtime.enabled:raise ReviewError(503,'reviews_disabled')
        if request.method not in ('GET','HEAD','POST'):raise ReviewError(405,'method_not_allowed')
        if request.method=='POST' and headers.get('origin')!=runtime.origin:raise ReviewError(403,'origin_rejected')
        if len(request.body)>service.images.max_bytes+64*1024:raise ReviewError(413,'payload_too_large')
        query=parse_qs(parts.query,max_num_fields=10)
        if any(len(value)>1 for value in query.values()):raise ReviewError(400,'duplicate_fields')
        locale=query.get('locale',['uk'])[0]
        if path.startswith(('/admin','/en/admin')):
            if request.method not in ('GET','HEAD'):raise ReviewError(405,'method_not_allowed')
            lang='en' if path.startswith('/en/') else 'uk'
            normalized=path.removeprefix('/en')
            if normalized!='/admin/login':
                try:auth.session(headers.get('cookie'))
                except ReviewError:return Response(303,b'',{'Location':('/en' if lang=='en' else '')+'/admin/login'})
            if not re.fullmatch(r'/admin/(?:login|reviews(?:/(?:new|[a-f0-9-]{36}))?)',normalized):raise ReviewError(404,'not_found')
            return Response(200,self.admin_html(lang).encode(),{'Content-Type':'text/html; charset=utf-8'})
        if path=='/api/admin/session' and request.method in ('GET','HEAD'):
            if request.method=='HEAD':return json_response({'ok':True})
            service.limit('session',request.identity,40,600)
            result,cookie=auth.bootstrap(headers.get('cookie'));return json_response(result,headers={'Set-Cookie':cookie} if cookie else {})
        if path=='/api/admin/login' and request.method=='POST':
            payload,_,_=parse_body(request,32*1024)
            if not isinstance(payload,dict) or set(payload)!={'password'}:raise ReviewError(400,'invalid_payload')
            result,cookie=auth.login(headers.get('cookie'),headers.get('x-csrf-token'),payload['password'],request.identity,service.clock());return json_response(result,headers={'Set-Cookie':cookie})
        if path.startswith('/api/admin'):
            auth.session(headers.get('cookie'))
            if request.method=='POST':auth.check_csrf(headers.get('cookie'),headers.get('x-csrf-token'))
            if path=='/api/admin/logout' and request.method=='POST':return json_response({'ok':True},headers={'Set-Cookie':auth.logout(headers.get('cookie'),headers.get('x-csrf-token'))})
            if path=='/api/admin/reviews' and request.method in ('GET','HEAD'):return json_response(service.admin_list(query.get('status',[None])[0],query.get('cursor',[None])[0]))
            if path=='/api/admin/reviews' and request.method=='POST':
                payload,image,filename=parse_body(request,32*1024)
                if image is not None:raise ReviewError(422,'unsupported_fields')
                return json_response(service.submit(payload,manual=True,identity='admin:'+request.identity),201)
            match=re.fullmatch(r'/api/admin/reviews/assets/([a-f0-9-]{36})/(small|large)',path)
            if match and request.method in ('GET','HEAD'):
                data,mime=service.asset(*match.groups(),private=True);return Response(200,data,{'Content-Type':mime})
            match=re.fullmatch(r'/api/admin/reviews/([a-f0-9-]{36})(?:/(preview|update|upload|action))?',path)
            if match:
                review_id,operation=match.groups()
                if request.method in ('GET','HEAD'):
                    if operation=='preview':return json_response(service.preview(review_id,locale))
                    if operation is None:return json_response(service.admin_get(review_id))
                if request.method=='POST':
                    payload,image,filename=parse_body(request,service.images.max_bytes+64*1024)
                    if not isinstance(payload,dict) or type(payload.get('version')) is not int:raise ReviewError(422,'version_required')
                    if operation=='update' and image is None:return json_response(service.update(review_id,payload))
                    if operation=='action' and image is None and set(payload)=={'version','action'}:return json_response(service.action(review_id,payload['action'],payload['version']))
                    if operation=='upload' and image is not None and set(payload)<= {'version','role','alt'}:return json_response(service.upload(review_id,payload.get('role'),payload['version'],image,filename,payload.get('alt','')))
            raise ReviewError(404,'not_found')
        if path=='/api/reviews/options' and request.method in ('GET','HEAD'):
            from .review_images import HEIF
            return json_response({'maxBytes':service.images.max_bytes,'mimeTypes':['image/jpeg','image/png','image/webp']+(['image/heic','image/heif'] if HEIF else [])})
        if path=='/api/reviews' and request.method in ('GET','HEAD'):
            if set(query)-{'locale','limit','cursor','featured'}:raise ReviewError(422,'invalid_filter')
            if query.get('featured',['false'])[0] not in ('true','false'):raise ReviewError(422,'invalid_filter')
            return json_response(service.public_list(locale,int(query.get('limit',['12'])[0]),query.get('cursor',[None])[0],query.get('featured',['false'])[0]=='true'))
        if path=='/api/reviews/submit' and request.method=='POST':
            service.limit('upload',request.identity,15,600)
            payload,image,filename=parse_body(request,service.images.max_bytes+64*1024)
            result=service.submit(payload,image=image,filename=filename,identity=request.identity)
            return json_response(result,200 if result['duplicate'] else 201)
        match=re.fullmatch(r'/api/reviews/assets/([a-f0-9-]{36})/(small|large)',path)
        if match and request.method in ('GET','HEAD'):
            data,mime=service.asset(*match.groups());return Response(200,data,{'Content-Type':mime})
        raise ReviewError(404,'not_found')
