# Catalog Grid Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add two responsive breakpoints so the catalog shows 3 columns at 900–1279px and 4 columns at ≥1280px, while keeping the existing 1-column mobile and 2-column tablet behavior.

**Architecture:** Pure CSS change — two new `@media` blocks added after the existing `@media (min-width: 500px)` rule in `templates/base.html` (line 85–87). No template or backend changes needed; both `catalog.html` and `index.html` already use `.item-grid`.

**Tech Stack:** CSS Grid, inline `<style>` in `templates/base.html`.

---

### Task 1: Add 3-column and 4-column breakpoints

**Files:**
- Modify: `templates/base.html:85-87`

**Step 1: Verify the baseline**

The current media query block (lines 85–87 of `templates/base.html`) looks like:

```css
@media (min-width: 500px) {
  .item-grid { grid-template-columns: 1fr 1fr; gap: 2.5rem 1.5rem; }
}
```

Confirm this by reading the file. Do not proceed if it looks different.

**Step 2: Add the two new breakpoints**

Replace lines 85–87 with:

```css
@media (min-width: 500px) {
  .item-grid { grid-template-columns: 1fr 1fr; gap: 2.5rem 1.5rem; }
}
@media (min-width: 900px) {
  .item-grid { grid-template-columns: repeat(3, 1fr); gap: 2.5rem 1.5rem; }
}
@media (min-width: 1280px) {
  .item-grid { grid-template-columns: repeat(4, 1fr); gap: 2.5rem 2rem; }
}
```

Key details:
- `repeat(3, 1fr)` and `repeat(4, 1fr)` — explicit column counts, not auto-fill
- 900px breakpoint: same gap as 2-column (cards still roomy)
- 1280px breakpoint: column gap widens to `2rem` (cards are narrower, need breathing room)
- Mobile (< 500px) stays at 1 column — unchanged

**Step 3: Run the test suite**

```bash
/Users/jason/code/personal/item_catalog/.venv/bin/pytest /Users/jason/code/personal/item_catalog/tests/ -v
```

Expected: 31 passed, 0 failed. (This is a CSS-only change; the test suite has no visual regression tests. The pass confirms no template or route was accidentally broken.)

**Step 4: Visually verify in a browser**

Start the dev server:

```bash
cd /Users/jason/code/personal/item_catalog && .venv/bin/uvicorn main:app --reload
```

Open `http://localhost:8000` and verify:
- Narrow the window to < 500px → 1 column
- 500–899px → 2 columns
- 900–1279px → 3 columns
- ≥ 1280px → 4 columns

Use browser DevTools responsive mode to check all four widths quickly.

**Step 5: Commit**

```bash
git add templates/base.html
git commit -m "feat: responsive catalog grid — 3 columns at 900px, 4 at 1280px"
```
