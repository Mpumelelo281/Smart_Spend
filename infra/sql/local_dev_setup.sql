-- Run this ONCE against your local (non-Docker) PostgreSQL install, as a
-- superuser, e.g.:
--   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -f infra/sql/local_dev_setup.sql
--
-- In docker-compose, the `db` service's POSTGRES_USER/PASSWORD/DB env vars
-- do this step automatically. This script exists only for developers
-- running the backend directly against their own machine's Postgres.

DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'smartspend') THEN
        CREATE ROLE smartspend WITH LOGIN PASSWORD 'smartspend' CREATEDB;
    END IF;
END
$$;

SELECT 'CREATE DATABASE smartspend OWNER smartspend'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smartspend')
\gexec

\c smartspend

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
