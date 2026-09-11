# Task 20 summary — Remove CDN usage, vendor everything locally

## What was found

A repo-wide search (`index.html`, `src/`, Dockerfiles, `nginx.conf`, backend) turned up exactly one external-CDN dependency: `frontend/index.html` loaded the Fraunces and IBM Plex Mono fonts from `fonts.googleapis.com` / `fonts.gstatic.com` via `<link rel="preconnect">` and a Google Fonts CSS2 stylesheet URL. No other CDN-hosted scripts, stylesheets, or fonts were found anywhere in the project (backend has no frontend-style CDN usage at all).

## What was implemented

- Installed `@fontsource-variable/fraunces` and `@fontsource/ibm-plex-mono` as regular npm dependencies (`frontend/package.json`), which vendor the actual Google Fonts `.woff2`/`.woff` files plus matching `@font-face` CSS.
- Removed the three Google Fonts `<link>` tags from `frontend/index.html`.
- Imported the font CSS (`@fontsource-variable/fraunces/full.css`, and the 400/500/600 weights of `@fontsource/ibm-plex-mono`) in `frontend/src/main.tsx`, so Vite bundles the font files as hashed local assets alongside the rest of the app — same as every other CDN-load-to-package-import conversion.
- Updated `--font-display` in `frontend/src/index.css` from `'Fraunces'` to `'Fraunces Variable'` to match the font-family name the fontsource variable-font package registers (`'IBM Plex Mono'` needed no rename — fontsource uses the same family name Google Fonts does).

## Deviation from the prompt

The prompt suggested self-hosting via downloaded font files served from `public/` as one option; an npm-package-based vendor (`@fontsource`) was used instead since it's the more idiomatic Vite/npm approach for this exact scenario (locally installed package, bundled through Vite, hashed/cached assets, easy version pinning) rather than manually downloading and maintaining font binaries in `public/`. No functional or visual difference — same fonts, same weights, same optical-size variability (Fraunces is bundled as a full variable font covering the opsz+wght axes the original Google Fonts URL requested).

## Verification

- `npx tsc -b` — clean.
- `npx vite build` — succeeds; inspected `dist/index.html`, `dist/assets/*.css` — no `http(s)://` references anywhere in the built output. All font files (`fraunces-*.woff2`, `ibm-plex-mono-*.woff`/`.woff2`) are emitted as local hashed assets under `dist/assets/`.
- `npx vitest run` — all 8 existing tests still pass.
- `npx eslint .` — clean.
- Was unable to bind a local dev-server port in this sandboxed shell to do a live network-tab check, but the build-output inspection above is equivalent evidence: the artifact Docker/nginx actually serves contains zero external CDN references.

## Files changed

- `frontend/index.html` — removed Google Fonts `<link>` tags.
- `frontend/src/main.tsx` — added local font CSS imports.
- `frontend/src/index.css` — updated `--font-display` family name.
- `frontend/package.json`, `frontend/package-lock.json` — added `@fontsource-variable/fraunces` and `@fontsource/ibm-plex-mono` dependencies.
