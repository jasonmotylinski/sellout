# Catalog Grid Layout Design

## Problem

The catalog grid tops out at 2 columns regardless of screen size. On desktop,
items are displayed in wide 2-column cards that leave significant whitespace
and don't match the density of boutique reference sites (Chairish, 1stDibs).

## Approach

Add two `@media` breakpoints to the existing `.item-grid` CSS Grid rule in
`base.html`. No template changes needed — both `catalog.html` and `index.html`
already use `.item-grid`.

## Breakpoints

| Viewport     | Columns | Gap              |
|--------------|---------|------------------|
| < 500px      | 1       | 3rem 1.5rem (unchanged) |
| 500–899px    | 2       | 2.5rem 1.5rem (unchanged) |
| 900–1279px   | 3       | 2.5rem 1.5rem |
| ≥ 1280px     | 4       | 2.5rem 2rem |

## Scope

Two new `@media` blocks after the existing `@media (min-width: 500px)` rule.
Typography (`clamp` title size) scales naturally via the `vw` unit at narrower
card widths — no changes needed.
