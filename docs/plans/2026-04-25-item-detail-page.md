# Item Detail Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a public `/items/{item_id}` detail page where visitors can view all item images via a main image + thumbnail strip gallery.

**Architecture:** New GET route fetches item + images using existing DB functions, renders a new `item_detail.html` template. Catalog cards become `<a>` links. Gallery interactivity handled by ~15 lines of inline vanilla JS.

**Tech Stack:** FastAPI, Jinja2, SQLite (via `database.py`), vanilla JS, inline CSS in `base.html`.

---

### Task 1: Route — GET /items/{item_id}

**Files:**
- Modify: `main.py`
- Test: `tests/test_routes.py`

**Step 1: Write the failing tests**

Add to `tests/test_routes.py`:

```python
def test_item_detail_loads(client):
    client.post("/admin/items/new", data={"title": "Vase", "description": "Blue ceramic", "price": "45.00", "status": "available"})
    response = client.get("/items/1")
    assert response.status_code == 200
    assert "Vase" in response.text
    assert "Blue ceramic" in response.text
    assert "45.00" in response.text


def test_item_detail_404(client):
    response = client.get("/items/999")
    assert response.status_code == 404
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_routes.py::test_item_detail_loads tests/test_routes.py::test_item_detail_404 -v
```

Expected: both FAIL with 404 / `TemplateNotFound` errors.

**Step 3: Add the route to main.py**

Add after the `public_catalog` route (after line 50):

```python
@app.get("/items/{item_id}", response_class=HTMLResponse)
def item_detail(item_id: int, request: Request):
    row = database.get_item(item_id)
    if row is None:
        raise HTTPException(status_code=404)
    item = dict(row)
    images = [dict(img) for img in database.get_images(item_id)]
    return templates.TemplateResponse(request, "item_detail.html", {
        "item": item,
        "images": images,
    })
```

**Step 4: Create a minimal `templates/item_detail.html`** (just enough for the test to pass — full template comes in Task 2):

```html
{% extends "base.html" %}
{% block title %}{{ item.title }} — Sellout{% endblock %}
{% block content %}
<h1>{{ item.title }}</h1>
<p>{{ item.description }}</p>
<p>${{ "%.2f"|format(item.price) }}</p>
{% endblock %}
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_routes.py::test_item_detail_loads tests/test_routes.py::test_item_detail_404 -v
```

Expected: both PASS.

**Step 6: Commit**

```bash
git add main.py templates/item_detail.html tests/test_routes.py
git commit -m "feat: add public item detail route"
```

---

### Task 2: Catalog cards become links

**Files:**
- Modify: `templates/catalog.html`
- Test: `tests/test_routes.py`

**Step 1: Write the failing test**

Add to `tests/test_routes.py`:

```python
def test_catalog_cards_link_to_detail(client):
    client.post("/admin/items/new", data={"title": "Mirror", "description": "", "price": "30.00", "status": "available"})
    response = client.get("/")
    assert 'href="/items/1"' in response.text
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_routes.py::test_catalog_cards_link_to_detail -v
```

Expected: FAIL — no such href in catalog HTML.

**Step 3: Wrap the article in an anchor in catalog.html**

Replace the current `<article ...>` block in `templates/catalog.html`:

```html
{% for item, images in items_with_images %}
<a href="/items/{{ item.id }}" class="item-card-link">
<article class="item-card{% if item.status == 'sold' %} item-card--sold{% endif %}">
  <div class="item-card__img">
    {% if images %}
    <img src="/uploads/{{ images[0].filename }}" alt="{{ item.title }}">
    {% else %}
    <div class="item-card__placeholder">◦</div>
    {% endif %}
  </div>
  <h2 class="item-card__title">{{ item.title }}</h2>
  {% if item.description %}<p class="item-card__desc">{{ item.description }}</p>{% endif %}
  <div class="item-card__footer">
    <span class="price">${{ "%.2f"|format(item.price) }}</span>
    <span class="badge badge--{{ item.status }}">{{ item.status }}</span>
  </div>
</article>
</a>
{% endfor %}
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_routes.py::test_catalog_cards_link_to_detail -v
```

Expected: PASS.

**Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS.

**Step 6: Commit**

```bash
git add templates/catalog.html tests/test_routes.py
git commit -m "feat: catalog cards link to item detail page"
```

---

### Task 3: Full item_detail.html template with image gallery

**Files:**
- Modify: `templates/item_detail.html`

This task has no new test — the route test from Task 1 already covers the page loading. The template work is visual; verify by running the dev server.

**Step 1: Replace item_detail.html with the full template**

```html
{% extends "base.html" %}
{% block title %}{{ item.title }} — Sellout{% endblock %}
{% block header_nav %}
<a href="/" class="nav-link">← All items</a>
{% endblock %}
{% block content %}
<div class="detail-layout">

  <div class="detail-images">
    {% if images %}
    <div class="detail-main-img">
      <img id="main-img" src="/uploads/{{ images[0].filename }}" alt="{{ item.title }}">
    </div>
    {% if images|length > 1 %}
    <div class="thumb-strip">
      {% for img in images %}
      <button
        class="thumb{% if loop.first %} thumb--active{% endif %}"
        data-src="/uploads/{{ img.filename }}"
        aria-label="View image {{ loop.index }}"
      >
        <img src="/uploads/{{ img.filename }}" alt="">
      </button>
      {% endfor %}
    </div>
    {% endif %}
    {% else %}
    <div class="detail-main-img detail-main-img--empty">◦</div>
    {% endif %}
  </div>

  <div class="detail-info">
    <h1 class="detail-title">{{ item.title }}</h1>
    <div class="detail-price-row">
      <span class="price">${{ "%.2f"|format(item.price) }}</span>
      <span class="badge badge--{{ item.status }}">{{ item.status }}</span>
    </div>
    {% if item.description %}
    <p class="detail-desc">{{ item.description }}</p>
    {% endif %}
  </div>

</div>

<script>
  document.addEventListener('DOMContentLoaded', function () {
    var mainImg = document.getElementById('main-img');
    if (!mainImg) return;
    document.querySelectorAll('.thumb').forEach(function (btn) {
      btn.addEventListener('click', function () {
        mainImg.src = btn.dataset.src;
        document.querySelectorAll('.thumb').forEach(function (b) {
          b.classList.remove('thumb--active');
        });
        btn.classList.add('thumb--active');
      });
    });
  });
</script>
{% endblock %}
```

**Step 2: Run existing tests to confirm nothing broke**

```bash
pytest -v
```

Expected: all PASS.

**Step 3: Commit**

```bash
git add templates/item_detail.html
git commit -m "feat: item detail template with thumbnail gallery"
```

---

### Task 4: CSS for detail page layout

**Files:**
- Modify: `templates/base.html`

Add the following CSS block inside the `<style>` tag in `base.html`, just before the closing `</style>` tag (after the `@media (prefers-reduced-motion)` block):

```css
/* ── Item detail layout ─────────────────────── */
.item-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
}
@media (min-width: 600px) {
  .detail-layout { grid-template-columns: 1fr 1fr; align-items: start; }
}

.detail-main-img {
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--cream-alt);
  border-radius: var(--r);
  margin-bottom: 0.75rem;
}
.detail-main-img img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
  transition: opacity 0.2s;
}
.detail-main-img--empty {
  display: flex; align-items: center; justify-content: center;
  color: var(--border-mid);
  font-size: 2rem;
}

.thumb-strip {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
}

.thumb {
  flex-shrink: 0;
  width: 64px; height: 64px;
  border: 2px solid transparent;
  border-radius: var(--r);
  overflow: hidden;
  cursor: pointer;
  padding: 0;
  background: none;
  transition: border-color 0.15s;
}
.thumb img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}
.thumb--active { border-color: var(--espresso); }
.thumb:hover:not(.thumb--active) { border-color: var(--border-mid); }

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: clamp(1.5rem, 4vw, 2rem);
  font-weight: 500;
  line-height: 1.15;
}

.detail-price-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.detail-desc {
  font-size: 0.95rem;
  color: var(--mid);
  line-height: 1.6;
}
```

**Step 2: Run full test suite**

```bash
pytest -v
```

Expected: all PASS.

**Step 3: Start the dev server and visually verify**

```bash
uvicorn main:app --reload
```

Check:
- Catalog cards are clickable, hover still shows image zoom
- Detail page shows main image + thumbnail strip for multi-image items
- Clicking a thumbnail swaps the main image and moves the active border
- Single-image items show no thumbnail strip
- No-image items show the cream placeholder
- Mobile layout stacks images above info panel
- Back link ("← All items") appears in header

**Step 4: Commit**

```bash
git add templates/base.html
git commit -m "feat: item detail page CSS"
```
