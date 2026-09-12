CREATE TABLE commerce_leads (
 id TEXT PRIMARY KEY, request_hash TEXT NOT NULL UNIQUE, payload_hash TEXT NOT NULL,
 payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE commerce_notification_outbox (
 lead_id TEXT PRIMARY KEY REFERENCES commerce_leads(id),
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','sending','sent','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, lease_until TIMESTAMPTZ,
 next_attempt TIMESTAMPTZ NOT NULL DEFAULT NOW(), last_error TEXT
);
