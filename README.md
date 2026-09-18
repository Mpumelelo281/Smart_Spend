# SmartSpend

AI-driven budgeting and price-comparison web app for NSFAS-funded students
(fixed R1650/month allowance). Built for DUT module SODM01/SFEN301.

Two constraints shape almost every decision in this codebase: mobile data
is expensive for this user base (payload size is never an afterthought),
and the system holds personal financial data under POPIA (anonymity
guarantees are enforced in code, not policy — see Rule 7 below).

## Stack

Django 5 + DRF + Celery/Redis + PostgreSQL 16 on the backend; React 18 +
Vite + Tailwind, built as a PWA, on the frontend. See the top of this repo
history / project brief for the full rationale; nothing here substitutes
the mandated stack.

## Running locally

```bash
cp backend/.env.example backend/.env   # edit if needed
docker compose up --build
```

- Backend: http://localhost:8000 (Django admin at `/admin/`)
- Frontend: http://localhost:5173
- Postgres: localhost:5432, Redis: localhost:6379

### Backend without Docker

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then point DATABASE_URL/REDIS_URL at something reachable
python manage.py migrate
python manage.py runserver
```

Running the auth test suite requires a reachable Postgres **and** Redis
(the auth endpoints are rate-limited via the Redis-backed throttle cache) —
either `docker compose up -d db redis` first, or rely on CI, which starts
both as service containers.

```bash
cd backend
pytest
flake8 .
pylint apps smartspend
```

### Frontend without Docker

```bash
cd frontend
npm install
npm run dev
```

```bash
cd frontend
npm run test        # Vitest + React Testing Library, single run
npm run test:watch  # same, in watch mode
```

### Scheduled (Celery beat) tasks

Two periodic tasks exist but aren't scheduled by default — register them
via the django-celery-beat admin (`/admin/django_celery_beat/periodictask/`)
once a worker is running:

- `catalog.check_price_drops` (e.g. hourly) — alerts students when a
  product in their cart gets cheaper elsewhere.
- `reporting.refresh_reporting_views` (e.g. every 15 minutes) — refreshes
  the materialised views Student Services reports read from (see below).

## Sprint 1 — what's implemented

Authentication and budget creation, per the build order:

- All 11 ERD entities modelled and migrated (`apps/accounts`,
  `apps/budgets`, `apps/catalog`, `apps/recommendations`,
  `apps/notifications`) — see "Sprints 2–3" below for the business logic
  built on top of catalog/recommendations/notifications since.
- Registration gated to a DUT email domain, with email verification.
- Two-step TOTP MFA login (enrolment on first login, challenge on every
  login after) — see `apps/accounts/views.py`.
- Server-side RBAC for Student / Administrator / Student Services Officer
  (`apps/accounts/permissions.py`), checked on every endpoint via
  `permission_classes`, never assumed from the UI.
- Append-only audit log for every auth event (`apps/accounts/models.py::AuditLog`,
  enforced by overriding `save`/`delete`, not just convention).
- Budget creation with the allocation rule — categories can never sum to
  more than the student's allowance — enforced server-side in
  `apps/budgets/serializers.py`, previewed client-side in
  `frontend/src/pages/BudgetSetup.jsx`.
- React budget-setup screen, PWA-installable, service worker caching the
  app shell and the most recent `GET /budgets/` response.

Ten numbered rules from the project brief are referenced by number
(`Rule 1`–`Rule 10`) directly in the code comments closest to where each
is enforced, so the Construction chapter of the report can be written by
reading the code.

### Deliberate deviations, documented where they occur

- `User.password` (Django's built-in hashed-password field) stands in for
  the ERD's `password_hash` — renaming it would mean re-implementing
  `django.contrib.auth` by hand for no behavioural difference. See the
  docstring in `apps/accounts/models.py`.
- `AuditLog` is additional infrastructure, not one of the 11 ERD entities —
  Rule 8 requires it and it has to live somewhere.

## Sprints 2–3 — what's since been added

- Retailer adapters + circuit breakers + 15-minute Redis price cache +
  search API (`apps/catalog`) — SerpApi Google Shopping is fully live;
  Checkers/Shoprite/Mr Price (`apps/catalog/adapters/`) are wired into the
  same adapter interface but stay inert until a verified search endpoint
  is configured (`CHECKERS_API_BASE_URL` etc. — see each module's
  docstring and `.env.example`).
- A rule-based cold-start recommender (`apps/recommendations`) — ranks
  cheapest-in-category listings when there's no training data yet; the
  scikit-learn hybrid model that replaces/augments it is still future
  work (`Recommendation.was_accepted` is already captured as its training
  signal).
- Threshold notifications dispatch via a Celery task
  (`apps/budgets/tasks.py`) instead of inline in the request/response
  cycle, plus Web Push delivery (`apps/notifications/push.py` — needs a
  VAPID keypair, see `.env.example`) and a price-drop check
  (`apps/catalog/tasks.py`).
- Student Services k-anonymity reporting (`apps/reporting`, backed by
  `infra/sql/002_reporting_views.sql`) — apply that SQL file against the
  database once (it's not a Django migration, by design — see
  `smartspend/db_router.py`) before the report endpoints return data.
- Recurring budgets (clone last month's categories), an Excel (.xlsx)
  export of budget history, and a pace-based spend forecast — all in
  `apps/budgets/views.py`, surfaced on the Dashboard and History pages.
  The export is a real spreadsheet (bold header, banded Excel Table,
  currency-formatted columns via `openpyxl`), not CSV — CSV can't carry
  any formatting at all, so "Export Excel" on the History page downloads
  `smartspend-budget-history.xlsx` directly. Each row is one category's
  own Allocated/Spent for that month, plus two Month Total columns
  repeated across every row for that month, so "was that the whole
  month's spend or just this category?" is answerable from the row
  itself rather than ambiguous.
- `TransactionSerializer.create()` falls back to running the threshold
  check inline if enqueuing it onto Celery fails (e.g. no broker
  reachable — the normal state of a non-Docker local dev setup with no
  Redis/worker running). Without this, the 80%/exceeded alert silently
  never fires at all in that setup, not just late — see the comment
  there and `apps/budgets/tasks.py`.
