CREATE TABLE IF NOT EXISTS baseline_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    metric_key TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 0,
    mean_value DOUBLE PRECISION,
    median_value DOUBLE PRECISION,
    stddev_value DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    p50_value DOUBLE PRECISION,
    p75_value DOUBLE PRECISION,
    p90_value DOUBLE PRECISION,
    p95_value DOUBLE PRECISION,
    p99_value DOUBLE PRECISION,
    distribution_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, metric_key, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_baseline_distributions_source_id
    ON baseline_distributions(source_id);

CREATE INDEX IF NOT EXISTS idx_baseline_distributions_metric_key
    ON baseline_distributions(metric_key);

CREATE INDEX IF NOT EXISTS idx_baseline_distributions_window_start
    ON baseline_distributions(window_start);

CREATE INDEX IF NOT EXISTS idx_baseline_distributions_window_end
    ON baseline_distributions(window_end);
