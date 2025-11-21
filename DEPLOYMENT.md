# Deployment Guide

This document collects the steps needed to ship the Site-B frontend to production, either directly on a host or inside Docker. The backend API the site consumes can be deployed independently, but you’ll typically run both containers on the same network.

---

## 1. Prerequisites

- Python **3.11** (used by the application).
- PostgreSQL (or another DB supported by SQLAlchemy – update `DATABASE_URL` accordingly).
- Access to the upstream API that provides agenda, speakers, news, etc.
- Optional: Node.js (only required if you rebuild Tailwind assets outside Docker).
- Docker 24+ and Docker Compose v2 if you plan to containerise.

The repo ships with `tailwindcss.exe` for local Windows builds; Docker builds assume `app/static/css/tw.build.css` is already bundled (run the Tailwind CLI before building if you change styles).

---

## 2. Environment configuration

Copy `.env` and edit for each environment:

| Variable | Purpose |
| --- | --- |
| `ENV` | Set to `prod` in production to enable template caching. |
| `APP_NAME` | Display name in page titles. |
| `BACKEND_BASE_URL` | Base URL for the upstream API (e.g. `http://backend:8000`). |
| `MEDIA_BASE_URL`, `MEDIA_PREFIX` | Where uploaded media is hosted. |
| `DATABASE_URL` | SQLAlchemy connection string. |
| `TRANSLATE_*` | Only used by translation helpers; optional. |
| `DEFAULT_LANG`, `SUPPORTED_LANGS` | Language negotiation defaults. |
| `SITE_MAP_RAW` | Comma-separated `host:slug:id` entries so the middleware selects the right theme. |

Never commit secrets; inject them at runtime through env files or your orchestrator.

---

## 3. Install dependencies (bare-metal deployment)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Rebuild Tailwind CSS whenever templates or the `tailwind.config.js` change:

```bash
./tailwindcss.exe `
  -c tailwind.config.js `
  -i app/static/css/tw.css `
  -o app/static/css/tw.build.css `
  --minify
```

On Linux/macOS, install the Tailwind CLI via npm (`npx tailwindcss …`) or download the appropriate binary.

---

## 4. Database and backend checks

1. Ensure the backend has run any required migrations against the target DB.
2. Confirm this frontend can reach the backend API using the configured `BACKEND_BASE_URL`.
3. Validate media URLs (`MEDIA_BASE_URL` + `MEDIA_PREFIX`) return assets.

---

## 5. Smoke tests

```bash
python -m compileall app           # catches syntax errors
python -m uvicorn app.main:app     # quick manual check (press Ctrl+C to stop)
```

Browse through both tenants (main + Site B) to verify hero sections, detailbar, and data-driven pages before deploying.

---

## 6. Production ASGI server (bare metal)

Use Gunicorn with Uvicorn workers:

```bash
export ENV=prod
export BACKEND_BASE_URL=http://backend:8000

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60
```

Wrap this command with your preferred process manager (systemd, supervisor, etc.) and place it behind an HTTPS-capable reverse proxy (nginx, Caddy, Apache).

---

## 7. Docker deployment

### 7.1 Build the image

```
docker build -t tourism-front:latest .
```

The Dockerfile is a slim Python 3 image that installs dependencies and runs Uvicorn with four workers. Ensure `app/static/css/tw.build.css` exists before building (use the provided Tailwind CLI locally if you edit styles).

### 7.2 Compose stack

`docker-compose.yml` defines only the frontend service and expects a backend container named `backend` on the external Docker network `tourism` (created by the backend stack). Bring the stack up with:

```
docker compose up --build
```

Expose the frontend through your reverse proxy (e.g. map `port 80 -> frontend:8000`). Provide the `.env` file (or dedicated `env_file`) with production variables. If you run the frontend standalone, create the shared network once with `docker network create tourism` so both services can reach each other at `http://backend:8000`.

### 7.3 Useful overrides

- Set `FRONT_SITE_ID` / `FRONT_SITE_SLUG` if you want a specific fallback site when no host match is found.
- Override Gunicorn worker count through `GUNICORN_WORKERS` (add env + edit command if required).
- Attach volumes if you need to persist or hot-reload templates in a dev container.

---

## 8. Release checklist

- [ ] `.env` (or secret manager) populated with production values.
- [ ] Tailwind bundle rebuilt (Docker build handles this automatically).
- [ ] Database reachable and migrated by the backend.
- [ ] Backend container/service reachable from the frontend (`BACKEND_BASE_URL`).
- [ ] Reverse proxy forwarding traffic and serving `/static/` with caching headers.
- [ ] Health checks configured (consider adding `/healthz` route for load balancers).
- [ ] Monitoring/alerts wired up for Gunicorn and reverse proxy logs.

Once the above is satisfied you are ready to ship the Site-B frontend alongside its backend counterpart in Docker or on bare metal.
