# Sellout

A mobile-first web app for cataloging household items for sale. Add items with photos, set prices, and share a clean public view with buyers.

## Features

- **Public catalog** (`/`) — shareable read-only view for buyers, no edit controls
- **Admin** (`/admin`) — add, edit, and delete items with photo uploads; protected by HTTP basic auth

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your credentials:

```
ADMIN_USER=yourname
ADMIN_PASS=yourpassword
```

## Running

```bash
uvicorn main:app --reload
```

Share `/` with buyers. Access `/admin` with your credentials to manage items.

To make it accessible on your local network (e.g. from your phone):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# find your local IP
ipconfig getifaddr en0
```

## Stack

- Python 3.11+, FastAPI, Uvicorn
- Jinja2 server-rendered templates (no JS framework)
- SQLite via `sqlite3` stdlib (no ORM)
- Images stored as files in `uploads/`
- `python-dotenv` for env config
