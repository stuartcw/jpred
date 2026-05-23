# JPred 2026 — Mobile Upgrade Proposal

## Summary

The desktop site is well-designed and should remain unchanged. The mobile experience has several specific, fixable problems. This document describes what is broken, why, and exactly what to change.

All changes are CSS and HTML template only. No Python scripts need to be touched.

---

## Files to change

| File | Change type |
|------|-------------|
| `style.css` | CSS rewrite for mobile breakpoints |
| `templates/index.html` | Wrap tables in scroll container; fix duplicate HTML tags |
| `templates/users.html` | Wrap tables; fix duplicate HTML tags |
| `templates/user_template.html` | Wrap tables; fix duplicate HTML tags |
| `templates/template.html` | Wrap tables; fix duplicate HTML tags |
| `templates/teams.html` | No changes needed — already mobile-friendly |

---

## Problem 1: Tables break at 768px

### What is happening

At `max-width: 768px` the CSS converts every table row into a stacked block:

```css
tr { display: block; margin-bottom: 15px; }
th, td { display: block; text-align: left; }
```

The `<thead>` is still rendered (headers are visible), but the cells are now stacked vertically. Headers no longer correspond visually to their cells. The 6-column leaderboard (Rank, Name, Points, J1 Exact, J2/3 Exact, Total Exact) becomes a very tall, confusing block of unlabelled values.

### Fix

Remove the stacking rules entirely from the `768px` breakpoint. Replace with a horizontal scroll container.

**In `style.css`** — change the `@media (max-width: 768px)` block to:

```css
@media (max-width: 768px) {
    body { padding: 10px; }
    .content { padding: 15px; }
    th, td { padding: 6px; }
    a { word-wrap: break-word; }
}
```

Add a new utility class (outside any breakpoint):

```css
.table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin-top: 20px;
}

.table-wrap table {
    margin-top: 0;
    min-width: 500px;
}
```

**In every template** — wrap each `<table>` tag:

```html
<div class="table-wrap">
    <table>
        ...
    </table>
</div>
```

This gives users a swipeable table on mobile. All columns remain readable, headers align with cells, and nothing breaks.

---

## Problem 2: Card layout at 480px is broken

### What is happening

At `max-width: 480px` the CSS hides the `<thead>` and shows a label before each cell using:

```css
tbody tr td::before {
    content: attr(data-label);
    font-weight: bold;
    display: inline-block;
    width: 50%;
}
```

The `width: 50%` is hardcoded. Labels like "Exact Matches J2/3" are too long for 50% of a phone screen and wrap onto multiple lines, making rows unexpectedly tall. The layout also uses `display: flex; flex-direction: column` on `tbody tr` which, combined with `display: inline-block` on `::before`, produces inconsistent alignment.

### Fix

Replace the `td::before` block with a flex-based approach:

```css
@media (max-width: 480px) {
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1rem; }

    th { display: none; }

    tbody tr {
        display: block;
        border: 1px solid #ddd;
        border-radius: 6px;
        margin-bottom: 12px;
        padding: 4px 0;
    }

    td {
        display: flex;
        align-items: baseline;
        gap: 0.5em;
        padding: 6px 10px;
        border-bottom: 1px solid #eee;
        font-size: 14px;
    }

    td:last-child { border-bottom: none; }

    td::before {
        content: attr(data-label);
        font-weight: 700;
        flex-shrink: 0;
        min-width: 7em;
        color: #555;
    }
}
```

The `min-width: 7em` on the label is wide enough for the longest labels without wrapping, and `flex-shrink: 0` prevents it from being compressed.

---

## Problem 3: Sidebar appears above the leaderboard on mobile

### What is happening

On the index page, the layout is a flex container with the leaderboard on the left and navigation sidebar on the right. At `max-width: 900px` the CSS collapses this with:

```css
.page-layout { flex-direction: column-reverse; }
```

`column-reverse` puts the sidebar (navigation links) **above** the leaderboard on mobile. A user arriving on the homepage sees the navigation links first and has to scroll down to find the scores.

### Fix

Change one word:

```css
@media (max-width: 900px) {
    .page-layout { flex-direction: column; }  /* was column-reverse */
    .sidebar { width: 100%; }
}
```

The leaderboard appears first, navigation below.

---

## Problem 4: Font sizes at 480px are too large

### What is happening

```css
h1 { font-size: 2rem; }
h2 { font-size: 1.8rem; }
h3 { font-size: 1.5rem; }
```

On a 375px phone, `h2` at 1.8rem is very large and wastes screen space. The page headers dominate the view before the user reaches any content.

### Fix

Covered in Problem 2's fix block above (h1: 1.5rem, h2: 1.2rem, h3: 1rem).

---

## Problem 5: Redundant breakpoint

### What is happening

There is a breakpoint `@media (min-width: 481px) and (max-width: 767px)` that only sets `.content { max-width: 90%; }`. This range is fully covered by the adjacent `768px` breakpoint and adds no value.

### Fix

Remove the entire block:

```css
/* DELETE this block */
@media (min-width: 481px) and (max-width: 767px) {
    .content {
        padding: 15px;
        width: fit-content;
        max-width: 90%;
        margin: 0 auto;
    }
}
```

---

## Problem 6: Duplicate HTML tags in templates

### What is happening

Four templates contain a second `<html><head><title>` block inside `<body>`, left over from editing. While browsers tolerate this, it is invalid HTML and may cause unexpected rendering in some mobile browsers.

For example, in `users.html`:

```html
</head>
<html>       <!-- stray open tag -->
<head>       <!-- stray open tag -->
    <title>All Entrants</title>
</head>
<body>
```

### Fix

In each of `users.html`, `user_template.html`, and `template.html`, remove the stray inner `<html><head><title>…</title></head>` block. The correct title is already set in the outer `<head>`.

---

## Testing

After making changes, run `./build_preds.sh` to regenerate all HTML, then open `docs/index.html` in a browser.

Check these viewports using browser DevTools device emulation:

| Device | Width | Expected |
|--------|-------|----------|
| iPhone SE | 375px | Card layout, leaderboard first, sidebar below |
| iPhone 14 | 390px | Same as above |
| iPad Mini | 768px | Horizontally scrollable table |
| iPad landscape | 1024px | Desktop layout unchanged |
| Desktop | 1440px | Desktop layout unchanged |

Key things to verify on phone widths:
- Leaderboard rows show label + value side by side with no wrapping
- Tapping a row does not cause layout reflow
- The sidebar navigation links appear below the table, not above
- Page title is a reasonable size and does not dominate the viewport
