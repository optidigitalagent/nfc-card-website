"""PostgreSQL repository. No automatic fallback or production schema mutation."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import psycopg
from psycopg.rows import dict_row

class ReviewRepository:
    def __init__(self, dsn):
        self.dsn = dsn

    @contextmanager
    def transaction(self):
        with psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5) as connection:
            connection.execute("SET LOCAL statement_timeout='10s'")
            yield connection

    def migrate(self):
        with self.transaction() as db:
            db.execute('SELECT pg_advisory_xact_lock(91821101)')
            db.execute('CREATE TABLE IF NOT EXISTS nfc_review_migrations (name TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')
            for file in sorted((Path(__file__).parent/'migrations').glob('*.sql')):
                source=file.read_bytes(); checksum=hashlib.sha256(source).hexdigest()
                prior=db.execute('SELECT checksum FROM nfc_review_migrations WHERE name=%s',(file.name,)).fetchone()
                if prior:
                    if prior['checksum'] != checksum: raise ValueError('migration_checksum_drift')
                    continue
                db.execute(source.decode('utf-8'))
                db.execute('INSERT INTO nfc_review_migrations(name,checksum) VALUES(%s,%s)',(file.name,checksum))

    def ready(self):
        with self.transaction() as db:
            if not db.execute("SELECT to_regclass('nfc_review_migrations') name").fetchone()['name']:return False
            applied={r['name']:r['checksum'] for r in db.execute('SELECT name,checksum FROM nfc_review_migrations').fetchall()}
            return all(applied.get(p.name)==hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).parent/'migrations').glob('*.sql'))

    def rate_limit(self, key, limit, window, now):
        bucket=int(now)//window
        with self.transaction() as db:
            row=db.execute('''INSERT INTO review_rate_limits(key,window_start,attempts) VALUES(%s,%s,1)
              ON CONFLICT(key) DO UPDATE SET window_start=EXCLUDED.window_start,
              attempts=CASE WHEN review_rate_limits.window_start=EXCLUDED.window_start THEN review_rate_limits.attempts+1 ELSE 1 END
              RETURNING attempts''',(key,bucket)).fetchone()
            db.execute('DELETE FROM review_rate_limits WHERE window_start < %s AND key LIKE %s',(bucket-2,key.split(':',1)[0]+':%'))
            return row['attempts'] <= limit
