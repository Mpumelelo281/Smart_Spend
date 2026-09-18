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

## Deploying to Render

`render.yaml` at the repo root is a Render Blueprint that defines the whole
stack — Django API, Celery worker, React static site, Postgres and Redis.
On Render's **Hobby** workspace plan (no monthly fee; you only pay for
usage), the cost breaks down as:

| Service | Instance type | Cost |
|---|---|---|
| `smartspend-api` (Django) | Free — spins down after 15 min idle, ~30–60s cold start | $0 |
| `smartspend-frontend` (React) | Static site | $0 |
| `smartspend-redis` (Key Value) | Free — in-memory only, wiped on restart (fine: it's only the Celery broker and a price-query cache) | $0 |
| `smartspend-db` (Postgres) | Free — **expires 30 days after creation** (see below) | $0 |
| `smartspend-worker` (Celery worker + beat) | Starter — Background Workers have no free tier | ~$7/mo |

Worker and beat run together in one service (`celery ... worker -B`) so
this is one paid instance, not two.

**The free Postgres expires after 30 days.** That's a Render limit, not
something this repo controls. Before it does, either upgrade the database
to a paid plan in the Render dashboard, or move to an external free
Postgres (e.g. Neon) and update `DATABASE_URL`/`REPORTING_DATABASE_URL` on
both `smartspend-api` and `smartspend-worker`.

### One-time setup

1. Push this repo to GitHub (Render deploys from a connected repo).
2. In the Render dashboard: **New → Blueprint**, pick this repo. Render
   reads `render.yaml` and prompts for each secret marked `sync: false`.
3. When prompted, fill in:
   - `DJANGO_SECRET_KEY` — generate one with
     `python -c "import secrets; print(secrets.token_urlsafe(50))"` and
     paste the **same value** into both `smartspend-api` and
     `smartspend-worker`.
   - `SERPAPI_KEY` — optional; blank still works (search just uses
     seeded data).
   - `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `DEFAULT_FROM_EMAIL` —
     required for verification and password-reset emails; without SMTP
     configured, nobody can complete registration. See the Gmail
     app-password note in `backend/.env.example`.
   - `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` — optional; only needed for
     Web Push. Generate with `vapid --gen`.
4. After the first deploy finishes, **check the real URLs** Render
   assigned (Dashboard → each service). If a service name was already
   taken globally, Render appends a random suffix — in which case update
   `CORS_ALLOWED_ORIGINS` and `FRONTEND_BASE_URL` on `smartspend-api`, and
   `VITE_API_BASE_URL` on `smartspend-frontend`, to the real URLs, then
   redeploy both.
5. Add the single-page-app rewrite by hand: Dashboard →
   `smartspend-frontend` → **Redirects/Rewrites** → add a rule with
   Source `/*`, Destination `/index.html`, Action **Rewrite**. Without it,
   refreshing any page other than `/` — and, critically, the link in the
   verification email (`/verify-email?token=...`) — returns a 404. (This
   isn't in `render.yaml` on purpose; see the comment there.)
6. Apply the reporting SQL once, from the Render Postgres service's
   **Connect** tab (it gives you a ready `psql` command):
   ```
   \i infra/sql/001_init_roles.sql
   \i infra/sql/002_reporting_views.sql
   ```
   Until then `REPORTING_DATABASE_URL` reuses the main connection (see the
   comment in `render.yaml`), and Student Services reports won't return
   data — nothing else is affected.
7. Register a Celery beat schedule for `catalog.check_price_drops` and
   `reporting.refresh_reporting_views` via the Django admin (see
   "Scheduled tasks" above).

Render has no South Africa region (its regions are Oregon, Ohio,
Virginia, Frankfurt and Singapore). `render.yaml` pins everything to
Frankfurt, the closest to South Africa — and all services must share one
region anyway, since Render's private network (which Redis is restricted
to) doesn't span regions. That's fine for a demo, but worth flagging if
this ever handles real students' data: POPIA cross-border transfer rules
would apply.

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
