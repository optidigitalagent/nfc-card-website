CREATE TABLE client_reviews (
 id UUID PRIMARY KEY, source TEXT NOT NULL CHECK(source IN ('public_form','admin')),
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('draft','pending','verified','published','rejected','archived')),
 locale TEXT NOT NULL CHECK(locale IN ('uk','en')), rating SMALLINT NOT NULL CHECK(rating BETWEEN 1 AND 5),
 raw_review_text TEXT NOT NULL CHECK(length(raw_review_text) BETWEEN 10 AND 2000),
 public_review_text TEXT, instagram_url TEXT NOT NULL, business_name TEXT, google_maps_url TEXT, website_url TEXT,
 slug TEXT UNIQUE, verified_customer BOOLEAN NOT NULL DEFAULT FALSE, publication_consent BOOLEAN NOT NULL DEFAULT FALSE,
 consent_recorded_at TIMESTAMPTZ, featured BOOLEAN NOT NULL DEFAULT FALSE, sort_order INTEGER NOT NULL DEFAULT 0,
 private_verification_note TEXT, submission_reference TEXT NOT NULL UNIQUE,
 version INTEGER NOT NULL DEFAULT 1 CHECK(version>0), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), reviewed_at TIMESTAMPTZ, published_at TIMESTAMPTZ, archived_at TIMESTAMPTZ
);
CREATE INDEX client_reviews_public ON client_reviews(featured DESC,sort_order,published_at DESC,id) WHERE status='published';
CREATE INDEX client_reviews_queue ON client_reviews(status,created_at DESC,id);
CREATE TABLE client_review_translations (
 review_id UUID NOT NULL REFERENCES client_reviews(id), locale TEXT NOT NULL CHECK(locale IN ('uk','en')),
 public_review_text TEXT NOT NULL CHECK(length(public_review_text) BETWEEN 10 AND 2000),
 primary_alt TEXT NOT NULL, secondary_alt TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE,
 PRIMARY KEY(review_id,locale)
);
CREATE TABLE client_review_assets (
 id UUID PRIMARY KEY, review_id UUID NOT NULL REFERENCES client_reviews(id),
 role TEXT NOT NULL CHECK(role IN ('proof','primary_card_location','secondary_business_location')),
 original_object_key TEXT NOT NULL, checksum TEXT NOT NULL, mime_type TEXT NOT NULL,
 byte_size BIGINT NOT NULL CHECK(byte_size>0), width INTEGER NOT NULL CHECK(width>0), height INTEGER NOT NULL CHECK(height>0),
 derivatives JSONB NOT NULL, alt_text TEXT NOT NULL DEFAULT '', processing_status TEXT NOT NULL CHECK(processing_status IN ('ready','failed')),
 is_public BOOLEAN NOT NULL DEFAULT FALSE, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX client_review_assets_current ON client_review_assets(review_id,role) WHERE active;
CREATE TABLE client_review_audit_events (
 id UUID PRIMARY KEY, review_id UUID NOT NULL REFERENCES client_reviews(id), action TEXT NOT NULL,
 actor TEXT NOT NULL, version INTEGER NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE review_idempotency (
 request_hash TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, review_id UUID NOT NULL REFERENCES client_reviews(id),
 expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE review_fingerprints (
 fingerprint TEXT PRIMARY KEY, expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE review_rate_limits (
 key TEXT PRIMARY KEY, window_start BIGINT NOT NULL, attempts INTEGER NOT NULL CHECK(attempts>0)
);
CREATE TABLE review_upload_jobs (
 id UUID PRIMARY KEY, object_keys JSONB NOT NULL, state TEXT NOT NULL CHECK(state IN ('staged','attached','cleanup','cleaned')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE review_notification_outbox (
 id UUID PRIMARY KEY, review_id UUID NOT NULL REFERENCES client_reviews(id), kind TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','sending','sent','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, lease_until TIMESTAMPTZ, next_attempt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 last_error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(review_id,kind)
);
CREATE INDEX review_outbox_ready ON review_notification_outbox(next_attempt) WHERE state<>'sent';
CREATE TABLE review_admin_sessions (
 session_hash TEXT PRIMARY KEY, csrf_hash TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), revoked BOOLEAN NOT NULL DEFAULT FALSE,
 authenticated BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE FUNCTION guard_review_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.rating<>OLD.rating OR NEW.raw_review_text<>OLD.raw_review_text OR NEW.source<>OLD.source OR NEW.locale<>OLD.locale THEN
  RAISE EXCEPTION 'immutable_review_origin';
 END IF;
 IF NEW.status<>OLD.status AND NOT (
  (OLD.status='draft' AND NEW.status IN ('pending','rejected','archived')) OR
  (OLD.status='pending' AND NEW.status IN ('verified','rejected','archived')) OR
  (OLD.status='verified' AND NEW.status IN ('published','pending','rejected','archived')) OR
  (OLD.status='published' AND NEW.status IN ('verified','archived')) OR
  (OLD.status IN ('rejected','archived') AND NEW.status='draft')
 ) THEN RAISE EXCEPTION 'invalid_review_transition'; END IF;
 IF NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'invalid_review_version'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER review_update_guard BEFORE UPDATE ON client_reviews FOR EACH ROW EXECUTE FUNCTION guard_review_update();
