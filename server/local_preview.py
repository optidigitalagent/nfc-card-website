"""Explicit local launcher. No fixture, default password or external notifications."""
import argparse,os,secrets
from http.server import ThreadingHTTPServer
from pathlib import Path
from .review_config import configure
from .review_http import ReviewHTTP
from .commerce_repository import PostgresLeadService
from .preview import Handler,ROOT
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state',type=Path,required=True);parser.add_argument('--port',type=int,default=8765);parser.add_argument('--database-url',required=True);args=parser.parse_args()
    state=args.state.resolve()
    if state.is_relative_to((ROOT/'site').resolve()):raise ValueError('private_preview_state_required')
    state.mkdir(parents=True,exist_ok=True);secret_file=state/'session-secret.txt'
    if not secret_file.exists():
        with secret_file.open('x',encoding='utf-8') as f:f.write(secrets.token_hex(32))
    values={'NFC_ENV':'local','NFC_DATABASE_URL':args.database_url,'NFC_PUBLIC_ORIGIN':f'http://127.0.0.1:{args.port}','NFC_LOCAL_STORAGE_ENABLED':'true','NFC_LOCAL_STORAGE_PATH':str(state/'objects'),'NFC_ADMIN_SESSION_SECRET':secret_file.read_text('utf-8'),'NFC_ADMIN_PASSWORD_HASH':os.environ.get('NFC_ADMIN_PASSWORD_HASH',''),'NFC_TELEGRAM_ENABLED':'false'}
    runtime=configure(values);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.leads=PostgresLeadService(runtime.service.repo,secret=runtime.service.secret,mode='local')
    server.reviews=ReviewHTTP(runtime,lambda lang:(ROOT/'server/templates'/f'admin-{lang}.html').read_text('utf-8'))
    print(f'NFC CARD local: http://127.0.0.1:{args.port}; admin '+('configured' if values['NFC_ADMIN_PASSWORD_HASH'] else 'requires owner password hash')+'; no live notifications.',flush=True)
    server.serve_forever()
if __name__=='__main__':main()
