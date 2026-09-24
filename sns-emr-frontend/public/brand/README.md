# Brand Assets — Locked

**These are the only approved SNS Hospice Solutions logo assets.**
Do not add, replace, regenerate, or "clean up" any file in this directory
without an explicit request from the project owner. This folder has
drifted/reverted before; treat every file here as final until told
otherwise.

## Canonical files

| File | Variant (see `src/components/BrandLogo.tsx`) | Used for |
|---|---|---|
| `sns-logo-dark.svg` | `dark` | Light-theme backgrounds (e.g. login page) |
| `sns-logo-light.svg` | `light` | Dark-theme backgrounds (e.g. navy sidebars/headers) |
| `sns-logo-icon.svg` | `icon` | Compact mark, general use |
| `sns-logo-icon-dark-tile.svg` | `icon-dark-tile` | Compact mark inside the small dark/teal Owner Platform sidebar tile |

`BrandLogo.tsx` is the single source of truth for these paths — every
page must render `<BrandLogo variant="..." />` rather than hardcoding an
`<img src="/brand/...">` path directly.

## Rules

1. Do not swap, resize, recolor, or re-export any of the four files
   above without an explicit request.
2. Do not add new logo files to this directory "just in case" — if a
   new variant is genuinely needed, it must be requested explicitly and
   wired through `BrandLogo.tsx`, not dropped in ad hoc.
3. If a file in this directory ever looks different from what's
   expected, that is a regression — check git history for the file
   before assuming a new version should be created.
