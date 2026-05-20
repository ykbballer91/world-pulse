CREATE TABLE IF NOT EXISTS display_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_date DATE NOT NULL UNIQUE,
    page_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_display_log_display_date
    ON display_log(display_date);
