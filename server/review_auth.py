"""Opaque server-side sessions; only CSRF values are returned to JavaScript."""
import hmac,secrets
from http.cookies import SimpleCookie,CookieError
from datetime import datetime,timezone,timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError,InvalidHashError
from .review_security import ReviewError,digest

class AdminAuth:
    cookie_name='nfc_admin_session'
    def __init__(self,repo,*,secret,password_hash='',secure=True,ttl=14400,clock=None):
        if len(secret)<32:raise ValueError('admin_session_secret_required')
        self.repo=repo;self.secret=secret;self.password_hash=password_hash;self.secure=secure;self.ttl=ttl;self.clock=clock or (lambda:datetime.now(timezone.utc));self.verifier=PasswordHasher()
    def token(self,cookies):
        try:
            values=SimpleCookie();values.load(cookies or '');token=values[self.cookie_name].value
            return token if len(token)==64 else None
        except (KeyError,CookieError):return None
    def cookie(self,token,max_age=None):return f'{self.cookie_name}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={self.ttl if max_age is None else max_age}'+('; Secure' if self.secure else '')
    def csrf(self,token):return digest(self.secret,'csrf:'+token)
    def session(self,cookies,require=True):
        token=self.token(cookies)
        if token:
            with self.repo.transaction() as db:row=db.execute('SELECT * FROM review_admin_sessions WHERE session_hash=%s AND NOT revoked AND expires_at>%s',(digest(self.secret,token),self.clock())).fetchone()
            if row and (row['authenticated'] or not require):return token,row
        if require:raise ReviewError(401,'authentication_required')
        return None,None
    def create(self,authenticated=False):
        token=secrets.token_hex(32);expiry=self.clock()+timedelta(seconds=self.ttl if authenticated else 600)
        with self.repo.transaction() as db:db.execute('INSERT INTO review_admin_sessions(session_hash,csrf_hash,expires_at,authenticated) VALUES(%s,%s,%s,%s)',(digest(self.secret,token),digest(self.secret,self.csrf(token)),expiry,authenticated))
        return token
    def bootstrap(self,cookies):
        token,row=self.session(cookies,False);header=None
        if not token:token=self.create();header=self.cookie(token,600)
        return {'authenticated':bool(row and row['authenticated']),'configured':bool(self.password_hash),'csrf':self.csrf(token)},header
    def check_csrf(self,cookies,csrf,require=True):
        token,row=self.session(cookies,require)
        if not token or not isinstance(csrf,str) or not hmac.compare_digest(digest(self.secret,csrf),row['csrf_hash']):raise ReviewError(403,'csrf_rejected')
        return token
    def login(self,cookies,csrf,password,identity,clock_seconds):
        old=self.check_csrf(cookies,csrf,False)
        if not self.repo.rate_limit('login:'+digest(self.secret,identity),8,600,clock_seconds):raise ReviewError(429,'rate_limited')
        if not self.password_hash:raise ReviewError(503,'admin_not_configured')
        if not isinstance(password,str) or not 12<=len(password)<=256:raise ReviewError(401,'invalid_credentials')
        try:valid=self.verifier.verify(self.password_hash,password)
        except (VerificationError,InvalidHashError):valid=False
        if not valid:raise ReviewError(401,'invalid_credentials')
        with self.repo.transaction() as db:db.execute('UPDATE review_admin_sessions SET revoked=TRUE WHERE session_hash=%s',(digest(self.secret,old),))
        token=self.create(True);return {'ok':True,'csrf':self.csrf(token)},self.cookie(token)
    def logout(self,cookies,csrf):
        token=self.check_csrf(cookies,csrf)
        with self.repo.transaction() as db:db.execute('UPDATE review_admin_sessions SET revoked=TRUE WHERE session_hash=%s',(digest(self.secret,token),))
        return self.cookie('',0)
