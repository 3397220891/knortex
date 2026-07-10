# Knortex

Document intelligence knowledge graph platform: upload PDF / Word / TXT documents, and the backend asynchronously parses the text, extracts entities and relationships, and writes them to PostgreSQL (provenance/source of truth) and Neo4j (graph traversal). The frontend provides upload, search, and graph visualization.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Vite, Ant Design 5, ECharts |
| API | FastAPI, Pydantic v2 |
| Async tasks | Celery 5 + Redis (broker / result backend) |
| Document parsing | PyMuPDF (PDF), python-docx (Word) |
| Entity/relation extraction | spaCy `en_core_web_sm` (NER) + regex sentence-pattern templates (relations) |
| Storage | PostgreSQL 16 (source of truth, SQLAlchemy ORM) + Neo4j 5 (graph projection) |
| Testing / CI | pytest + httpx, GitHub Actions |
| Infrastructure | Docker Compose (neo4j / postgres / redis) |

## Architecture

```
React SPA (Vite :3000)
      │  axios, multipart/form-data
      ▼
FastAPI (:8000) ── /upload returns 202 + task_id immediately
      │  celery.delay()
      ▼
Redis (broker) ──► Celery Worker: process_document_task
                        │
                        ├─ DocumentParser   (PyMuPDF / python-docx)
                        ├─ InformationExtractor (spaCy NER + regex relation templates)
                        │
                        ▼
        PostgreSQL (source of truth, assigns entity/relation UUIDs)
                        │  reuses the same UUIDs once written
                        ▼
                     Neo4j (graph projection, backs /search and /graph)
```

The frontend polls `GET /tasks/{task_id}` for the background processing result (see `frontend/src/components/FileUpload.tsx`).

## Getting Started

### Prerequisites

- Docker (runs Neo4j / PostgreSQL / Redis)
- Python 3.12
- Node.js 20

### 1. Start infrastructure

```bash
docker-compose up -d
```

This starts three containers: `kg-neo4j` (7474/7687), `kg-postgres` (5432), `kg-redis` (6379). Credentials are listed in the environment variables table below and default to matching `backend/.env.example`.

### 2. Backend

Run all of the following from the `backend/` directory. The code uses relative imports (`from api.endpoints... import`, not `backend.api...`), so the working directory must be `backend/` — it won't work from the repo root.

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows PowerShell / cmd
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
copy .env.example .env         # Windows; use `cp .env.example .env` on macOS/Linux
```

Start the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**In a second terminal**, start the Celery worker (same `backend/` directory, same virtualenv):

```bash
celery -A tasks worker --loglevel=info --pool=solo
```

> Neither `-A tasks` nor `--pool=solo` is optional here — see "Common Configuration Pitfalls" below.

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000.

## Environment Variables (`backend/.env`, copied from `.env.example`)

| Variable | Default | Notes |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Must match the port docker-compose exposes |
| `NEO4J_USER` / `NEO4J_PASSWORD` | `neo4j` / `password` | Must match docker-compose's `NEO4J_AUTH=neo4j/password`; keep both sides in sync |
| `POSTGRES_URL` | `postgresql+psycopg2://knortex:knortex@localhost:5432/knortex` | User/password/db name must match docker-compose's `POSTGRES_USER/PASSWORD/DB` |
| `REDIS_URL` | `redis://localhost:6379/0` | Shared by both the Celery broker and result backend |
| `UPLOAD_DIR` | `uploads` | **Relative path** — relative to the process's working directory at startup, see note below |
| `DEBUG` | `false` | Currently unused in code, reserved |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Must exactly match the frontend's origin (protocol + host + port), or the browser will silently block requests |

The frontend's backend URL (`http://localhost:8000`) is currently hardcoded in `frontend/src/services/api.ts` — **there is no environment variable for it**. If the backend runs on a different host/port, edit that file directly.

## Common Configuration Pitfalls

These were found by walking the code and commit history — not theoretical advice:

1. **The Celery worker must be started with `-A tasks`, not `-A celery_app`.**
   `backend/celery_app.py` only creates the Celery instance — there's no `autodiscover_tasks()` / `include=[...]`. The task is actually registered by `backend/tasks.py` via `@celery_app.task`. Starting the worker with `-A celery_app` connects to Redis fine, but the `process_document` task never gets registered, so uploads sit stuck at `PENDING` and the worker log shows `Received unregistered task of type 'process_document'`.

2. **Celery's default prefork pool often fails to start or hangs on Windows.**
   On a Windows machine, always add `--pool=solo` (single process, sufficient for local development). For real concurrency, run the worker under WSL2 or a Linux container instead.

3. **The spaCy model in `requirements.txt` is installed directly from a GitHub Releases wheel URL:**
   ```
   https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
   ```
   If GitHub access is flaky on your network, `pip install -r requirements.txt` will hang or time out on that line. Install it separately instead: `pip install spacy==3.8.2` followed by `python -m spacy download en_core_web_sm` (which goes through spaCy's own download source), or download the wheel manually and `pip install <local-wheel-path>`.

4. **`UPLOAD_DIR` is a relative path, resolved against whatever directory the process was started from.**
   Both `uvicorn` and the Celery worker must be started from `backend/` (see Getting Started above) — otherwise the two processes resolve `uploads/` to different directories, and the worker fails to find the file it's supposed to process.

5. **There is no database migration tool (no Alembic).**
   `backend/main.py` only calls `Base.metadata.create_all()` on startup, which creates missing tables but never alters existing ones. After changing a field in `db/models.py`, local development typically requires manually running `docker-compose down -v` to recreate the `postgres_data` volume (this wipes data), or hand-writing the schema-altering SQL.

6. **`.env` is not checked into the repo (`.gitignore`d) — only `.env.example` is.**
   You must copy it manually after cloning, or `pydantic-settings` falls back to the defaults baked into the code (fine in most cases, but it won't connect if you've changed your local Postgres/Neo4j password).

7. **CORS matching is exact, not prefix/wildcard.**
   `CORS_ORIGINS` only allows `http://localhost:3000` by default (matching the port hardcoded in `frontend/vite.config.ts`'s `server.port: 3000`). If you change the frontend port, access it over a LAN IP, or use `127.0.0.1` instead of `localhost`, add the matching origin to `CORS_ORIGINS` in `.env` — otherwise the browser console will show a CORS error instead of a backend error.

## Testing

```bash
cd backend
pytest -v
```

Unit tests use an in-memory SQLite database (created and torn down per test in `tests/conftest.py`) plus Celery's `task_always_eager=True` — **none** of the docker-compose services need to be running to run them. The tradeoff is that the unit tests won't catch issues in Postgres-specific types (`Uuid`, `JSON` columns) or real Neo4j Cypher statements; for changes touching those, run a full `docker-compose up -d` and exercise the upload flow manually before committing.

The frontend currently has type-checking and a build check, no unit tests:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

## CI

`.github/workflows/ci.yml` runs on `push`/`pull_request` to `main`, with two parallel jobs: `backend` (`pip install` + `pytest`) and `frontend` (`npm ci` + `tsc --noEmit` + `npm run build`). Neither job depends on Postgres/Neo4j/Redis service containers.

## Known Limitations

- The frontend does not yet call `/documents` (document list) or `/entities/{id}/evidence` (entity provenance) — the provenance data the backend already tracks isn't surfaced in the UI.
- Relationship extraction relies on 6 fixed English regex sentence patterns; there's no Chinese support and semantic coverage is limited.
- Documents aren't chunked yet (`DocumentChunk` has exactly one row per document), so provenance is only accurate at the document level.
- There is no API authentication, and the CORS configuration is meant for local development, not public deployment.
