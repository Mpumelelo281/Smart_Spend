-- Runs once, automatically, on first `db` container start (see
-- docker-compose.yml, which mounts this directory at
-- /docker-entrypoint-initdb.d). Creates the second, restricted database
-- role Rule 7 depends on: Student Services reports must be served through
-- a connection that cannot see row-level student data at all, not one that
-- is merely told not to look.
--
-- The role has no privileges yet — Sprint 3 grants it SELECT on the
-- anonymised materialised views once those exist (infra/sql/002_reporting_views.sql).
-- It is intentionally created with zero default table access.

DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'smartspend_reporting') THEN
        CREATE ROLE smartspend_reporting WITH LOGIN PASSWORD 'smartspend_reporting';
    END IF;
END
$$;

REVOKE ALL ON SCHEMA public FROM smartspend_reporting;
GRANT CONNECT ON DATABASE smartspend TO smartspend_reporting;
GRANT USAGE ON SCHEMA public TO smartspend_reporting;
