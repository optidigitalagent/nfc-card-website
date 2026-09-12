"""Frozen v1 normalization for matching already-saved retries only. Never creates leads."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from threading import RLock
from pathlib import Path
from urllib.parse import urlsplit
from typing import Protocol

MAX_LOGO = 10 * 1024 * 1024
PRODUCTS = {'review-card', 'counter-stand', 'team-kit', 'multi-location', 'help'}
LIMITS = {'name':120,'business':200,'city':200,'maps':2048,'contact':250,'comment':2000,'addresses':4000,'locationMaps':10000,'responsible':250,'topic':200,'message':2000,'source':250}

try:
    from .errors import LeadError
except ImportError:
    from errors import LeadError

def maps_url(value):
    try:
        u=urlsplit(value)
        if u.scheme!='https' or u.username or u.password or u.port not in (None,443): return False
        host=(u.hostname or '').lower()
        if host in {'maps.app.goo.gl','g.page'}: return bool(u.path.strip('/'))
        if host=='goo.gl': return u.path.startswith('/maps/') and len(u.path)>6
        if host in {'maps.google.com','maps.google.com.ua','maps.google.co.uk'}: return True
        if host in {'google.com','www.google.com','google.com.ua','www.google.com.ua','google.co.uk','www.google.co.uk'}:
            return u.path=='/maps' or u.path.startswith('/maps/')
    except (ValueError,TypeError): pass
    return False

def valid_contact(value):
    if not isinstance(value,str): return False
    value=value.strip()
    return bool(re.fullmatch(r'@[A-Za-z][A-Za-z0-9_]{4,31}',value) or
        re.fullmatch(r'https://t\.me/[A-Za-z][A-Za-z0-9_]{4,31}',value) or
        re.fullmatch(r'[^\s@<>]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}',value) or
        (re.fullmatch(r'\+?[\d ()-]+',value) and 7<=len(re.sub(r'\D','',value))<=15))

def clean_logo(logo):
    """Decode and re-encode a raster, stripping metadata and never serving originals."""
    if not logo: return None
    if not isinstance(logo,dict) or set(logo)-{'name','type','data'}: raise LeadError(422,'validation',{'logo':'logo'})
    if not isinstance(logo.get('type'),str) or logo['type'] not in {'image/png','image/jpeg'}: raise LeadError(422,'validation',{'logo':'logo'})
    data=logo.get('data')
    if not isinstance(data,str) or len(data)>MAX_LOGO*4//3+8: raise LeadError(422,'validation',{'logo':'logo'})
    try:
        raw=base64.b64decode(data,validate=True)
        if len(raw)>MAX_LOGO or len(raw)==0: raise ValueError()
        from PIL import Image
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in {'PNG','JPEG'} or (im.format=='PNG')!=(logo['type']=='image/png'): raise ValueError()
            if im.width*im.height>16000000 or min(im.size)<1: raise ValueError()
            im.load()
            if getattr(im,'n_frames',1)>1: raise ValueError()
            safe=im.convert('RGBA' if im.format=='PNG' else 'RGB')
            stream=io.BytesIO()
            safe.save(stream,format='PNG' if im.format=='PNG' else 'JPEG')
            result=stream.getvalue()
            if len(result)>MAX_LOGO: raise ValueError()
        return {'mime':logo['type'],'bytes':result,'sha256':hashlib.sha256(result).hexdigest()}
    except Exception:
        raise LeadError(422,'validation',{'logo':'logo'}) from None

def normalize_legacy(payload):
    if not isinstance(payload,dict): raise LeadError(400,'invalid_payload')
    if payload.get('website'): raise LeadError(422,'spam_rejected')
    if not isinstance(payload.get('locale'),str) or not isinstance(payload.get('language'),str) or payload['locale'] not in {'uk','en'} or payload['language'] not in {'uk','en'}: raise LeadError(422,'invalid_locale')
    kind=payload.get('kind','order')
    if not isinstance(kind,str) or kind not in {'order','contact'}: raise LeadError(422,'invalid_kind')
    result={'kind':kind,'locale':payload['locale'],'language':payload['language'],'consent':True,'is_test':True}
    errors={}
    for key,limit in LIMITS.items():
        v=payload.get(key,'')
        if not isinstance(v,str) or len(v)>limit:
            errors[key]=key; continue
        result[key]=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]','',v).strip()
    for key in (['name','business','topic','message'] if kind=='contact' else ['name','business','city']):
        if not result.get(key): errors[key]=key
    if not valid_contact(result.get('contact')): errors['contact']='contact'
    if payload.get('consent') is not True: errors['consent']='consent'
    result['product']=payload.get('product','help' if kind=='contact' else '')
    if not isinstance(result['product'],str) or result['product'] not in PRODUCTS: errors['product']='product'
    def positive(key,default=None):
        value=payload.get(key,default)
        if isinstance(value,bool) or not re.fullmatch(r'[1-9]\d{0,3}',str(value or '')):
            errors[key]=key;return None
        return int(value)
    result['quantity']=positive('quantity',1 if kind=='contact' else None)
    if kind=='order' and (result['product']!='help' or result.get('maps')) and not maps_url(result.get('maps','')): errors['maps']='maps'
    if kind=='order' and result['product']=='multi-location':
        result['locations']=positive('locations');result['perLocation']=positive('perLocation')
        if not result.get('addresses'):errors['addresses']='addresses'
        links=result.get('locationMaps','').splitlines()
        if len(links)!=(result.get('locations') or 0) or not all(maps_url(u.strip()) for u in links):errors['locationMaps']='locationMaps'
        if not valid_contact(result.get('responsible')):errors['responsible']='responsible'
    else:
        for key in ['locations','perLocation','addresses','locationMaps','responsible']:result.pop(key,None)
    source=result.get('source','')
    if not source.startswith('/') or source.startswith('//') or '?' in source or '#' in source: result['source']='/'
    # UTM are retained only in private storage, never passed to the analytics adapter.
    utm=payload.get('utm',{})
    if not isinstance(utm,dict):raise LeadError(422,'invalid_utm')
    result['utm']={k:v for k,v in utm.items() if k in {'utm_source','utm_medium','utm_campaign','utm_content','utm_term'} and isinstance(v,str) and len(v)<=200}
    key=payload.get('idempotencyKey','')
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',key):raise LeadError(400,'invalid_idempotency_key')
    if errors:raise LeadError(422,'validation',errors)
    logo=clean_logo(payload.get('logo'))
    result['has_logo']=logo is not None
    if logo:result['logo_sha256']=logo['sha256']
    return key,result,logo

def legacy_telegram_message(lead_id,created,lead):
    """Blueprint §13, plain text: no HTML/Markdown injection and no public file URL."""
    message='\n'.join([
        '🆕 Нова заявка NFC CARD','',f'Номер: {lead_id}',f'Дата і час: {created}',
        f'Мова: {lead["language"].upper()}',f'Джерело: {lead["source"]}', '',
        f'Ім’я: {lead["name"]}',f'Бізнес: {lead["business"]}',f'Продукт: {lead["product"]}',
        f'Кількість: {lead["quantity"]}',f'Місто / країна: {lead.get("city", "")}',
        f'Google Maps: {lead.get("maps", "")}',f'Контакт: {lead["contact"]}', '',
        'Логотип: '+('збережений у приватному сховищі' if lead['has_logo'] else 'не додано'),
        f'Коментар: {lead.get("comment") or lead.get("message", "")}', '', 'Згода з privacy: так'
    ]+([f'Локацій: {lead.get("locations")}',f'Адреси: {lead.get("addresses")}',f'Посилання локацій: {lead.get("locationMaps")}',f'Виробів на точку: {lead.get("perLocation")}',f'Відповідальна особа: {lead.get("responsible")}'] if lead['product']=='multi-location' else []))
    if len(message)>3900:message=message[:3800]+'\n\nСкорочено. Повні дані — у приватному сховищі заявки '+lead_id
    return message

