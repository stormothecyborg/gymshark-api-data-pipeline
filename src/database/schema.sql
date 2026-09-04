CREATE TABLE IF NOT EXISTS raw_listings (
    raw_id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    request_id TEXT NOT NULL,
    raw_payload JSONB NOT NULL,
    listing_url TEXT
);

CREATE TABLE IF NOT EXISTS listings (
    listing_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT,
    category TEXT,
    brand TEXT,
    product_url TEXT,
    sku TEXT,
    currency TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS listing_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    listing_id TEXT NOT NULL,
    source TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    price NUMERIC,
    old_price NUMERIC,
    availability BOOLEAN,
    raw_id BIGINT REFERENCES raw_listings(raw_id),
    UNIQUE (listing_id, source, observed_at)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    source TEXT NOT NULL,
    rows_extracted INTEGER,
    rows_cleaned INTEGER,
    rows_rejected INTEGER,
    status TEXT NOT NULL,
    error_message TEXT,
    duration_seconds NUMERIC
);

CREATE TABLE IF NOT EXISTS listing_features (
    listing_id TEXT NOT NULL,
    source TEXT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL,
    current_price NUMERIC,
    price_change_pct_7d NUMERIC,
    price_change_pct_30d NUMERIC,
    days_tracked INTEGER,
    is_available BOOLEAN,
    availability_change_count INTEGER,
    PRIMARY KEY (listing_id, source, computed_at)
);

CREATE INDEX IF NOT EXISTS idx_listing_snapshots_listing_id
    ON listing_snapshots (listing_id);

CREATE INDEX IF NOT EXISTS idx_listing_snapshots_observed_at
    ON listing_snapshots (observed_at);
