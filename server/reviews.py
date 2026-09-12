"""One review identity, explicit moderation actions, durable persistence before notification."""
from datetime import datetime,timezone,timedelta
import hashlib,json,time,uuid
from psycopg.types.json import Jsonb
from psycopg.errors import UniqueViolation
from .review_security import ReviewError,public_submission,plain,instagram,web_url,identifier,digest

ROLES=('proof','primary_card_location','secondary_business_location')
STATUSES=('draft','pending','verified','published','rejected','archived')
def uid():return str(uuid.uuid4())
def now():return datetime.now(timezone.utc)
def text_id(row):return str(row['id'])

class FakeReviewNotifier:
    def __init__(self,fail=False):self.fail=fail;self.attempts=0
    def send(self,payload):
        self.attempts+=1
        if self.fail:raise OSError('synthetic_notification_failure')

class ReviewService:
    def __init__(self,repository,storage,images,*,secret,origin,notifier=None,clock=time.time,mode='local'):
        if mode=='production' and isinstance(notifier,FakeReviewNotifier):raise ValueError('test_notifier_forbidden_in_production')
        self.repo=repository;self.storage=storage;self.images=images;self.secret=secret;self.origin=origin;self.notifier=notifier if notifier is not None else (FakeReviewNotifier() if mode in ('local','test') else None);self.clock=clock;self.mode=mode

    def limit(self,kind,identity,limit=8,window=600):
        key=kind+':'+digest(self.secret,identity)
        if not self.repo.rate_limit(key,limit,window,self.clock()):raise ReviewError(429,'rate_limited')

    def stage(self,data,filename=''):
        image=self.images.process(data,filename);asset_id=uid();keys=[asset_id+'/'+name for name in ('original','small','large')]
        with self.repo.transaction() as db:db.execute('INSERT INTO review_upload_jobs(id,object_keys,state) VALUES(%s,%s,\'staged\')',(asset_id,Jsonb(keys)))
        try:
            self.storage.put(keys[0],image.original,image.mime)
            derivatives={}
            for size,value in image.variants.items():
                key=asset_id+'/'+size;self.storage.put(key,value['data'],value['mime']);derivatives[size]={k:v for k,v in value.items() if k!='data'};derivatives[size]['key']=key
            return {'id':asset_id,'original_object_key':keys[0],'checksum':image.checksum,'mime_type':image.mime,'byte_size':len(data),'width':image.width,'height':image.height,'derivatives':derivatives}
        except Exception:
            self.abandon(asset_id);raise ReviewError(503,'image_storage_unavailable',{'image':'image'}) from None

    def abandon(self,job_id):
        # Recovery journal precedes storage writes. A failed cleanup remains retryable.
        try:
            with self.repo.transaction() as db:db.execute("UPDATE review_upload_jobs SET state='cleanup',updated_at=NOW() WHERE id=%s AND state<>'attached'",(job_id,))
            self.reconcile(job_id)
        except Exception:pass

    def reconcile(self,job_id=None):
        with self.repo.transaction() as db:
            rows=db.execute("SELECT * FROM review_upload_jobs WHERE (state='cleanup' OR (state='staged' AND created_at<NOW()-INTERVAL '1 hour'))"+(' AND id=%s' if job_id else '')+' FOR UPDATE SKIP LOCKED',(job_id,) if job_id else ()).fetchall()
            for job in rows:
                for key in job['object_keys']:self.storage.delete(key)
                db.execute("UPDATE review_upload_jobs SET state='cleaned',updated_at=NOW() WHERE id=%s",(job['id'],))
            db.execute('DELETE FROM review_fingerprints WHERE expires_at<NOW()');db.execute('DELETE FROM review_idempotency WHERE expires_at<NOW()');db.execute('DELETE FROM review_admin_sessions WHERE expires_at<NOW() OR revoked')
        return len(rows)

    def retention(self,*,rejected_days=180,unused_asset_days=30,apply=False):
        """Bounded, explicit operator action; default is a non-destructive count preview.

        Published reviews and their active publication photos are never removed.
        Object cleanup is journaled in the same transaction as metadata removal.
        """
        if any(type(n) is not int or not 1<=n<=3650 for n in (rejected_days,unused_asset_days)):raise ValueError('invalid_retention_days')
        with self.repo.transaction() as db:
            rows=db.execute("SELECT id FROM client_reviews WHERE status='rejected' AND updated_at<NOW()-(%s*INTERVAL '1 day') ORDER BY updated_at LIMIT 100 FOR UPDATE SKIP LOCKED",(rejected_days,)).fetchall()
            ids=[r['id'] for r in rows]
            assets=db.execute("SELECT a.id FROM client_review_assets a JOIN client_reviews r ON r.id=a.review_id WHERE (a.review_id=ANY(%s::uuid[]) OR ((NOT a.active OR a.role='proof') AND a.created_at<NOW()-(%s*INTERVAL '1 day'))) AND NOT(a.active AND a.role<>'proof' AND r.status='published') ORDER BY a.created_at LIMIT 500 FOR UPDATE OF a SKIP LOCKED",(ids,unused_asset_days)).fetchall()
            asset_ids=[a['id'] for a in assets]
            # Retire selected assets even if one record has more than a batch.
            # Delete the parent only when every asset is included; the next pass progresses.
            purge_ids=[]
            for id in ids:
                remaining=db.execute('SELECT 1 FROM client_review_assets WHERE review_id=%s AND NOT(id=ANY(%s::uuid[])) LIMIT 1',(id,asset_ids)).fetchone()
                if not remaining:purge_ids.append(id)
            ids=purge_ids
            result={'rejectedRecords':len(ids),'unusedAssets':len(assets),'applied':bool(apply)}
            if not apply:return result
            db.execute("UPDATE review_upload_jobs SET state='cleanup',updated_at=NOW() WHERE id=ANY(%s::uuid[])",(asset_ids,))
            db.execute('DELETE FROM client_review_assets WHERE id=ANY(%s::uuid[])',(asset_ids,))
            for table in ('client_review_translations','client_review_audit_events','review_idempotency','review_notification_outbox'):
                from psycopg import sql
                db.execute(sql.SQL('DELETE FROM {} WHERE review_id=ANY(%s::uuid[])').format(sql.Identifier(table)),(ids,))
            db.execute('DELETE FROM client_reviews WHERE id=ANY(%s::uuid[])',(ids,))
            db.execute('INSERT INTO review_retention_events(id,rejected_records,unused_assets) VALUES(%s,%s,%s)',(uid(),len(ids),len(assets)))
        self.reconcile()
        return result

    @staticmethod
    def attach(db,review_id,asset,role,alt=''):
        db.execute('''INSERT INTO client_review_assets(id,review_id,role,original_object_key,checksum,mime_type,byte_size,width,height,derivatives,alt_text,processing_status)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ready')''',(asset['id'],review_id,role,asset['original_object_key'],asset['checksum'],asset['mime_type'],asset['byte_size'],asset['width'],asset['height'],Jsonb(asset['derivatives']),alt))
        db.execute("UPDATE review_upload_jobs SET state='attached',updated_at=NOW() WHERE id=%s",(asset['id'],))

    @staticmethod
    def audit(db,review_id,action,version,actor='admin'):
        db.execute('INSERT INTO client_review_audit_events(id,review_id,action,actor,version) VALUES(%s,%s,%s,%s,%s)',(uid(),review_id,action,actor,version))

    def submit(self,payload,*,image=None,filename='',identity='loopback',manual=False):
        data=public_submission(payload);self.limit('submit',identity)
        request_hash=digest(self.secret,('admin:' if manual else 'public:')+data['request_id'])
        canonical={k:v for k,v in data.items() if k!='request_id'}
        canonical['image_hash']=hashlib.sha256(image).hexdigest() if image else None
        payload_hash=digest(self.secret,json.dumps(canonical,sort_keys=True,ensure_ascii=False))
        with self.repo.transaction() as db:
            prior=db.execute('SELECT i.payload_hash,r.submission_reference,r.id FROM review_idempotency i JOIN client_reviews r ON r.id=i.review_id WHERE request_hash=%s AND expires_at>NOW()',(request_hash,)).fetchone()
            if prior:
                if prior['payload_hash']!=payload_hash:raise ReviewError(409,'idempotency_conflict')
                result={'ok':True,'reference':prior['submission_reference'],'duplicate':True}
                if manual:result['id']=str(prior['id'])
                return result
        staged=self.stage(image,filename) if image else None
        review_id=uid();reference='NFCR-'+uuid.uuid4().hex[:20].upper();duplicate=False
        try:
            with self.repo.transaction() as db:
                db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(request_hash,))
                db.execute('DELETE FROM review_idempotency WHERE request_hash=%s AND expires_at<=NOW()',(request_hash,))
                prior=db.execute('SELECT i.payload_hash,r.submission_reference,r.id FROM review_idempotency i JOIN client_reviews r ON r.id=i.review_id WHERE request_hash=%s AND expires_at>NOW()',(request_hash,)).fetchone()
                if prior:
                    if prior['payload_hash']!=payload_hash:raise ReviewError(409,'idempotency_conflict')
                    reference=prior['submission_reference'];review_id=str(prior['id']);duplicate=True
                else:
                    fp=digest(self.secret,'duplicate:'+payload_hash)
                    db.execute('DELETE FROM review_fingerprints WHERE fingerprint=%s AND expires_at<NOW()',(fp,))
                    if not manual:
                        try:db.execute("INSERT INTO review_fingerprints(fingerprint,expires_at) VALUES(%s,NOW()+INTERVAL '15 minutes')",(fp,))
                        except UniqueViolation:raise ReviewError(409,'duplicate_submission') from None
                    db.execute('''INSERT INTO client_reviews(id,source,status,locale,rating,raw_review_text,instagram_url,publication_consent,consent_recorded_at,submission_reference)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)''',(review_id,'admin' if manual else 'public_form','draft' if manual else 'pending',data['locale'],data['rating'],data['raw_review_text'],data['instagram_url'],not manual,reference))
                    if staged:self.attach(db,review_id,staged,'proof')
                    db.execute("INSERT INTO review_idempotency(request_hash,payload_hash,review_id,expires_at) VALUES(%s,%s,%s,NOW()+INTERVAL '30 days')",(request_hash,payload_hash,review_id))
                    self.audit(db,review_id,'create_draft' if manual else 'submit_pending',1,'admin' if manual else 'public')
                    if not manual:db.execute('INSERT INTO review_notification_outbox(id,review_id,kind) VALUES(%s,%s,%s)',(uid(),review_id,'NEW_NFC_CARD_REVIEW_SUBMISSION'))
        except Exception:
            if staged:self.abandon(staged['id'])
            raise
        if duplicate and staged:self.abandon(staged['id'])
        if not duplicate and not manual:
            try:self.dispatch_outbox(review_id)
            except Exception:pass  # Committed review + outbox remain recoverable.
        result={'ok':True,'reference':reference,'duplicate':duplicate}
        if manual:result['id']=review_id
        return result

    def dispatch_outbox(self,review_id=None):
        if self.notifier is None:return False
        with self.repo.transaction() as db:
            row=db.execute("SELECT * FROM review_notification_outbox WHERE (state IN ('pending','failed') OR (state='sending' AND lease_until<NOW())) AND next_attempt<=NOW()"+(' AND review_id=%s' if review_id else '')+' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED',(review_id,) if review_id else ()).fetchone()
            if not row:return False
            db.execute("UPDATE review_notification_outbox SET state='sending',attempts=attempts+1,lease_until=NOW()+INTERVAL '2 minutes' WHERE id=%s",(row['id'],))
            review=db.execute('SELECT submission_reference,rating,raw_review_text,instagram_url FROM client_reviews WHERE id=%s',(row['review_id'],)).fetchone()
            attached=bool(db.execute("SELECT 1 FROM client_review_assets WHERE review_id=%s AND role='proof' AND active",(row['review_id'],)).fetchone())
        payload={'type':row['kind'],'submissionId':review['submission_reference'],'rating':review['rating'],'preview':review['raw_review_text'][:180],'instagram':review['instagram_url'],'imageAttached':attached,'adminUrl':self.origin+'/admin/reviews/'+str(row['review_id'])}
        try:self.notifier.send(payload);state='sent';error=None
        except Exception:state='failed';error='notification_unavailable'
        with self.repo.transaction() as db:db.execute("UPDATE review_notification_outbox SET state=%s,last_error=%s,lease_until=NULL,next_attempt=NOW()+INTERVAL '1 minute' WHERE id=%s",(state,error,row['id']))
        return state=='sent'

    def row(self,db,review_id,version=None):
        row=db.execute('SELECT * FROM client_reviews WHERE id=%s FOR UPDATE',(identifier(review_id),)).fetchone()
        if not row:raise ReviewError(404,'not_found')
        if version is not None and (type(version) is not int or version!=row['version']):raise ReviewError(409,'stale_version')
        return row

    def admin_list(self,status=None,cursor=None):
        if status and status not in STATUSES:raise ReviewError(422,'invalid_filter')
        offset=0
        if cursor:
            try:
                value,signature=cursor.split('.')
                if not value.isdigit() or not 0<=int(value)<=100000 or signature!=digest(self.secret,'admin-cursor:'+(status or '')+':'+value):raise ValueError()
                offset=int(value)
            except (ValueError,AttributeError):raise ReviewError(422,'invalid_cursor') from None
        with self.repo.transaction() as db:
            rows=db.execute('SELECT id,status,source,locale,rating,business_name,submission_reference,created_at,version FROM client_reviews'+(' WHERE status=%s' if status else '')+' ORDER BY created_at DESC,id LIMIT 101 OFFSET %s',((status,offset) if status else (offset,))).fetchall()
        value=str(offset+100)
        return {'items':rows[:100],'nextCursor':value+'.'+digest(self.secret,'admin-cursor:'+(status or '')+':'+value) if len(rows)>100 else None}

    def admin_get(self,review_id):
        with self.repo.transaction() as db:
            row=self.row(db,review_id)
            row['assets']=db.execute('SELECT id,role,alt_text,width,height,processing_status FROM client_review_assets WHERE review_id=%s AND active',(review_id,)).fetchall()
            row['translations']=db.execute('SELECT locale,public_review_text,primary_alt,secondary_alt,approved FROM client_review_translations WHERE review_id=%s',(review_id,)).fetchall()
            row['audit']=db.execute('SELECT action,version,created_at FROM client_review_audit_events WHERE review_id=%s ORDER BY created_at',(review_id,)).fetchall()
            row['publicationBlockers']=self.gate(db,row)
            return row

    def update(self,review_id,payload):
        if not isinstance(payload,dict) or type(payload.get('version')) is not int:raise ReviewError(422,'version_required')
        allowed={'version','businessName','publicReviewText','instagramUrl','googleMapsUrl','websiteUrl','slug','verifiedCustomer','publicationConsent','featured','sortOrder','privateNote','translations','primaryAlt','secondaryAlt'}
        if not isinstance(payload,dict) or set(payload)-allowed:raise ReviewError(422,'unsupported_fields')
        mapping={'businessName':'business_name','publicReviewText':'public_review_text','googleMapsUrl':'google_maps_url','websiteUrl':'website_url','slug':'slug','verifiedCustomer':'verified_customer','publicationConsent':'publication_consent','featured':'featured','sortOrder':'sort_order','privateNote':'private_verification_note','instagramUrl':'instagram_url'}
        values={}
        for key,value in payload.items():
            if key not in mapping:continue
            if key in ('verifiedCustomer','publicationConsent','featured'):
                if type(value) is not bool:raise ReviewError(422,'validation',{key:key})
            elif key=='sortOrder':
                if type(value) is not int or not -10000<=value<=10000:raise ReviewError(422,'validation',{key:key})
            elif key=='instagramUrl':value=instagram(value)
            elif key in ('googleMapsUrl','websiteUrl'):value=web_url(value,key,'maps' if key=='googleMapsUrl' else 'website',optional=True)
            else:
                value=plain(value,key,0,200 if key=='businessName' else 100 if key=='slug' else 2000)
                if key=='slug' and value:
                    import re
                    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value):raise ReviewError(422,'validation',{key:key})
                value=value or None
            values[mapping[key]]=value
        try:
            with self.repo.transaction() as db:
                row=self.row(db,review_id,payload.get('version'))
                if row['status']=='published':raise ReviewError(409,'unpublish_before_edit')
                for key,value in values.items():row[key]=value
                if values:
                    from psycopg import sql
                    query=sql.SQL('UPDATE client_reviews SET {} ,version=version+1,updated_at=NOW(),consent_recorded_at=CASE WHEN %s THEN COALESCE(consent_recorded_at,NOW()) ELSE consent_recorded_at END WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in values))
                    db.execute(query,(*values.values(),row['publication_consent'],review_id))
                else:db.execute('UPDATE client_reviews SET version=version+1,updated_at=NOW() WHERE id=%s',(review_id,))
                for field,role in [('primaryAlt',ROLES[1]),('secondaryAlt',ROLES[2])]:
                    if field in payload:db.execute('UPDATE client_review_assets SET alt_text=%s WHERE review_id=%s AND role=%s AND active',(plain(payload[field],field,0,300),review_id,role))
                if 'translations' in payload:
                    translations=payload['translations']
                    if not isinstance(translations,list) or len(translations)>2:raise ReviewError(422,'validation',{'translations':'translations'})
                    seen=set()
                    for tr in translations:
                        if not isinstance(tr,dict) or set(tr)!={'locale','publicReviewText','primaryAlt','secondaryAlt','approved'} or tr['locale'] not in ('uk','en') or tr['locale'] in seen or type(tr['approved']) is not bool:raise ReviewError(422,'validation',{'translations':'translations'})
                        seen.add(tr['locale']);body=plain(tr['publicReviewText'],'translations',10,2000);a=plain(tr['primaryAlt'],'translations',1,300);b=plain(tr['secondaryAlt'],'translations',1,300)
                        db.execute('''INSERT INTO client_review_translations(review_id,locale,public_review_text,primary_alt,secondary_alt,approved) VALUES(%s,%s,%s,%s,%s,%s)
                          ON CONFLICT(review_id,locale) DO UPDATE SET public_review_text=EXCLUDED.public_review_text,primary_alt=EXCLUDED.primary_alt,secondary_alt=EXCLUDED.secondary_alt,approved=EXCLUDED.approved''',(review_id,tr['locale'],body,a,b,tr['approved']))
                self.audit(db,review_id,'enrich',row['version']+1)
        except UniqueViolation:raise ReviewError(409,'slug_exists',{'slug':'slug'}) from None
        return self.admin_get(review_id)

    def upload(self,review_id,role,version,data,filename='',alt=''):
        if type(version) is not int:raise ReviewError(422,'version_required')
        if role not in ROLES[1:]:raise ReviewError(422,'invalid_asset_role')
        alt=plain(alt,'alt',0,300)
        with self.repo.transaction() as db:
            row=self.row(db,review_id,version)
            if row['status']=='published':raise ReviewError(409,'unpublish_before_edit')
        staged=self.stage(data,filename)
        try:
            with self.repo.transaction() as db:
                row=self.row(db,review_id,version)
                if row['status']=='published':raise ReviewError(409,'unpublish_before_edit')
                db.execute('UPDATE client_review_assets SET active=FALSE,is_public=FALSE WHERE review_id=%s AND role=%s AND active',(review_id,role))
                self.attach(db,review_id,staged,role,alt)
                db.execute('UPDATE client_reviews SET version=version+1,updated_at=NOW() WHERE id=%s',(review_id,));self.audit(db,review_id,'replace_'+role,row['version']+1)
        except Exception:self.abandon(staged['id']);raise
        return self.admin_get(review_id)

    def gate(self,db,row):
        blockers=[]
        for field in ('public_review_text','business_name','instagram_url','google_maps_url','slug','verified_customer','publication_consent','consent_recorded_at'):
            if not row.get(field):blockers.append(field)
        if row.get('public_review_text') and len(row['public_review_text'])<10:blockers.append('public_review_text')
        assets=db.execute('SELECT * FROM client_review_assets WHERE review_id=%s AND active',(row['id'],)).fetchall()
        chosen=[]
        for role in ROLES[1:]:
            asset=next((a for a in assets if a['role']==role),None)
            if not asset:blockers.append(role);continue
            chosen.append(asset)
            if not asset['alt_text']:blockers.append(role+'_alt')
            if asset['processing_status']!='ready' or set(asset['derivatives'])!={'small','large'}:blockers.append(role+'_derivatives')
        if len(chosen)==2 and chosen[0]['checksum']==chosen[1]['checksum']:blockers.append('two_distinct_photos')
        return blockers

    def action(self,review_id,action,version):
        if type(version) is not int:raise ReviewError(422,'version_required')
        transitions={'submit':({'draft'},'pending'),'verify':({'pending'},'verified'),'publish':({'verified'},'published'),'unpublish':({'published'},'verified'),'reject':({'draft','pending','verified'},'rejected'),'archive':({'draft','pending','verified','published'},'archived'),'restore':({'rejected','archived'},'draft')}
        if action not in transitions:raise ReviewError(422,'invalid_action')
        with self.repo.transaction() as db:
            row=self.row(db,review_id,version);allowed,target=transitions[action]
            if row['status'] not in allowed:raise ReviewError(409,'invalid_transition')
            if action=='verify' and not row['verified_customer']:raise ReviewError(422,'publication_blocked',{'verified_customer':'verified_customer'})
            if action=='publish':
                blockers=self.gate(db,row)
                if blockers:raise ReviewError(422,'publication_blocked',{b:b for b in blockers})
                # Revalidate stored URLs/text at the final boundary, not only on edit.
                instagram(row['instagram_url']);web_url(row['google_maps_url'],'google_maps_url','maps');web_url(row['website_url'],'website_url',optional=True)
                plain(row['public_review_text'],'public_review_text',10,2000);plain(row['business_name'],'business_name',1,200)
            db.execute('''UPDATE client_reviews SET status=%s,version=version+1,updated_at=NOW(),reviewed_at=NOW(),
              published_at=CASE WHEN %s='published' THEN NOW() ELSE published_at END,
              archived_at=CASE WHEN %s='archived' THEN NOW() ELSE archived_at END WHERE id=%s''',(target,target,target,review_id))
            db.execute("UPDATE client_review_assets SET is_public=(active AND role<>'proof' AND %s='published') WHERE review_id=%s",(target,review_id));self.audit(db,review_id,action,row['version']+1)
        return self.admin_get(review_id)

    def public_item(self,db,row,locale,preview=False):
        tr=db.execute('SELECT * FROM client_review_translations WHERE review_id=%s AND locale=%s AND approved',(row['id'],locale)).fetchone()
        # Explicit fallback: approved original language and its original alt text, same identity/rating.
        assets=db.execute('SELECT * FROM client_review_assets WHERE review_id=%s AND active AND role<>\'proof\''+('' if preview else ' AND is_public'),(row['id'],)).fetchall()
        def image(role,alt_field):
            asset=next((a for a in assets if a['role']==role),None)
            if not asset:return None
            d=asset['derivatives']['large'];prefix='/api/admin/reviews/assets/' if preview else '/api/reviews/assets/'
            return {'url':prefix+str(asset['id'])+'/large','alt':tr[alt_field] if tr else asset['alt_text'],'width':d['width'],'height':d['height']}
        return {'id':str(row['id']),'slug':row['slug'],'rating':row['rating'],'reviewText':tr['public_review_text'] if tr else row['public_review_text'],'businessName':row['business_name'],'instagramUrl':row['instagram_url'],'googleMapsUrl':row['google_maps_url'],'websiteUrl':row['website_url'],'primaryImage':image(ROLES[1],'primary_alt'),'secondaryImage':image(ROLES[2],'secondary_alt'),'publishedAt':row['published_at'].isoformat() if row['published_at'] else None}

    def public_list(self,locale='uk',limit=12,cursor=None,featured=None):
        if locale not in ('uk','en') or type(limit) is not int or not 1<=limit<=30:raise ReviewError(422,'invalid_filter')
        offset=0
        if cursor:
            try:
                number,signature=cursor.split('.')
                if not number.isdigit() or not 0<=int(number)<=10000 or digest(self.secret,'cursor:'+number)!=signature:raise ValueError()
                offset=int(number)
            except (ValueError,AttributeError):raise ReviewError(422,'invalid_cursor') from None
        with self.repo.transaction() as db:
            rows=db.execute("SELECT * FROM client_reviews WHERE status='published'"+(' AND featured' if featured else '')+' ORDER BY featured DESC,sort_order,id LIMIT %s OFFSET %s',(limit+1,offset)).fetchall()
            items=[self.public_item(db,row,locale) for row in rows[:limit]]
        next_offset=str(offset+limit);return {'items':items,'nextCursor':next_offset+'.'+digest(self.secret,'cursor:'+next_offset) if len(rows)>limit else None}

    def preview(self,review_id,locale):
        if locale not in ('uk','en'):raise ReviewError(422,'invalid_filter')
        with self.repo.transaction() as db:
            row=self.row(db,review_id);return {'item':self.public_item(db,row,locale,True),'publicationBlockers':self.gate(db,row)}

    def asset(self,asset_id,size,private=False):
        if size not in ('small','large'):raise ReviewError(404,'not_found')
        with self.repo.transaction() as db:
            row=db.execute('''SELECT a.*,r.status FROM client_review_assets a JOIN client_reviews r ON r.id=a.review_id
              WHERE a.id=%s AND a.active''',(identifier(asset_id),)).fetchone()
            if not row or row['processing_status']!='ready' or (not private and (row['status']!='published' or not row['is_public'] or row['role']=='proof')):raise ReviewError(404,'not_found')
            data=row['derivatives'][size]
            try:return self.storage.get(data['key']),data['mime']
            except Exception:raise ReviewError(503,'asset_unavailable') from None
