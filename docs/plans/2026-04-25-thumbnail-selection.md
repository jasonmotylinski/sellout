# Thumbnail Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let the admin pick which uploaded image appears as the catalog thumbnail by clicking "★" on any image in the edit form.

**Architecture:** Thumbnail = `images[0]` (lowest `sort_order`) — already true everywhere. Promoting an image to cover means setting its `sort_order = 0` and re-numbering the rest. A new `database.set_cover_image()` function and a new POST route handle this; the edit form gains a "★" button per non-cover image and a "Cover" badge on the current cover.

**Tech Stack:** Python, SQLite (via `database.py` module-level `_conn`), FastAPI, Jinja2 templates, vanilla CSS in `templates/base.html`.

---

### Task 1: `database.set_cover_image(item_id, image_id)`

**Files:**
- Modify: `database.py` (append after line 80)
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

Add to `tests/test_database.py`:

```python
def test_set_cover_image():
    item_id = database.create_item("Desk", "", 100.0, "available")
    img_a = database.add_image(item_id, "a.jpg", sort_order=0)
    img_b = database.add_image(item_id, "b.jpg", sort_order=1)
    img_c = database.add_image(item_id, "c.jpg", sort_order=2)

    database.set_cover_image(item_id, img_b)

    images = database.get_images(item_id)
    assert images[0]["id"] == img_b   # b is now first
    assert images[1]["id"] == img_a   # a is second
    assert images[2]["id"] == img_c   # c is third
```

**Step 2: Run to verify it fails**

```bash
.venv/bin/pytest tests/test_database.py::test_set_cover_image -v
```

Expected: `FAILED` — `AttributeError: module 'database' has no attribute 'set_cover_image'`

**Step 3: Implement `set_cover_image`**

Append to `database.py`:

```python
def set_cover_image(item_id: int, image_id: int):
    images = get_images(item_id)
    ordered = [img for img in images if img["id"] == image_id] + \
              [img for img in images if img["id"] != image_id]
    for i, img in enumerate(ordered):
        _conn.execute("UPDATE item_images SET sort_order = ? WHERE id = ?", (i, img["id"]))
    _conn.commit()
```

**Step 4: Run to verify it passes**

```bash
.venv/bin/pytest tests/test_database.py::test_set_cover_image -v
```

Expected: `PASSED`

**Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat: add set_cover_image to database"
```

---

### Task 2: Route `POST /admin/items/{item_id}/images/{image_id}/set-cover`

**Files:**
- Modify: `main.py` (append after the `delete_image_route` at line 157)
- Test: `tests/test_routes.py`

**Step 1: Write the failing test**

Add to `tests/test_routes.py`:

```python
def test_set_cover_image(client):
    client.post("/admin/items/new", data={"title": "Shelf", "description": "", "price": "20.00", "status": "available"})
    # add two fake images directly via database
    import database
    img_a = database.add_image(1, "a.jpg", sort_order=0)
    img_b = database.add_image(1, "b.jpg", sort_order=1)

    response = client.post(f"/admin/items/1/images/{img_b}/set-cover", follow_redirects=False)

    assert response.status_code == 303
    images = database.get_images(1)
    assert images[0]["id"] == img_b
```

**Step 2: Run to verify it fails**

```bash
.venv/bin/pytest tests/test_routes.py::test_set_cover_image -v
```

Expected: `FAILED` — 404 or 405 (route doesn't exist yet)

**Step 3: Add the route**

Add to `main.py` after the `delete_image_route` function (after line 157):

```python
@app.post("/admin/items/{item_id}/images/{image_id}/set-cover")
def set_cover_image_route(item_id: int, image_id: int, _=Depends(require_admin)):
    if database.get_item(item_id) is None:
        raise HTTPException(status_code=404)
    database.set_cover_image(item_id, image_id)
    return RedirectResponse(f"/admin/items/{item_id}/edit", status_code=303)
```

**Step 4: Run to verify it passes**

```bash
.venv/bin/pytest tests/test_routes.py::test_set_cover_image -v
```

Expected: `PASSED`

**Step 5: Commit**

```bash
git add main.py tests/test_routes.py
git commit -m "feat: add set-cover route"
```

---

### Task 3: Edit form UI — "★" button and "Cover" badge

**Files:**
- Modify: `templates/item_form.html` (lines 9–20, the existing image grid)
- Modify: `templates/base.html` (after `.img-del:hover` at line 249, add new CSS rules)

**Step 1: Update the image grid in `item_form.html`**

Replace the existing image grid block (lines 9–20):

```html
{% if item and images %}
<div class="img-grid">
  {% for img in images %}
  <div class="img-grid__item">
    <img src="/uploads/{{ img.filename }}" alt="photo">
    <form method="post" action="/admin/items/{{ item.id }}/images/{{ img.id }}/delete">
      <button type="submit" class="img-del" title="Remove">×</button>
    </form>
  </div>
  {% endfor %}
</div>
{% endif %}
```

With:

```html
{% if item and images %}
<div class="img-grid">
  {% for img in images %}
  <div class="img-grid__item">
    <img src="/uploads/{{ img.filename }}" alt="photo">
    {% if loop.first %}
      <span class="img-cover-badge">Cover</span>
    {% else %}
      <form method="post" action="/admin/items/{{ item.id }}/images/{{ img.id }}/set-cover">
        <button type="submit" class="img-cover" title="Set as thumbnail">★</button>
      </form>
    {% endif %}
    <form method="post" action="/admin/items/{{ item.id }}/images/{{ img.id }}/delete">
      <button type="submit" class="img-del" title="Remove">×</button>
    </form>
  </div>
  {% endfor %}
</div>
{% endif %}
```

**Step 2: Add CSS to `base.html`**

After `.img-del:hover` (line 249), add:

```css
    .img-cover {
      position: absolute; top: 4px; left: 4px;
      background: oklch(15% 0.01 60 / 0.6);
      color: white;
      border: none; border-radius: 50%;
      width: 22px; height: 22px;
      font-size: 12px; line-height: 22px;
      text-align: center; cursor: pointer; padding: 0;
      transition: background 0.15s;
    }
    .img-cover:hover { background: oklch(15% 0.01 60 / 0.85); }
    .img-cover-badge {
      position: absolute; top: 4px; left: 4px;
      background: oklch(55% 0.08 75 / 0.85);
      color: white;
      border-radius: 3px;
      font-size: 0.6rem; font-family: 'DM Sans', sans-serif;
      letter-spacing: 0.06em; text-transform: uppercase;
      padding: 2px 5px; pointer-events: none;
    }
```

**Step 3: Run full test suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all 20 tests pass (19 existing + 1 new set-cover route test from Task 2). The template change has no automated test — verify visually by starting the dev server:

```bash
.venv/bin/uvicorn main:app --reload
```

Open `http://localhost:8000/admin`, create an item with 2+ images, edit it, and confirm:
- First image shows "Cover" badge (top-left) and "×" delete (top-right)
- Other images show "★" button (top-left) and "×" delete (top-right)
- Clicking "★" reloads the form with that image now showing "Cover"

**Step 4: Commit**

```bash
git add templates/item_form.html templates/base.html
git commit -m "feat: cover image badge and set-cover button in edit form"
```
