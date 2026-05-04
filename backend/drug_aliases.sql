-- Reference Drug Alias Seed File
-- Purpose:
--   Provides canonical drug alias mappings used by SNS EMR
--   for medication normalization and compliance reporting.
--
-- Usage:
--   This file may be applied manually in non-production
--   environments or referenced for data verification.
--
-- NOTE:
--   This file does NOT modify schema.
--   Schema changes are handled via Alembic migrations only.
-- Load aliases into drug_aliases
-- alias_text = what nurse may type (brand or generic)
-- canonical_text = ingredient-level name you will compare on

BEGIN;

-- Optional: clear existing mappings if you are rebuilding
-- TRUNCATE drug_aliases;

-- Insert mappings (use ON CONFLICT to avoid duplicates)
-- IMPORTANT: alias_text must be lowercase/trimmed before insert

-- Example rows:
-- INSERT INTO drug_aliases(alias_text, canonical_text) VALUES
-- ('glucophage', 'metformin'),
-- ('metformin', 'metformin')
-- ON CONFLICT (alias_text) DO UPDATE SET canonical_text = EXCLUDED.canonical_text;

COMMIT;