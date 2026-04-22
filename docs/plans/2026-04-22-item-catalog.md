# Item Catalog Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a mobile-first FastAPI web app for cataloging household items for sale, with admin CRUD and a public shareable catalog view.

**Architecture:** Single FastAPI app with Jinja2 server-rendered templates. SQLite via Python's stdlib `sqlite3` (no ORM). Images stored as files in `uploads/` on disk, paths stored in the database. Two zones: admin (`/`) and public (`/catalog`).

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Jinja2, python-multipart, pytest, httpx

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `uploads/.gitkeep`
- Create: `tests/__init__.py`

**Step 1: Create `requirements.txt`**

```
fastapi
uvicorn[standard]
jinja2
python-multipart
pytest
httpx
```

**Step 2: Create `.gitignore`**

```
catalog.db
uploads/*
!uploads/.gitkeep
__pycache__/
*.pyc
.pytest_cache/
.venv/
```

**Step 3: Create directories and empty files**

```bash
mkdir -p templates uploads tests
touch uploads/.gitkeep tests/__init__.py
```

**Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 5: Commit**

```bash
git add requirements.txt .gitignore uploads/.gitkeep tests/__init__.py
git commit -m "chore: project scaffold"
```

---

### Task 2: Database Module

**Files:**
- Create: `database.py`
- Create: `tests/test_database.py`

All database functions use a module-level connection initialized by `init_db()`. No connection is passed around — callers just call the functions.

**Step 1: Write failing tests**

Create `tests/test_database.py`:

```python
import pytest
import tempfile
import os
import database


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    database.init_db(str(tmp_path / "test.db"))


def test_create_and_get_item():
    item_id = database.create_item(title="Couch", description="Blue sofa", price=50.0, status="available")
    item = database.get_item(item_id)
    assert item["title"] == "Couch"
    assert item["price"] == 50.0
    assert item["status"] == "available"


def test_list_items():
    database.create_item(title="Chair", description="", price=10.0, status="available")
    database.create_item(title="Table", description="", price=20.0, status="sold")
    items = database.list_items()
    assert len(items) == 2


def test_update_item():
    item_id = database.create_item(title="Lamp", description="", price=5.0, status="available")
    database.update_item(item_id, title="Floor Lamp", description="Tall", price=8.0, status="sold")
    item = database.get_item(item_id)
    assert item["title"] == "Floor Lamp"
    assert item["status"] == "sold"


def test_delete_item():
    item_id = database.create_item(title="Box", description="", price=1.0, status="available")
    database.delete_item(item_id)
    assert database.get_item(item_id) is None


def test_add_and_get_images():
    item_id = database.create_item(title="Desk", description="", price=30.0, status="available")
    database.add_image(item_id, filename="abc123.jpg", sort_order=0)
    database.add_image(item_id, filename="def456.jpg", sort_order=1)
    images = database.get_images(item_id)
    assert len(images) == 2
    assert images[0]["filename"] == "abc123.jpg"


def test_delete_image():
    item_id = database.create_item(title="Shelf", description="", price=15.0, status="available")
    img_id = database.add_image(item_id, filename="img.jpg", sort_order=0)
    database.delete_image(img_id)
    assert database.get_images(item_id) == []


def test_delete_item_cascades_images():
    item_id = database.create_item(title="Wardrobe", description="", price=100.0, status="available")
    database.add_image(item_id, filename="img.jpg", sort_order=0)
    database.delete_item(item_id)
    assert database.get_images(item_id) == []
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_database.py -v
```

Expected: `ImportError` — `database` module doesn't exist yet.

**Step 3: Create `database.py`**

```python
import sqlite3
from typing import Optional

_conn: Optional[sqlite3.Connection] = None


def init_db(path: str = "catalog.db") -> sqlite3.Connection:
    global _conn
    _conn = sqlite3.connect(path, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")
    _conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS item_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
    """)
    _conn.commit()
    return _conn


def create_item(title: str, description: str, price: float, status: str) -> int:
    cur = _conn.execute(
        "INSERT INTO items (title, description, price, status) VALUES (?, ?, ?, ?)",
        (title, description, price, status),
    )
    _conn.commit()
    return cur.lastrowid


def get_item(item_id: int) -> Optional[sqlite3.Row]:
    return _conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def list_items() -> list:
    return _conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()


def update_item(item_id: int, title: str, description: str, price: float, status: str):
    _conn.execute(
        "UPDATE items SET title=?, description=?, price=?, status=? WHERE id=?",
        (title, description, price, status, item_id),
    )
    _conn.commit()


def delete_item(item_id: int):
    _conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    _conn.commit()


def add_image(item_id: int, filename: str, sort_order: int = 0) -> int:
    cur = _conn.execute(
        "INSERT INTO item_images (item_id, filename, sort_order) VALUES (?, ?, ?)",
        (item_id, filename, sort_order),
    )
    _conn.commit()
    return cur.lastrowid


def get_images(item_id: int) -> list:
    return _conn.execute(
        "SELECT * FROM item_images WHERE item_id = ? ORDER BY sort_order",
        (item_id,),
    ).fetchall()


def delete_image(image_id: int):
    _conn.execute("DELETE FROM item_images WHERE id = ?", (image_id,))
    _conn.commit()
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_database.py -v
```

Expected: All 7 tests PASS.

**Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat: database module with SQLite schema and CRUD"
```

---

### Task 3: FastAPI App + Templates

**Files:**
- Create: `main.py`
- Create: `templates/base.html`
- Create: `templates/index.html`
- Create: `templates/catalog.html`
- Create: `templates/item_form.html`
- Create: `tests/conftest.py`
- Create: `tests/test_routes.py`

**Step 1: Write failing route tests**

Create `tests/conftest.py`:

```python
import pytest
import os
import database
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    database.init_db(str(tmp_path / "test.db"))
    import main
    main.UPLOADS_DIR = str(uploads)
    return TestClient(main.app)
```

Create `tests/test_routes.py`:

```python
def test_admin_list_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Add Item" in response.text


def test_new_item_form_loads(client):
    response = client.get("/items/new")
    assert response.status_code == 200
    assert "<form" in response.text


def test_catalog_loads(client):
    response = client.get("/catalog")
    assert response.status_code == 200


def test_create_item_redirects(client):
    response = client.post(
        "/items/new",
        data={"title": "Couch", "description": "Blue", "price": "50.00", "status": "available"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_created_item_appears_in_list(client):
    client.post("/items/new", data={"title": "Chair", "description": "", "price": "10.00", "status": "available"})
    response = client.get("/")
    assert "Chair" in response.text


def test_created_item_appears_in_catalog(client):
    client.post("/items/new", data={"title": "Table", "description": "Oak", "price": "80.00", "status": "available"})
    response = client.get("/catalog")
    assert "Table" in response.text


def test_edit_item_form_loads(client):
    client.post("/items/new", data={"title": "Lamp", "description": "", "price": "5.00", "status": "available"})
    response = client.get("/items/1/edit")
    assert response.status_code == 200
    assert "Lamp" in response.text


def test_update_item(client):
    client.post("/items/new", data={"title": "Old Name", "description": "", "price": "5.00", "status": "available"})
    client.post("/items/1/edit", data={"title": "New Name", "description": "", "price": "8.00", "status": "sold"})
    response = client.get("/")
    assert "New Name" in response.text


def test_delete_item(client):
    client.post("/items/new", data={"title": "Gone", "description": "", "price": "1.00", "status": "available"})
    client.post("/items/1/delete")
    response = client.get("/")
    assert "Gone" not in response.text
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_routes.py -v
```

Expected: `ImportError` — `main` module doesn't exist yet.

**Step 3: Create `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Item Catalog{% endblock %}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f4f4f8; color: #222; }
    .header { background: #1a1a2e; color: white; padding: 1rem 1.25rem; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }
    .header h1 { font-size: 1.15rem; font-weight: 700; }
    .header a { color: #aac4e0; text-decoration: none; font-size: 0.9rem; }
    .container { max-width: 600px; margin: 0 auto; padding: 1rem; }
    .btn { display: inline-block; padding: 0.75rem 1.25rem; border-radius: 10px; border: none; font-size: 1rem; font-weight: 600; cursor: pointer; text-decoration: none; text-align: center; transition: opacity 0.15s; }
    .btn:active { opacity: 0.8; }
    .btn-primary { background: #e63946; color: white; }
    .btn-secondary { background: #457b9d; color: white; }
    .btn-danger { background: #c0392b; color: white; }
    .btn-block { display: block; width: 100%; }
    .card { background: white; border-radius: 14px; overflow: hidden; margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }
    .card-img { width: 100%; height: 220px; object-fit: cover; background: #eee; display: block; }
    .card-img-placeholder { width: 100%; height: 140px; background: #e8e8f0; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 2rem; }
    .card-body { padding: 0.85rem 1rem 1rem; }
    .card-body h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }
    .card-description { color: #555; font-size: 0.9rem; margin-bottom: 0.5rem; line-height: 1.4; }
    .price { font-size: 1.4rem; font-weight: 700; color: #e63946; }
    .badge { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; margin-left: 0.5rem; }
    .badge-available { background: #d4edda; color: #155724; }
    .badge-sold { background: #f8d7da; color: #721c24; }
    .item-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 0.75rem; }
    .form-group { margin-bottom: 1.1rem; }
    label { display: block; margin-bottom: 0.4rem; font-weight: 600; font-size: 0.9rem; color: #444; }
    input[type=text], input[type=number], textarea, select {
      width: 100%; padding: 0.8rem; border: 1.5px solid #ddd; border-radius: 10px;
      font-size: 1rem; font-family: inherit; background: white; transition: border-color 0.15s;
    }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #457b9d; }
    textarea { min-height: 100px; resize: vertical; }
    .upload-area { border: 2px dashed #457b9d; border-radius: 10px; padding: 1.5rem; text-align: center; background: #f0f7ff; cursor: pointer; }
    .upload-area p { color: #457b9d; font-weight: 600; margin-bottom: 0.5rem; }
    .upload-area input[type=file] { width: 100%; margin-top: 0.5rem; }
    .existing-images { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; }
    .existing-images .img-wrap { position: relative; }
    .existing-images img { width: 100%; height: 90px; object-fit: cover; border-radius: 8px; display: block; }
    .img-delete-btn { position: absolute; top: 3px; right: 3px; background: rgba(0,0,0,0.65); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; font-size: 0.85rem; line-height: 24px; text-align: center; cursor: pointer; padding: 0; }
    .new-previews { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-top: 0.75rem; }
    .new-previews img { width: 100%; height: 90px; object-fit: cover; border-radius: 8px; }
    .no-items { text-align: center; padding: 3rem 1rem; color: #999; }
    .no-items p { font-size: 1.1rem; }
    .divider { border: none; border-top: 1px solid #eee; margin: 1.5rem 0; }
    .add-btn-wrap { margin: 1rem 0 0.5rem; }
  </style>
</head>
<body>
  <div class="header">
    <h1>{% block header_title %}Item Catalog{% endblock %}</h1>
    {% block header_action %}{% endblock %}
  </div>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

**Step 4: Create `templates/index.html`**

```html
{% extends "base.html" %}
{% block title %}Admin — Items{% endblock %}
{% block header_title %}My Items{% endblock %}
{% block header_action %}<a href="/catalog">Public View →</a>{% endblock %}
{% block content %}
<div class="add-btn-wrap">
  <a href="/items/new" class="btn btn-primary btn-block">+ Add Item</a>
</div>
{% if not items_with_images %}
<div class="no-items"><p>No items yet. Tap Add Item to get started.</p></div>
{% else %}
{% for item, images in items_with_images %}
<div class="card">
  {% if images %}
  <img class="card-img" src="/uploads/{{ images[0].filename }}" alt="{{ item.title }}">
  {% else %}
  <div class="card-img-placeholder">📦</div>
  {% endif %}
  <div class="card-body">
    <h2>{{ item.title }}</h2>
    {% if item.description %}<p class="card-description">{{ item.description }}</p>{% endif %}
    <div class="item-footer">
      <span class="price">${{ "%.2f"|format(item.price) }}<span class="badge badge-{{ item.status }}">{{ item.status }}</span></span>
      <a href="/items/{{ item.id }}/edit" class="btn btn-secondary">Edit</a>
    </div>
  </div>
</div>
{% endfor %}
{% endif %}
{% endblock %}
```

**Step 5: Create `templates/catalog.html`**

```html
{% extends "base.html" %}
{% block title %}For Sale{% endblock %}
{% block header_title %}For Sale{% endblock %}
{% block content %}
{% if not items_with_images %}
<div class="no-items"><p>No items listed yet. Check back soon!</p></div>
{% else %}
{% for item, images in items_with_images %}
<div class="card">
  {% if images %}
  <img class="card-img" src="/uploads/{{ images[0].filename }}" alt="{{ item.title }}">
  {% else %}
  <div class="card-img-placeholder">📦</div>
  {% endif %}
  <div class="card-body">
    <h2>{{ item.title }}</h2>
    {% if item.description %}<p class="card-description">{{ item.description }}</p>{% endif %}
    <div class="item-footer">
      <span class="price">${{ "%.2f"|format(item.price) }}</span>
      <span class="badge badge-{{ item.status }}">{{ item.status }}</span>
    </div>
  </div>
</div>
{% endfor %}
{% endif %}
{% endblock %}
```

**Step 6: Create `templates/item_form.html`**

```html
{% extends "base.html" %}
{% block title %}{% if item %}Edit Item{% else %}New Item{% endif %}{% endblock %}
{% block header_title %}{% if item %}Edit Item{% else %}New Item{% endif %}{% endblock %}
{% block header_action %}<a href="/">← Back</a>{% endblock %}
{% block content %}
<form method="post" enctype="multipart/form-data" style="margin-top: 1rem;">
  <div class="form-group">
    <label for="title">Title</label>
    <input type="text" id="title" name="title" value="{{ item.title if item else '' }}" required placeholder="e.g. Blue sofa">
  </div>
  <div class="form-group">
    <label for="description">Description</label>
    <textarea id="description" name="description" placeholder="Condition, dimensions, any notes…">{{ item.description if item else '' }}</textarea>
  </div>
  <div class="form-group">
    <label for="price">Price ($)</label>
    <input type="number" id="price" name="price" step="0.01" min="0" value="{{ item.price if item else '' }}" required placeholder="0.00">
  </div>
  <div class="form-group">
    <label for="status">Status</label>
    <select id="status" name="status">
      <option value="available" {% if not item or item.status == 'available' %}selected{% endif %}>Available</option>
      <option value="sold" {% if item and item.status == 'sold' %}selected{% endif %}>Sold</option>
    </select>
  </div>
  <div class="form-group">
    <label>Photos</label>
    {% if images %}
    <div class="existing-images">
      {% for img in images %}
      <div class="img-wrap">
        <img src="/uploads/{{ img.filename }}" alt="photo">
        <form method="post" action="/items/{{ item.id }}/images/{{ img.id }}/delete" style="display:inline;">
          <button type="submit" class="img-delete-btn" title="Remove photo">×</button>
        </form>
      </div>
      {% endfor %}
    </div>
    {% endif %}
    <div class="upload-area">
      <p>📷 Tap to add photos</p>
      <input type="file" name="images" accept="image/*" capture="environment" multiple id="imageInput">
    </div>
    <div class="new-previews" id="newPreviews"></div>
  </div>
  <button type="submit" class="btn btn-primary btn-block">Save Item</button>
</form>
{% if item %}
<hr class="divider">
<form method="post" action="/items/{{ item.id }}/delete">
  <button type="submit" class="btn btn-danger btn-block"
    onclick="return confirm('Delete this item and all its photos?')">Delete Item</button>
</form>
{% endif %}
<script>
document.getElementById('imageInput').addEventListener('change', function(e) {
  const preview = document.getElementById('newPreviews');
  preview.innerHTML = '';
  Array.from(e.target.files).forEach(function(file) {
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    preview.appendChild(img);
  });
});
</script>
{% endblock %}
```

**Step 7: Create `main.py`**

```python
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database

DB_PATH = os.environ.get("DB_PATH", "catalog.db")
UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "uploads")

Path(UPLOADS_DIR).mkdir(exist_ok=True)
database.init_db(DB_PATH)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory="templates")


def _items_with_images():
    items = database.list_items()
    return [(item, database.get_images(item["id"])) for item in items]


@app.get("/", response_class=HTMLResponse)
def admin_list(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items_with_images": _items_with_images(),
    })


@app.get("/catalog", response_class=HTMLResponse)
def public_catalog(request: Request):
    return templates.TemplateResponse("catalog.html", {
        "request": request,
        "items_with_images": _items_with_images(),
    })


@app.get("/items/new", response_class=HTMLResponse)
def new_item_form(request: Request):
    return templates.TemplateResponse("item_form.html", {
        "request": request,
        "item": None,
        "images": [],
    })


@app.post("/items/new")
async def create_item(
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: str = Form("available"),
    images: List[UploadFile] = File(default=[]),
):
    item_id = database.create_item(title=title, description=description, price=price, status=status)
    for i, image in enumerate(images):
        if image.filename:
            ext = Path(image.filename).suffix.lower() or ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            dest = Path(UPLOADS_DIR) / filename
            dest.write_bytes(await image.read())
            database.add_image(item_id, filename=filename, sort_order=i)
    return RedirectResponse("/", status_code=303)


@app.get("/items/{item_id}/edit", response_class=HTMLResponse)
def edit_item_form(item_id: int, request: Request):
    item = database.get_item(item_id)
    images = database.get_images(item_id)
    return templates.TemplateResponse("item_form.html", {
        "request": request,
        "item": item,
        "images": images,
    })


@app.post("/items/{item_id}/edit")
async def update_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: str = Form("available"),
    images: List[UploadFile] = File(default=[]),
):
    database.update_item(item_id, title=title, description=description, price=price, status=status)
    existing_count = len(database.get_images(item_id))
    for i, image in enumerate(images):
        if image.filename:
            ext = Path(image.filename).suffix.lower() or ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            dest = Path(UPLOADS_DIR) / filename
            dest.write_bytes(await image.read())
            database.add_image(item_id, filename=filename, sort_order=existing_count + i)
    return RedirectResponse(f"/items/{item_id}/edit", status_code=303)


@app.post("/items/{item_id}/delete")
def delete_item(item_id: int):
    database.delete_item(item_id)
    return RedirectResponse("/", status_code=303)


@app.post("/items/{item_id}/images/{image_id}/delete")
def delete_image(item_id: int, image_id: int):
    database.delete_image(image_id)
    return RedirectResponse(f"/items/{item_id}/edit", status_code=303)
```

**Step 8: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests PASS (7 database + 9 route tests).

**Step 9: Commit**

```bash
git add main.py templates/ tests/conftest.py tests/test_routes.py
git commit -m "feat: FastAPI app with all routes and templates"
```

---

### Task 4: Manual Smoke Test

**Step 1: Start the server**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Step 2: Test on desktop browser — verify each of these**

- [ ] `http://localhost:8000` loads with "Add Item" button
- [ ] `/items/new` shows the form
- [ ] Create an item with description, price, and at least one image — redirects back to `/`
- [ ] Item appears in the list with thumbnail, title, price, and status badge
- [ ] Edit item loads pre-filled with existing images shown
- [ ] Can delete an individual image from an item
- [ ] Can add more images when editing
- [ ] Update saves correctly
- [ ] Delete item removes it from the list
- [ ] `/catalog` shows items without edit controls

**Step 3: Find your local IP and test on phone**

```bash
ipconfig getifaddr en0   # macOS WiFi interface
```

Open `http://<your-ip>:8000` on your phone and verify:
- [ ] Layout looks good on mobile
- [ ] "Add Item" button is large and tappable
- [ ] The photo input opens your camera (or photo library)
- [ ] Multiple photos show as previews before saving
- [ ] Cards are readable with adequate spacing

**Step 4: Test the public catalog URL**

Share `http://<your-ip>:8000/catalog` with someone on your local network and confirm they can see items but have no edit controls.

**Step 5: Commit any fixes**

```bash
git add -p
git commit -m "fix: mobile UI adjustments from smoke test"
```

---

## Running in Production (optional ngrok tunnel for public sharing)

To share the catalog with buyers outside your local network:

```bash
# Install ngrok if not already installed
brew install ngrok

# Expose port 8000
ngrok http 8000
```

Share the resulting `https://<id>.ngrok.io/catalog` URL with buyers.
