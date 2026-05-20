ALTER TABLE display_log
ADD COLUMN IF NOT EXISTS quiet_signal jsonb NOT NULL DEFAULT '{}'::jsonb;
