# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the dev server
uvicorn main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_routes.py

# Run a single test
pytest tests/test_routes.py::test_create_item_redirects
```

Dependencies are managed with a venv at `.venv/`. Activate with `source .venv/bin/activate` if needed, but `pytest` and `uvicorn` are available directly from `.venv/bin/`.

## Architecture

The app is a server-rendered FastAPI app with two modules:

- **`database.py`** — thin SQLite wrapper using a module-level `_conn` singleton. `init_db(path)` must be called before any other function. All functions operate on `_conn` directly — no ORM, no dependency injection.
- **`main.py`** — FastAPI app with Jinja2 templates and `multipart/form-data` routes. Image uploads are stored as files in `UPLOADS_DIR` (default: `uploads/`), served via a static mount at `/uploads`. Env vars (`DB_PATH`, `UPLOADS_DIR`, `ADMIN_USER`, `ADMIN_PASS`) are loaded from `.env` via `python-dotenv`.

**Two views:**
- `/` — public-facing catalog (no edit controls)
- `/admin` — admin list with add/edit/delete; all `/admin/*` routes require HTTP basic auth via the `require_admin` dependency (`ADMIN_USER`/`ADMIN_PASS` env vars, default `admin`/`admin`)

**Schema:** `items` (id, title, description, price, status, created_at) + `item_images` (id, item_id, filename, sort_order). Images cascade-delete when their item is deleted.

**Templates** all extend `templates/base.html`, which includes all CSS inline (no external stylesheet or JS framework).

## Testing

Tests use `pytest` with `FastAPI`'s `TestClient` (backed by `httpx`). The `client` fixture in `conftest.py` calls `database.init_db()` with a `tmp_path` database and patches `main.UPLOADS_DIR` to a temp directory — no disk or DB state leaks between tests. `test_database.py` uses an `autouse` fixture to reinitialize the DB per test.
