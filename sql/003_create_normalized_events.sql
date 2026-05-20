CREATE TABLE IF NOT EXISTS normalized_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_observation_id UUID NOT NULL REFERENCES raw_observations(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id),
    event_type TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    event_time TIMESTAMPTZ,
    magnitude_value DOUBLE PRECISION,
    location_label TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,
    normalized_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (raw_observation_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_normalized_events_raw_observation_id
    ON normalized_events(raw_observation_id);

CREATE INDEX IF NOT EXISTS idx_normalized_events_source_id
    ON normalized_events(source_id);

CREATE INDEX IF NOT EXISTS idx_normalized_events_event_type
    ON normalized_events(event_type);

CREATE INDEX IF NOT EXISTS idx_normalized_events_category
    ON normalized_events(category);

CREATE INDEX IF NOT EXISTS idx_normalized_events_event_time
    ON normalized_events(event_time);

CREATE INDEX IF NOT EXISTS idx_normalized_events_anomaly_score
    ON normalized_events(anomaly_score);
