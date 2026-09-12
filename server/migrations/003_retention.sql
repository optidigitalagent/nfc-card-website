-- No personal content is copied into retention logs.
CREATE TABLE review_retention_events (
 id UUID PRIMARY KEY, rejected_records INTEGER NOT NULL, unused_assets INTEGER NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
