# Sellout

A mobile-first web app for cataloging household items for sale. Add items with photos, set prices, and share a clean public view with buyers.

## Features

- **Admin view** (`/`) — add, edit, and delete items with photo uploads
- **Public catalog** (`/catalog`) — shareable read-only view for buyers, no edit controls

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000` for the admin view. Share `/catalog` with buyers.

To make the catalog accessible on your local network (e.g. from your phone):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# find your local IP
ipconfig getifaddr en0
```

Then open `http://<your-ip>:8000` on any device on the same WiFi.

## Stack

- Python 3.11+, FastAPI, Uvicorn
- Jinja2 server-rendered templates (no JS framework)
- SQLite via `sqlite3` stdlib (no ORM)
- Images stored as files in `uploads/`
