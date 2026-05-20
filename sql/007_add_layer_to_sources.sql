BEGIN;

ALTER TABLE sources
ADD COLUMN IF NOT EXISTS layer text;

ALTER TABLE sources
DROP CONSTRAINT IF EXISTS sources_layer_check;

ALTER TABLE sources
ADD CONSTRAINT sources_layer_check
CHECK (
  layer IS NULL
  OR layer IN ('reality', 'attention', 'context')
);

UPDATE sources
SET layer = 'reality'
WHERE name IN (
  'USGS Earthquake Hazards Program',
  'NOAA SWPC',
  'Cloudflare Radar'
);

UPDATE sources
SET layer = 'attention'
WHERE name = 'Wikipedia Pageviews';

UPDATE sources
SET layer = 'context'
WHERE name = 'Open Notify';

COMMIT;
