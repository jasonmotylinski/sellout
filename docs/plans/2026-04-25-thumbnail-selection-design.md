# Thumbnail Selection Design

## Problem

Items with multiple images always show the first-uploaded photo as the catalog
thumbnail. There's no way to change which image appears on the catalog grid without
deleting and re-uploading images in the right order.

## Approach

The thumbnail is already determined by `images[0]` (lowest `sort_order`). Promote
any image to cover by reassigning sort orders — no schema change required. Expose
this via an explicit per-image "★ Cover" button in the edit form.

## Design

**Backend**
- New function `database.set_cover_image(item_id, image_id)`: sets the target
  image's `sort_order = 0`, assigns `1, 2, 3…` to the rest in their current order.
- New route `POST /admin/items/{item_id}/images/{image_id}/set-cover`, protected by
  `require_admin`. Calls `set_cover_image`, redirects back to edit form.

**Frontend (edit form only)**
- Each image tile in the existing grid gets a small "★ Cover" form+button alongside
  the existing delete button.
- The current thumbnail tile (first image) shows a static "Cover" badge instead of
  the button, making the active state obvious.
- Catalog and index templates unchanged — they already use `images[0]`.

**Testing**
- One new test: create item with two images, POST set-cover for the second, confirm
  `get_images()` now returns it first.

## Out of scope

Full image reordering, drag-and-drop sorting.
