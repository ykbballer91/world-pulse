CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    request_url TEXT,
    observations_seen INTEGER NOT NULL DEFAULT 0,
    observations_inserted INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_hash TEXT NOT NULL,
    source_id UUID NOT NULL REFERENCES sources(id),
    ingestion_run_id UUID NOT NULL REFERENCES ingestion_runs(id),
    observed_at TIMESTAMPTZ,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, payload_hash)
);

CREATE TABLE IF NOT EXISTS source_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_observation_id UUID NOT NULL REFERENCES raw_observations(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id),
    ingestion_run_id UUID NOT NULL REFERENCES ingestion_runs(id),
    lineage_note TEXT NOT NULL DEFAULT 'raw observation inserted from source payload',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (raw_observation_id, source_id, ingestion_run_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_observations_source_id ON raw_observations(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_observations_ingestion_run_id ON raw_observations(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_raw_observations_observed_at ON raw_observations(observed_at);
CREATE INDEX IF NOT EXISTS idx_source_lineage_raw_observation_id ON source_lineage(raw_observation_id);
CREATE INDEX IF NOT EXISTS idx_source_lineage_source_id ON source_lineage(source_id);
CREATE INDEX IF NOT EXISTS idx_source_lineage_ingestion_run_id ON source_lineage(ingestion_run_id);

INSERT INTO sources (name, source_type, base_url)
VALUES (
    'USGS Earthquake Hazards Program',
    'public_observation_feed',
    'https://earthquake.usgs.gov/fdsnws/event/1/query'
)
ON CONFLICT (name) DO NOTHING;
