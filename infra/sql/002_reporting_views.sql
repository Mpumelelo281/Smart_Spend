-- Sprint 3: the anonymised materialised views the smartspend_reporting
-- role (see 001_init_roles.sql) is granted SELECT on. Rule 7 (k-anonymity):
-- any campus/month/category slice with fewer than K_ANONYMITY_THRESHOLD
-- distinct students is suppressed entirely by the HAVING clause below —
-- never returned with the count blanked out, since a "count is too small
-- to show" row is itself a re-identification signal. Keep the threshold
-- literal below in sync with settings.K_ANONYMITY_THRESHOLD (default 10)
-- — a materialised view can't read a Django setting at refresh time, so
-- this is the one place that value has to be duplicated.
--
-- Not created via a Django migration (see smartspend/db_router.py) —
-- apply manually against an existing database, or let
-- docker-entrypoint-initdb.d run it (mounted the same way as
-- 001_init_roles.sql) on a fresh one. Refreshed periodically by
-- apps.reporting.tasks.refresh_reporting_views — schedule that task via
-- the django-celery-beat admin (e.g. every 15 minutes); nothing refreshes
-- these automatically on write.

CREATE MATERIALIZED VIEW IF NOT EXISTS reporting_category_spend_summary AS
SELECT
    row_number() OVER (ORDER BY sp.campus, b.year, b.month, bc.name) AS id,
    sp.campus AS campus,
    b.year AS year,
    b.month AS month,
    bc.name AS category_name,
    COUNT(DISTINCT sp.profile_id) AS student_count,
    SUM(t.amount) AS total_spent,
    AVG(t.amount) AS avg_transaction_amount,
    SUM(bc.allocated_amount) AS total_allocated
FROM transaction t
JOIN budget_category bc ON bc.category_id = t.category_id
JOIN budget b ON b.budget_id = bc.budget_id
JOIN student_profile sp ON sp.profile_id = b.profile_id
GROUP BY sp.campus, b.year, b.month, bc.name
HAVING COUNT(DISTINCT sp.profile_id) >= 10;

CREATE UNIQUE INDEX IF NOT EXISTS reporting_category_spend_summary_pk
    ON reporting_category_spend_summary (id);
CREATE UNIQUE INDEX IF NOT EXISTS reporting_category_spend_summary_natural_key
    ON reporting_category_spend_summary (campus, year, month, category_name);

CREATE MATERIALIZED VIEW IF NOT EXISTS reporting_budget_utilization_summary AS
SELECT
    row_number() OVER (ORDER BY sp.campus, b.year, b.month) AS id,
    sp.campus AS campus,
    b.year AS year,
    b.month AS month,
    COUNT(DISTINCT sp.profile_id) AS student_count,
    SUM(b.total_allocated) AS total_allocated,
    SUM(COALESCE(spend.total_spent, 0)) AS total_spent
FROM budget b
JOIN student_profile sp ON sp.profile_id = b.profile_id
LEFT JOIN (
    SELECT bc.budget_id AS budget_id, SUM(t.amount) AS total_spent
    FROM transaction t
    JOIN budget_category bc ON bc.category_id = t.category_id
    GROUP BY bc.budget_id
) spend ON spend.budget_id = b.budget_id
GROUP BY sp.campus, b.year, b.month
HAVING COUNT(DISTINCT sp.profile_id) >= 10;

CREATE UNIQUE INDEX IF NOT EXISTS reporting_budget_utilization_summary_pk
    ON reporting_budget_utilization_summary (id);
CREATE UNIQUE INDEX IF NOT EXISTS reporting_budget_utilization_summary_natural_key
    ON reporting_budget_utilization_summary (campus, year, month);

GRANT SELECT ON reporting_category_spend_summary TO smartspend_reporting;
GRANT SELECT ON reporting_budget_utilization_summary TO smartspend_reporting;
