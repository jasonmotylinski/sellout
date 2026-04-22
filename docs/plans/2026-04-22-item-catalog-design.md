# Item Catalog App — Design

**Date:** 2026-04-22  
**Status:** Approved

## Overview

A quick mobile-first web app for cataloging household items for sale during a house move. Captures multiple photos, a description, and a price per item. Has a public-facing catalog view that can be shared with potential buyers.

## Architecture

Single FastAPI app with Jinja2 server-rendered templates. SQLite via the Python `sqlite3` stdlib (no ORM). Images stored as files on disk in an `uploads/` directory, with paths recorded in the database. App starts with `uvicorn`.

Two zones:
- **Admin** — password-free, local-use UI for managing items
- **Public** — read-only catalog view at `/catalog`, shareable via URL

## Data Model

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'available',  -- 'available' or 'sold'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);
```

## Pages

| Route | Zone | Purpose |
|---|---|---|
| `/` | Admin | Card grid of all items with thumbnail, title, price, status. "Add Item" button at top. |
| `/items/new` | Admin | Form: title, description, price, status, multi-image capture. |
| `/items/{id}/edit` | Admin | Pre-filled edit form. Delete individual images or add more. |
| `/catalog` | Public | Read-only card grid. Clean, shareable. |

Images uploaded via `multipart/form-data`. Mobile camera triggered via `<input type="file" accept="image/*" capture="environment">`.

## Project Structure

```
item_catalog/
  main.py           # FastAPI app, routes
  database.py       # SQLite connection, schema init, queries
  templates/
    base.html
    index.html
    item_form.html
    catalog.html
  uploads/          # Image files (gitignored)
  requirements.txt
  docs/
    plans/
```

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access admin from phone on local network: `http://<your-laptop-ip>:8000`  
Share catalog publicly via ngrok or similar tunnel: `http://<tunnel-url>/catalog`

## Dependencies

- `fastapi`
- `uvicorn`
- `jinja2`
- `python-multipart`
