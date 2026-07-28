-- Manual migration. No migration tool exists in this project (see
-- ../../docs/backend/database/migration-guide.md) -- docker/postgres/init.sql
-- only runs on a brand-new Postgres data directory, so an already-running
-- database needs this applied by hand:
--
--   psql "$DATABASE_URL" -f docker/postgres/migrations/0001_oauth_cleanup_and_report_review.sql
--
-- Corresponding init.sql DDL was also updated so a fresh install matches.
--
-- IRREVERSIBLE: dropping users.gh_id below destroys the only link back to a
-- GitHub-provisioned account. Those users were created with password_hash=''
-- (services/oauth_service.py), so unless their email also matches a Google
-- account they lose their only way to log in. Run this pre-check by hand
-- first -- it is deliberately NOT part of the transaction below:
--
--   -- Before applying: check how many users would lose their only login method.
--   -- SELECT count(*) FROM users WHERE gh_id IS NOT NULL AND gg_id IS NULL;
--   -- Back up the `users` table (e.g. `pg_dump -t users`) before proceeding if that count is non-zero.

BEGIN;

-- users.gg_re_token: dead column. Confirmed by grep -- the Google OAuth flow
-- (services/oauth_service.py) only ever reads/writes users.gg_id; nothing in
-- the codebase reads or writes gg_re_token.
ALTER TABLE users DROP COLUMN IF EXISTS gg_re_token;

-- users.gh_id: GitHub OAuth's lookup/link key. GitHub is no longer a
-- supported login provider (OAuthProviderType now only has GOOGLE) --
-- services/oauth_service.py::upsert_oauth_user's GitHub branches were
-- removed in the same change that drops this column.
ALTER TABLE users DROP COLUMN IF EXISTS gh_id;

-- url_report: human-over-AI review attribution, additive and nullable --
-- existing rows are unaffected (reviewed_by/reviewed_at stay NULL until an
-- admin next changes a report's status).
ALTER TABLE url_report ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE url_report ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ NULL;

COMMIT;
