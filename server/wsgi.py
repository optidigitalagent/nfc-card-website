"""Deployable WSGI boundary. Import requires explicit configured, migrated infrastructure.

Run with a production WSGI server, e.g. gunicorn server.wsgi:application.
This module performs no provisioning, migration or live notification.
"""
import json,mimetypes,re
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qsl
from .review_config import configure
from .review_http import ReviewHTTP,Request,Response,json_response,unique
from .commerce_repository import PostgresLeadService
from .leads import LeadError
from .routing import product_redirect
from .publication import PublicationPolicy,cache_control

ROOT=Path(__file__).resolve().parents[1]
class Application:
    def __init__(self,runtime):
        self.publication=PublicationPolicy.from_build(ROOT,runtime)
        self.runtime=runtime;self.reviews=ReviewHTTP(runtime,lambda lang:(ROOT/'server/templates'/f'admin-{lang}.html').read_text('utf-8'))
        self.leads=PostgresLeadService(runtime.service.repo,secret=runtime.service.secret,mode=runtime.mode)
    def route(self,request):
        if ReviewHTTP.handles(request.path):return self.reviews.dispatch(request)
        if request.path=='/healthz' and request.method in ('GET','HEAD') and request.headers.get('host')=='healthcheck.railway.app':
            ready=self.runtime.service.repo.ready()
            return json_response({'ok':ready,'publicationMode':self.publication.mode,'database':'ready' if ready else 'unavailable','storage':'configured_not_probed'},200 if ready else 503)
        if request.headers.get('host')!=urlsplit(self.runtime.origin).netloc:return json_response({'ok':False,'code':'host_rejected'},403)
        path=unquote(urlsplit(request.path).path)
        if path=='/healthz' and request.method in ('GET','HEAD'):
            ready=self.runtime.service.repo.ready()
            return json_response({'ok':ready,'publicationMode':self.publication.mode,'database':'ready' if ready else 'unavailable','storage':'configured_not_probed'},200 if ready else 503)
        if path=='/api/leads' and request.method=='POST':
            if request.headers.get('origin')!=self.runtime.origin:return json_response({'ok':False,'code':'origin_rejected'},403)
            if len(request.body)>65536:return json_response({'ok':False,'code':'payload_too_large'},413)
            mime=request.headers.get('content-type','').split(';')[0]
            if mime=='application/json':payload=json.loads(request.body,object_pairs_hook=unique)
            elif mime=='application/x-www-form-urlencoded':
                payload=unique(parse_qsl(request.body.decode('utf-8'),keep_blank_values=True,max_num_fields=40))
                payload['contractVersion']=int(payload.get('contractVersion','0'));payload['consent']=payload.get('consent') in ('yes','on','true');payload['differentContact']=False
                if 'attribution' in payload:payload['attribution']=json.loads(payload['attribution'],object_pairs_hook=unique)
            else:return json_response({'ok':False,'code':'unsupported_content_type'},415)
            result=self.leads.submit(payload,request.identity);return json_response(result,200 if result['receipt']['duplicate'] else 201)
        if request.method not in ('GET','HEAD'):return json_response({'ok':False,'code':'method_not_allowed'},405)
        redirect=product_redirect(request.path)
        if not redirect:redirect=json.loads((ROOT/'src/redirects.json').read_text('utf-8-sig')).get(path.rstrip('/'))
        if redirect:return Response(301,b'',{'Location':redirect})
        if path.startswith('/api/'):return json_response({'ok':False,'code':'not_found'},404)
        site=(ROOT/'site').resolve();file=(site/path.lstrip('/')).resolve()
        if not file.is_relative_to(site) or '\\' in path:return Response(404,b'Not found')
        if file.is_dir():file=file/'index.html'
        if not file.is_file() or file.name.startswith('.') or any(p.startswith('.') for p in file.relative_to(site).parts):return Response(404,b'Not found')
        data=file.read_bytes()
        if file.suffix=='.html':
            from .preview import hydrate_native_form
            import uuid
            source=data.decode('utf-8');source=re.sub(r'(name="requestToken"[^>]*value=")[^"]*',lambda m:m[1]+str(uuid.uuid4()),source)
            data=hydrate_native_form(source,request.path,self.leads.commerce).encode()
        return Response(200,data,{'Content-Type':mimetypes.guess_type(file)[0] or 'application/octet-stream'})
    def __call__(self,environ,start_response):
        method=environ.get('REQUEST_METHOD','GET');headers={k[5:].lower().replace('_','-'):v for k,v in environ.items() if k.startswith('HTTP_')};headers['content-type']=environ.get('CONTENT_TYPE','')
        try:
            length=environ.get('CONTENT_LENGTH','') or '0'
            if not re.fullmatch(r'[0-9]{1,9}',length) or 'transfer-encoding' in headers:response=json_response({'ok':False,'code':'invalid_length'},400)
            elif int(length)>self.runtime.service.images.max_bytes+65536:response=json_response({'ok':False,'code':'payload_too_large'},413)
            else:
                body=environ['wsgi.input'].read(int(length))
                if len(body)!=int(length):response=json_response({'ok':False,'code':'incomplete_payload'},400)
                else:response=self.route(Request(method,environ.get('PATH_INFO','/')+('?' + environ['QUERY_STRING'] if environ.get('QUERY_STRING') else ''),headers,body,environ.get('REMOTE_ADDR','unknown')))
        except LeadError as e:response=json_response({'ok':False,'code':e.code,'errors':e.fields},e.status)
        except (ValueError,TypeError,UnicodeError,RecursionError):response=json_response({'ok':False,'code':'invalid_payload'},400)
        except Exception:response=json_response({'ok':False,'code':'service_unavailable'},503)
        response.headers.update({'X-Content-Type-Options':'nosniff','Cache-Control':cache_control(environ.get('PATH_INFO','/'),response),'X-Robots-Tag':self.publication.robots(environ.get('PATH_INFO','/'),response.status,response.headers.get('Content-Type','')),'Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; media-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
        response.headers['Content-Length']=str(len(response.body));start_response(f'{response.status} {HTTPStatus(response.status).phrase}',list(response.headers.items()))
        return [b'' if method=='HEAD' else response.body]

def create_application():return Application(configure())
def application(environ,start_response):
    global _configured
    if _configured is None:
        try:_configured=create_application()
        except Exception:
            body=b'{"ok":false,"code":"service_unavailable"}'
            start_response('503 Service Unavailable',[('Content-Type','application/json'),('Content-Length',str(len(body))),('Cache-Control','no-store, private'),('X-Robots-Tag','noindex, nofollow'),('X-Content-Type-Options','nosniff')])
            return [b'' if environ.get('REQUEST_METHOD')=='HEAD' else body]
    return _configured(environ,start_response)
_configured=None
