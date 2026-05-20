CREATE TABLE IF NOT EXISTS score_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_key TEXT NOT NULL UNIQUE,
    formula_text TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS weirdness_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score_date DATE NOT NULL,
    score_value INTEGER NOT NULL CHECK (score_value >= 0 AND score_value <= 100),
    score_version TEXT NOT NULL,
    top_event_ids UUID[] NOT NULL DEFAULT '{}',
    component_scores JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (score_date, score_version)
);

CREATE INDEX IF NOT EXISTS idx_score_versions_version_key
    ON score_versions(version_key);

CREATE INDEX IF NOT EXISTS idx_weirdness_scores_score_date
    ON weirdness_scores(score_date);

CREATE INDEX IF NOT EXISTS idx_weirdness_scores_score_version
    ON weirdness_scores(score_version);
