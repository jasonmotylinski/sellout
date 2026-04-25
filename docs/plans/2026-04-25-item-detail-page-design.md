# Item Detail Page Design

## Summary

Add a public item detail page at `/items/{item_id}` where catalog visitors can click an item and view all its images via a main image + thumbnail strip gallery.

## Route & Data

- New route: `GET /items/{item_id}` in `main.py`
- Fetches item via `database.get_item()` and images via `database.get_images()`
- Returns 404 if item not found
- Passes `item` (dict) and `images` (list of dicts) to `item_detail.html`
- Catalog cards at `/` become `<a href="/items/{{ item.id }}">` links

## Template — `item_detail.html`

Extends `base.html`. Two-column layout on desktop (images left, info right), stacked on mobile. Back link to `/` in the header nav block.

### Image Panel
- **Main image**: large display, `aspect-ratio: 4/3`, `object-fit: cover`, cream placeholder if no images
- **Thumbnail strip**: horizontal row of square thumbnails below main image; active thumb has a thin espresso border; clicking swaps main image src

### Info Panel
- Title in Cormorant Garamond
- Price (Cormorant Garamond, weighted)
- Status badge (available/sold)
- Description in DM Sans

## JavaScript

Inline `<script>` (~15 lines) on `DOMContentLoaded`. Click handlers on each thumbnail set `mainImg.src` from `data-src` attribute and toggle `.thumb--active` class. No external dependencies.

## CSS

New styles added inline to `base.html` (consistent with existing approach):
- `.detail-layout` — two-column grid, collapses to single column on mobile
- `.detail-main-img` — main image container
- `.thumb-strip` — flex row, gap, overflow-x auto for mobile
- `.thumb` — square thumbnail, cursor pointer, border transition
- `.thumb--active` — espresso border to indicate selected image
- `.detail-info` — info panel spacing

## What Does Not Change

- `database.py` — no new queries needed; `get_item()` and `get_images()` already exist
- Admin routes — unchanged
- `base.html` CSS variables and design tokens — reused as-is
