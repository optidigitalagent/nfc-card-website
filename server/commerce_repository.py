"""PostgreSQL commerce adapter using the existing intent and canonical pricing contract."""
import time,uuid
from datetime import datetime,timezone
from psycopg.types.json import Jsonb
from .leads import normalize,encode,canonical_quote,load_commerce,receipt,displayed_price_observation,telegram_message,MockNotifier,CONSENT_VERSION,LeadError
from .review_security import digest

class PostgresLeadService:
    def __init__(self,repo,*,secret,mode='local',notifier=None,clock=time.time):
        if mode=='production' and isinstance(notifier,MockNotifier):raise ValueError('test_notifier_forbidden_in_production')
        self.repo=repo;self.secret=secret;self.mode=mode;self.notifier=notifier if notifier is not None else (MockNotifier() if mode in ('local','test') else None);self.clock=clock;self.commerce=load_commerce()
    def result(self,row,duplicate):
        value=receipt(row['id'],row['payload'],duplicate)
        value['mode']='saved' if self.mode=='production' else 'local_test'
        return {'ok':True,'receipt':value}
    def submit(self,payload,client='loopback'):
        if not self.repo.rate_limit('lead:'+digest(self.secret,client),30,60,self.clock()):raise LeadError(429,'rate_limited')
        if not isinstance(payload,dict) or payload.get('contractVersion')!=6:raise LeadError(422,'legacy_contract_retired')
        key,intent=normalize(payload);key=digest(self.secret,key);fingerprint=digest(self.secret,encode(intent))
        with self.repo.transaction() as db:
            db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(key,))
            row=db.execute('SELECT * FROM commerce_leads WHERE request_hash=%s',(key,)).fetchone()
            if row:
                if row['payload_hash']!=fingerprint:raise LeadError(409,'idempotency_conflict')
                return self.result(row,True)
            lead_id='NFC-'+uuid.uuid4().hex[:20].upper()
            lead={**intent,'quote':canonical_quote(intent['variant'],intent['quantity'],self.commerce),
                  'displayed_price':displayed_price_observation(payload.get('displayed_price')),
                  'physicalProduct':intent.get('product_id', self.commerce['physicalProduct']['id']),'consentVersion':CONSENT_VERSION,
                  'consentAcceptedAt':datetime.fromtimestamp(self.clock(),timezone.utc).isoformat(),'is_test':self.mode!='production'}
            db.execute('INSERT INTO commerce_leads(id,request_hash,payload_hash,payload) VALUES(%s,%s,%s,%s)',(lead_id,key,fingerprint,Jsonb(lead)))
            db.execute('INSERT INTO commerce_notification_outbox(lead_id) VALUES(%s)',(lead_id,))
        try:self.dispatch(lead_id)
        except Exception:pass
        return self.result({'id':lead_id,'payload':lead},False)
    def dispatch(self,lead_id=None):
        if self.notifier is None:return False
        with self.repo.transaction() as db:
            row=db.execute("SELECT * FROM commerce_notification_outbox WHERE (state IN ('pending','failed') OR (state='sending' AND lease_until<NOW())) AND next_attempt<=NOW()"+(' AND lead_id=%s' if lead_id else '')+' ORDER BY next_attempt LIMIT 1 FOR UPDATE SKIP LOCKED',(lead_id,) if lead_id else ()).fetchone()
            if not row:return False
            db.execute("UPDATE commerce_notification_outbox SET state='sending',attempts=attempts+1,lease_until=NOW()+INTERVAL '2 minutes' WHERE lead_id=%s",(row['lead_id'],))
            lead=db.execute('SELECT * FROM commerce_leads WHERE id=%s',(row['lead_id'],)).fetchone()
        try:self.notifier.send(lead['id'],telegram_message(lead['id'],lead['created_at'].timestamp(),lead['payload']));state='sent';error=None
        except Exception:state='failed';error='notification_unavailable'
        with self.repo.transaction() as db:db.execute("UPDATE commerce_notification_outbox SET state=%s,last_error=%s,lease_until=NULL,next_attempt=NOW()+INTERVAL '1 minute' WHERE lead_id=%s",(state,error,lead['id']))
        return state=='sent'
