# Multi-photo Upload Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow the admin photo picker to accumulate photos across multiple taps (camera or library) so iOS users can add photos one at a time without losing previous selections.

**Architecture:** Pure frontend change — a JS IIFE maintains a `File[]` array, appends on each picker close, de-duplicates, writes back to the hidden `<input>` via `DataTransfer` before the form submits. No backend changes.

**Tech Stack:** Vanilla JS, Jinja2 HTML template (`templates/item_form.html`), FastAPI TestClient (`tests/test_routes.py`)

---

### Task 1: Verify baseline

**Files:**
- Read: `templates/item_form.html`
- Run: `tests/test_routes.py`

**Step 1: Run existing tests**

```bash
.venv/bin/pytest tests/test_routes.py -v
```

Expected: all tests pass. If any fail, stop and fix before continuing.

**Step 2: Note existing behavior**

The current `<input type="file" name="images" accept="image/*" multiple id="imageInput">` is visible and has a `change` listener that replaces `#newPreviews` on each pick. This is what we're replacing.

---

### Task 2: Rewrite the Photos field in `item_form.html`

**Files:**
- Modify: `templates/item_form.html` (lines 45–74 — the Photos `form-row` and `<script>` block)

**Step 1: Replace the upload zone and script**

Replace the entire Photos `<div class="form-row">` block and the `<script>` block with:

```html
  <div class="form-row">
    <label class="form-label">Photos</label>
    <div class="preview-grid" id="newPreviews"></div>
    <input type="file" name="images" accept="image/*" multiple id="imageInput" style="display:none">
    <button type="button" class="btn btn--secondary btn--block" id="addPhotosBtn">Add photos</button>
  </div>
  <button type="submit" class="btn btn--primary btn--block">Save item</button>
</form>

{% if item %}
<hr class="divider">
<form method="post" action="/admin/items/{{ item.id }}/delete">
  <button type="submit" class="btn btn--danger btn--block"
    onclick="return confirm('Delete this item and all its photos?')">Delete item</button>
</form>
{% endif %}

<script>
(function () {
  var accumulated = [];
  var input = document.getElementById('imageInput');
  var addBtn = document.getElementById('addPhotosBtn');
  var preview = document.getElementById('newPreviews');

  addBtn.addEventListener('click', function () {
    input.value = '';
    input.click();
  });

  input.addEventListener('change', function (e) {
    Array.from(e.target.files).forEach(function (file) {
      var dup = accumulated.some(function (f) {
        return f.name === file.name && f.size === file.size && f.lastModified === file.lastModified;
      });
      if (!dup) accumulated.push(file);
    });
    syncInput();
    render();
  });

  function syncInput() {
    var dt = new DataTransfer();
    accumulated.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;
  }

  function render() {
    preview.innerHTML = '';
    accumulated.forEach(function (file, idx) {
      var wrap = document.createElement('div');
      wrap.className = 'img-grid__item';
      var img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      var del = document.createElement('button');
      del.type = 'button';
      del.className = 'img-del';
      del.title = 'Remove';
      del.textContent = '×';
      del.addEventListener('click', function () {
        URL.revokeObjectURL(img.src);
        accumulated.splice(idx, 1);
        syncInput();
        render();
      });
      wrap.appendChild(img);
      wrap.appendChild(del);
      preview.appendChild(wrap);
    });
  }
}());
</script>
```

**Step 2: Verify the file looks right**

The final `{% block content %}` should have this structure:
1. `page-header` div
2. Existing image grid (for edit view)
3. `<form method="post" enctype="multipart/form-data">` with title, description, price, status, photos rows, then Save button
4. `</form>`
5. Optional delete form (edit view only)
6. `<script>` IIFE

**Step 3: Check for a `btn--secondary` style**

```bash
grep -n "btn--secondary" templates/base.html
```

If not found, add to `base.html` inside the `<style>` block alongside `.btn--danger`:

```css
.btn--secondary { background: var(--color-bg); color: var(--color-text); border: 1px solid var(--color-border, #ccc); }
```

---

### Task 3: Run tests to verify no regression

**Files:**
- Run: `tests/test_routes.py`

**Step 1: Run full test suite**

```bash
.venv/bin/pytest tests/test_routes.py -v
```

Expected: all tests pass. The form submission behavior is unchanged — the `<input name="images">` is still present in the form, still submitted as multipart, so the backend routes are unaffected.

**Step 2: Spot-check the template renders**

```bash
.venv/bin/pytest tests/ -v
```

All 18 tests should pass.

---

### Task 4: Commit

```bash
git add templates/item_form.html templates/base.html
git commit -m "feature: accumulate photos across multiple picker taps on mobile"
```
