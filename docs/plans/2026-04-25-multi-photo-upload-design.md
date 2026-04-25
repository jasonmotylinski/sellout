# Multi-photo upload (JS accumulator)

## Problem

On iOS, "Take Photo" is single-shot — each new file picker selection replaces the
previous one in the `<input>`, so photos taken one at a time are lost. The backend
already accepts multiple files; the gap is entirely in the frontend.

## Approach

Maintain a JS array of `File` objects in page scope. Each time the file picker closes,
append new selections (de-duplicating by name+size+lastModified). Before the form
submits, write the accumulated array back to the input's `.files` via `DataTransfer`
so the standard multipart POST sends them all. No backend changes required.

## Design

**HTML**
- Hide the raw `<input type="file" accept="image/*" multiple>`.
- Add a visible "Add photos" button that triggers it via `.click()`.
- Keep the existing `.preview-grid` for thumbnails.

**JS accumulator**
- `let accumulated = []` holds the current pool of `File` objects.
- On `input change`: read `e.target.files`, push new files (skip duplicates), reset
  input value so the same file can be re-added after removal, write pool back to
  input via `DataTransfer`, re-render thumbnails.
- On thumbnail ×: splice file from `accumulated`, re-render, write back via
  `DataTransfer`.
- `render()` rebuilds the thumbnail strip from `accumulated` each time.

**Preview strip**
- One `<img>` per accumulated file, each with an `×` overlay button.
- "Add photos" button remains visible below the strip at all times.

## Out of scope

Drag-and-drop reordering, upload progress indicators, file size/type validation.
