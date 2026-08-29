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

## Sprint 1 — what's implemented

Authentication and budget creation, per the build order:

- All 11 ERD entities modelled and migrated (`apps/accounts`,
  `apps/budgets`, `apps/catalog`, `apps/recommendations`,
  `apps/notifications`) — catalog/recommendations/notifications are
  model-only until Sprints 2–3 add the business logic that uses them.
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

## Not yet built (Sprints 2–3)

Retailer adapters + circuit breakers + 15-minute Redis price cache +
search API (Sprint 2); the scikit-learn hybrid recommender, cold-start
fallback, threshold-notification Celery task, spending dashboard, and
Student Services k-anonymity reporting (Sprint 3).
