# Bhopal CivicAI — Backend

FastAPI backend for an AI-assisted civic grievance platform for Bhopal.
Citizens file geotagged complaints; Claude classifies, prioritises, routes and
de-duplicates them; municipal admins work the queue from a dashboard backed by
smart-city analytics.

**Stack:** FastAPI · PostgreSQL (Supabase) · Supabase Auth · SQLAlchemy 2.0 ·
Pydantic v2 · Claude API (`claude-opus-5`)

---

## Quick start

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then fill in the values (see below)
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for Swagger UI.

Minimum viable `.env` for local development — a SQLite file stands in for
Supabase Postgres so the API boots with no cloud credentials:

```env
DATABASE_URL=sqlite:///./bhopal_civicai_dev.db
SUPABASE_JWT_SECRET=any-long-random-string-for-local-dev
ADMIN_EMAILS=admin@bhopalcivicai.in
ANTHROPIC_API_KEY=sk-ant-...        # optional; omit to use the fallback analyser
```

---

## Configuration

Everything is environment-driven; see `.env.example` for the annotated list.
The settings that matter most:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Supabase pooler URL, e.g. `postgresql+psycopg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres` |
| `SUPABASE_JWT_SECRET` | Shared-secret (HS256) JWT verification |
| `SUPABASE_URL` | Asymmetric (ES256/RS256) verification via JWKS — use instead of the secret |
| `ANTHROPIC_API_KEY` | Claude API key. **Backend only — never ship to the client.** |
| `ADMIN_EMAILS` | Comma-separated allow-list that grants the admin role |
| `CORS_ORIGINS` | Comma-separated React origins |
| `AUTO_CREATE_TABLES` | `true` for dev; use `migrations/001_init.sql` in production |

### Two auth modes

* **Shared secret** — set `SUPABASE_JWT_SECRET` (Dashboard → Settings → API →
  JWT Secret). Simple, works everywhere.
* **Asymmetric signing keys (recommended)** — leave the secret blank and set
  `SUPABASE_URL`. Keys are fetched and cached from
  `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`.

---

## Database

For production, run the migration once in the Supabase SQL editor and turn off
runtime DDL:

```bash
psql "$DATABASE_URL" -f migrations/001_init.sql
# then set AUTO_CREATE_TABLES=false
```

The migration creates all five tables with indexes and CHECK constraints, seeds
the seven departments, adds `updated_at` triggers, and enables **row level
security**. The backend connects with the service role and so bypasses RLS —
API authorisation lives in `app/auth/dependencies.py`. The policies exist to
protect the data if the React client ever queries Supabase directly with the
anon key.

Tables: `profiles`, `complaints`, `complaint_confirmations`, `departments`,
`complaint_updates`.

---

## Roles

| Role | How it is obtained |
|---|---|
| `citizen` | Every Supabase signup. Always. |
| `admin` | `ADMIN_EMAILS` allow-list, an existing admin via `POST /api/v1/admin/users/{id}/role`, or `scripts/create_admin.py` |

**Signup can never produce an admin.** The client never supplies a role: the
request schemas reject a `role` field outright (`extra="forbid"`), and role
resolution reads only backend configuration. Every `/admin/*` route sits behind
the `require_admin` dependency, which checks the role stored in *our* database
rather than any claim inside the token.

```bash
python scripts/create_admin.py --email official@bhopal.gov.in            # promote
python scripts/create_admin.py --email official@bhopal.gov.in --pre-seed # before signup
python scripts/create_admin.py --list
```

---

## Testing with Swagger

1. Start the server: `uvicorn app.main:app --reload --port 8000`
2. Mint a local token (dev only — needs `SUPABASE_JWT_SECRET`):

   ```bash
   python scripts/dev_token.py --email citizen@example.com      # citizen
   python scripts/dev_token.py --email admin@bhopalcivicai.in   # admin (in ADMIN_EMAILS)
   ```

   In production, use a real Supabase access token instead — the React client
   gets one from `supabase.auth.getSession()`.
3. Open http://localhost:8000/docs, click **Authorize**, paste the token.
   Authorization persists across reloads.
4. Suggested walkthrough:
   `POST /auth/sync` → `GET /auth/me` → `POST /complaints` →
   `GET /complaints/{id}/status` → (admin token) `GET /admin/dashboard` →
   `PATCH /admin/complaints/{id}` → `GET /ai/admin-briefing`

Automated equivalent — drives every endpoint over real HTTP and asserts each
status code:

```bash
uvicorn app.main:app --port 8000          # terminal 1
python scripts/smoke_test.py --base-url http://localhost:8000   # terminal 2
```

Unit and API test suite (no server needed):

```bash
pytest              # 97 tests
pytest --cov=app
```

---

## API

Base path `/api/v1`. Every route except `/health`, `/ready` and the docs
requires `Authorization: Bearer <supabase-jwt>`.

### Authentication
| Method | Path | Notes |
|---|---|---|
| `POST` | `/auth/sync` | Mirror the Supabase user into `profiles` (idempotent) |
| `GET` | `/auth/me` | Profile + activity stats + permission list |
| `GET` | `/auth/verify` | Token introspection for route guards |

### Profile
| Method | Path | Notes |
|---|---|---|
| `GET` | `/profile` | Read own profile |
| `POST` / `PATCH` | `/profile` | Upsert / partial update |
| `GET` | `/profile/stats` | Complaint counts for this citizen |

### Complaints (citizen)
| Method | Path | Notes |
|---|---|---|
| `POST` | `/complaints` | File a complaint → triggers AI analysis |
| `GET` | `/complaints` | Own complaints; filter, search, sort, paginate |
| `GET` | `/complaints/nearby` | Open issues near a point, to confirm instead of duplicating |
| `GET` | `/complaints/{id}` | Full detail + AI verdict + timeline |
| `PATCH` | `/complaints/{id}` | Edit own complaint while still `submitted` |
| `GET` | `/complaints/{id}/status` | Status tracking with the SLA clock |
| `POST` | `/complaints/{id}/confirm` | "Me too" on an existing issue |
| `GET` | `/complaints/reference/{code}` | Look up by tracking code |

### Admin
| Method | Path | Notes |
|---|---|---|
| `GET` | `/admin/dashboard` | All dashboard statistics in one call |
| `GET` | `/admin/complaints` | Full queue: filter by status/category/severity/department/ward, free-text search, sort |
| `GET` | `/admin/complaints/{id}` | Detail including internal notes |
| `PATCH` | `/admin/complaints/{id}` | Status, department, priority, severity, category, assignee, resolution notes, evidence |
| `POST` | `/admin/complaints/{id}/evidence` | Before/after photos |
| `POST` | `/admin/complaints/{id}/reanalyze` | Re-run Claude on a complaint |
| `GET`/`POST` | `/admin/departments` | List / create |
| `PATCH` | `/admin/departments/{id}` | Update |
| `GET` | `/admin/users` | List users |
| `POST` | `/admin/users/{id}/role` | Grant/revoke admin |
| `POST` | `/admin/users/{id}/active` | Enable/disable an account |

### Analytics
| Method | Path | Access |
|---|---|---|
| `GET` | `/analytics/hotspots` | Any signed-in user |
| `GET` | `/analytics/trends` | Any signed-in user |
| `GET` | `/analytics/categories` | Any signed-in user |
| `GET` | `/analytics/city-health` | Any signed-in user |
| `GET` | `/analytics/departments` | **Admin only** (evaluates staff) |

### AI
| Method | Path | Access |
|---|---|---|
| `POST` | `/ai/analyze-complaint` | Any signed-in user — preview, nothing stored |
| `GET` | `/ai/admin-briefing` | **Admin only** |

---

## How the AI pipeline works

On `POST /complaints`:

1. The location is validated against the city service radius.
2. Nearby open complaints are found with an indexed bounding-box query plus an
   exact haversine pass (no PostGIS needed), and passed to Claude as duplicate
   candidates.
3. Claude returns a **structured output** validated against
   `ComplaintAnalysis`: category, severity, priority score, summary,
   responsible department, suggested action, tags, duplicate/similar
   references, confidence.
4. Output is sanitised — a `reference_code` that wasn't in the candidate list is
   discarded, and an unknown department code falls back to the category's owner.
   The model can never invent an identifier that reaches the database.
5. The verdict is written to the complaint, the department is assigned, and a
   timeline entry is recorded. A detected duplicate is linked, the complaint is
   marked `duplicate`, and the original gains a confirmation.

**Degradation is by design.** If the API key is missing, the request fails, or a
safety classifier declines it, a deterministic keyword analyser (including
common Hindi terms — *kachra*, *naali*, *paani*, *sadak*) produces a usable
result and the complaint is flagged `ai_analysis_status = "fallback"`. Filing a
civic complaint never fails because an upstream dependency is down.

Model configuration: `claude-opus-5` with adaptive thinking, effort from
`CLAUDE_EFFORT`, and prompt caching on the stable system prefix.

### Community signal
Confirmations raise a complaint's priority score, and past a threshold escalate
its severity — so a widely-felt problem rises in the queue without anyone
filing duplicates. Each citizen may confirm once, and only from near the
reported location.

### City health score
A 0–100 composite from resolution rate (30%), speed (20%), backlog (20%), open
critical issues (15%) and citizen engagement (15%), compared against the
previous equal-length window to derive the trend.

---

## Project layout

```
backend/
├── app/
│   ├── main.py               # app factory, middleware, lifespan, health probes
│   ├── api/
│   │   ├── deps.py           # pagination and shared query params
│   │   └── v1/               # auth, profile, complaints, admin, analytics, ai
│   ├── auth/                 # Supabase JWT verification + role dependencies
│   ├── database/             # engine, session, declarative base, bootstrap
│   ├── models/               # SQLAlchemy ORM models and enums
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # business logic (claude, complaint, admin, analytics, profile)
│   └── utils/                # config, errors, logging, geo maths
├── migrations/001_init.sql   # Supabase schema + RLS
├── scripts/                  # create_admin, dev_token, smoke_test
├── tests/                    # pytest suite
├── Dockerfile
└── .env.example
```

Routers stay thin: validation lives in `schemas/`, rules in `services/`.

---

## Production notes

* **Secrets** — `ANTHROPIC_API_KEY`, `SUPABASE_JWT_SECRET` and
  `SUPABASE_SERVICE_ROLE_KEY` belong in the backend environment only. Only
  `SUPABASE_URL` and the anon key are safe in the React bundle.
* **Errors** — every failure returns the same envelope, so the frontend can
  branch on a stable code:
  ```json
  { "error": { "code": "outside_service_area", "message": "…", "details": null } }
  ```
* **Observability** — each response carries `X-Request-ID` and
  `X-Response-Time-ms`, and every request is logged with its outcome.
* **Rate limiting** — the built-in limiter is per-process and per-IP; it blunts
  accidental floods but cannot coordinate across workers. Put a gateway or
  Redis-backed limiter in front for real traffic.
* **Probes** — `/health` is liveness (no I/O); `/ready` checks the database and
  reports whether auth and AI are configured.
* **Deploy** — `docker build -t bhopal-civicai-api . && docker run -p 8000:8000 --env-file .env bhopal-civicai-api`

### Frontend wiring (React)

```ts
const { data } = await supabase.auth.getSession();
const res = await fetch(`${API_URL}/api/v1/complaints`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${data.session?.access_token}`,
  },
  body: JSON.stringify({ title, description, latitude, longitude, image_url }),
});
```

Upload photos to Supabase Storage from the client, then send the resulting
public URL — the API stores URLs, not binary data.
