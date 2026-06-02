# Hospital Doctor Duty Roster Management System

Enterprise-style full-stack roster software for Bangladesh hospitals and clinics. The system includes JWT authentication, role based access control, doctor management, leave approval, smart monthly roster generation, conflict detection, workload analytics, exports, audit logging, and Docker deployment.

## Stack

- Frontend: React, Vite, TypeScript, TailwindCSS, Zustand, Axios, shadcn-style UI, Recharts, FullCalendar
- Backend: Python FastAPI, SQLAlchemy, PostgreSQL, JWT, bcrypt
- Deployment: Docker Compose with PostgreSQL, FastAPI, and Nginx-served frontend

## Project Structure

```text
backend/
  app/
    api/routes/        REST endpoints
    core/              settings and security
    db/                SQLAlchemy session and bootstrap
    models/            normalized ORM models
    schemas/           Pydantic API contracts
    services/          scheduling, analytics, notifications, exports
  scripts/seed.py      sample Bangladesh hospital data and roster
  tests/               scheduler tests
frontend/
  src/
    api/               Axios client and API functions
    components/        layout and shadcn-style UI
    features/          dashboard, doctors, leaves, roster, analytics
    store/             Zustand auth store
docs/
  API.md
  ARCHITECTURE.md
  POSTGRES_SCHEMA.sql
```

## Quick Start With Docker

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Seed sample data:

```bash
docker compose exec backend python scripts/seed.py
```

4. Open:

- Frontend: http://localhost:8080
- Backend docs: http://localhost:8000/api/docs

## Deployment Split

- Frontend: Vercel
- Backend API: Render
- Database: Neon PostgreSQL

For Vercel, set the project root to `frontend/` and add this environment variable:

```bash
VITE_API_BASE_URL=https://your-render-backend.onrender.com/api
```

Use the production example file in `frontend/.env.production.example` as the template.
Use `FIRST_SUPER_ADMIN_EMAIL`, `FIRST_SUPER_ADMIN_PASSWORD`, `DEFAULT_ADMIN_EMAIL`, and `DEFAULT_ADMIN_PASSWORD` in `.env` to change the default logins.
Set `ALLOW_PUBLIC_REGISTRATION=true` if staff/doctors should be able to create roster-view accounts.
For Render, add `BACKEND_CORS_ORIGIN_REGEX=https://.*\.vercel\.app` so the Vercel frontend can talk to the API without CORS errors.

Render backend setup:

- Existing Docker web service:
  - Branch: `main`
  - Root Directory: `backend`
  - Dockerfile Path: `Dockerfile`
  - Docker Build Context Directory: `.`
  - Docker Command: leave blank
  - Pre-Deploy Command: leave blank
- If you see `lstat /opt/render/project/src/backend/backend`, Render is pointing at the backend folder twice. With `Root Directory` already set to `backend`, do not put `backend/` again in the Dockerfile path or build context.
- Alternative Docker setup: leave `Root Directory` blank, set Dockerfile Path to `backend/Dockerfile`, and set Docker Build Context Directory to `backend`.

Seeded logins:

- Super admin: `goodmorning1293@gmail.com` / `Mahi1234@`
- Admin: `momenulislam900@gmail.com` / `12345678`
- Sample doctors: use any seeded doctor email / `Doctor@123`

Public account access:

- Staff can create an account from the login page and view/export/print the roster only.
- Doctors can self-register only when their email already exists in Doctor Management and no portal account has been created for that doctor yet.
- Super admin/admin accounts can manage doctors, leaves, roster generation, manual overrides, analytics, and conflict review.

If the Vercel login page shows a network error, the frontend is usually missing the Render API URL or the backend CORS settings are not deployed yet. Set `VITE_API_BASE_URL` in Vercel, make sure Render has `BACKEND_CORS_ORIGIN_REGEX=https://.*\.vercel\.app`, and redeploy both services.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Use PostgreSQL locally or run only the database:

```bash
docker compose up postgres
```

The backend accepts Neon-style `postgresql://...` URLs and converts them to the installed Psycopg v3 SQLAlchemy driver automatically.

## Roster Engine

The scheduler is implemented in `backend/app/services/roster_scheduler.py`. It uses constraint filtering plus weighted fairness priority scoring.

Hard constraints:

- No double duty on the same day
- Approved leave dates are blocked
- Weekly off day is blocked
- Consecutive night shifts are blocked
- Doctor monthly duty maximum is enforced
- Existing manual overrides can be preserved

Fairness inputs:

- Least loaded doctors are prioritized
- Duty type repetition is penalized
- Night load is penalized
- Preferred shift gets a lower score
- Weighted workload keeps emergency/night shifts balanced

## Useful Commands

```bash
# syntax check backend
python -m compileall backend/app backend/scripts

# run backend tests after installing requirements
cd backend
pytest

# build frontend
cd frontend
npm run build
```

## API Documentation

FastAPI generates interactive OpenAPI docs at `/api/docs`. A curated endpoint map is also available in `docs/API.md`.
