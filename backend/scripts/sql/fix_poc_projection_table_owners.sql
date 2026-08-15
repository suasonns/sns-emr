-- =========================================================
-- FILE: scripts/sql/fix_poc_projection_table_owners.sql
-- PURPOSE: Align ownership of POC projection tables to sns
-- RUN AS: postgres (or another sufficiently privileged owner/superuser)
-- =========================================================

ALTER TABLE public.poc_problems OWNER TO sns;
ALTER TABLE public.poc_goals OWNER TO sns;
ALTER TABLE public.poc_interventions OWNER TO sns;