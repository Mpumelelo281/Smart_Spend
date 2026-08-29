"""
Routes reporting-only reads to the restricted `reporting` database role.

Rule 7 (k-anonymity): Student Services aggregate reports must be served
through a database connection that literally cannot see row-level student
data — that guarantee has to live at the DB grant level, not just in
application code, or a bug in a view could bypass suppression entirely.
Models registered under the `reporting` app label are only ever read
through the `reporting` connection, which PostgreSQL restricts (via GRANT)
to the anonymised materialised views defined in infra/sql/002_reporting_views.sql
(added in Sprint 3, alongside infra/sql/001_init_roles.sql which creates the role).
"""


class ReportingRouter:
    reporting_app_labels = {"reporting"}

    def _is_reporting_model(self, model):
        app_label = getattr(getattr(model, "_meta", None), "app_label", None)
        return app_label in self.reporting_app_labels

    def db_for_read(self, model, **hints):
        if self._is_reporting_model(model):
            return "reporting"
        return None

    def db_for_write(self, model, **hints):
        if self._is_reporting_model(model):
            raise RuntimeError("The reporting database role is read-only.")
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.reporting_app_labels:
            # Materialised views are created by raw SQL (infra/sql), never
            # by Django migrations, on the reporting connection.
            return False
        return db == "default"
