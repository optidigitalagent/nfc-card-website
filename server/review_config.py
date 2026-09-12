"""Explicit environment configuration, with no dotenv/default credential discovery."""
from dataclasses import dataclass
from urllib.parse import urlsplit
from pathlib import Path
import os,secrets
from .review_repository import ReviewRepository
from .review_storage import PrivateS3Storage,LocalPrivateStorage
from .review_images import ImageProcessor
from .reviews import ReviewService,FakeReviewNotifier
from .review_auth import AdminAuth

@dataclass
class ReviewRuntime:
    service:ReviewService
    auth:AdminAuth
    origin:str
    mode:str
    enabled:bool=True
    rejected_days:int=180
    unused_asset_days:int=30

def configure(values=None):
    env=dict(os.environ if values is None else values)
    mode=env.get('NFC_ENV','production')
    if mode not in ('production','local','test'):raise ValueError('invalid_runtime_mode')
    origin=env.get('NFC_PUBLIC_ORIGIN','');parts=urlsplit(origin)
    if parts.path not in ('','/') or parts.query or parts.fragment or parts.username or parts.password:raise ValueError('invalid_public_origin')
    if mode=='production' and (parts.scheme!='https' or not parts.hostname or parts.hostname in ('localhost','127.0.0.1')):raise ValueError('production_https_origin_required')
    if mode!='production' and (parts.scheme!='http' or parts.hostname!='127.0.0.1'):raise ValueError('local_origin_must_be_loopback')
    if env.get('NFC_TELEGRAM_ENABLED','false').lower()!='false':raise ValueError('live_notifications_not_authorized')
    dsn=env.get('NFC_DATABASE_URL','')
    if not dsn.startswith(('postgresql://','postgres://')):raise ValueError('postgresql_required')
    secret=env.get('NFC_ADMIN_SESSION_SECRET','');password_hash=env.get('NFC_ADMIN_PASSWORD_HASH','')
    if mode=='production' and (len(secret)<32 or not password_hash.startswith('$argon2id$')):raise ValueError('production_admin_configuration_required')
    secret=secret or secrets.token_hex(32)
    if mode=='production':
        storage=PrivateS3Storage(endpoint=env.get('NFC_S3_ENDPOINT',''),bucket=env.get('NFC_S3_BUCKET',''),region=env.get('NFC_S3_REGION',''),access_key=env.get('NFC_S3_ACCESS_KEY',''),secret_key=env.get('NFC_S3_SECRET_KEY',''))
    else:
        if env.get('NFC_LOCAL_STORAGE_ENABLED')!='true' or not env.get('NFC_LOCAL_STORAGE_PATH'):raise ValueError('explicit_local_storage_required')
        path=Path(env['NFC_LOCAL_STORAGE_PATH']).resolve();site=Path(__file__).resolve().parents[1]/'site'
        if path.is_relative_to(site):raise ValueError('private_storage_cannot_be_public')
        storage=LocalPrivateStorage(path,mode=mode)
    repo=ReviewRepository(dsn)
    if not repo.ready():raise ValueError('review_migrations_required')
    limit=int(env.get('MAX_REVIEW_UPLOAD_MB','10'))
    if not 1<=limit<=20:raise ValueError('invalid_upload_limit')
    service=ReviewService(repo,storage,ImageProcessor(limit*1024*1024),secret=secret,origin=origin.rstrip('/'),mode=mode)
    rejected=int(env.get('NFC_REJECTED_REVIEW_RETENTION_DAYS','180'));unused=int(env.get('NFC_UNUSED_REVIEW_ASSET_RETENTION_DAYS','30'))
    if not all(1<=n<=3650 for n in (rejected,unused)):raise ValueError('invalid_retention_days')
    flag=env.get('NFC_REVIEWS_ENABLED','true')
    if flag not in ('true','false'):raise ValueError('invalid_reviews_feature_flag')
    return ReviewRuntime(service,AdminAuth(repo,secret=secret,password_hash=password_hash,secure=mode=='production'),origin.rstrip('/'),mode,flag=='true',rejected,unused)
