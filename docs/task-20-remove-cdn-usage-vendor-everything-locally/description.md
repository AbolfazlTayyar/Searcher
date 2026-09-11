# Task 20 — Remove CDN usage, vendor everything locally

**Do:** Audit the frontend (and backend, if applicable) for any CDN-loaded resources — script/link tags pointing at services like unpkg, jsdelivr, cdnjs, Google Fonts, etc. — and replace each with a locally installed/bundled equivalent, so the app has no runtime dependency on external CDNs.

**Prompt:**
> Search the project for any CDN usage — `<script>`/`<link>` tags in `index.html` or elsewhere pointing to external CDNs (unpkg, jsdelivr, cdnjs, Google Fonts, etc.), or any library loaded via CDN instead of a package import. Replace each with a locally installed npm package (or self-hosted asset, e.g. downloaded font files served from `public/`), bundled through Vite like the rest of the app. Remove the CDN references entirely. Don't change any functionality — this is a delivery-mechanism change only.

**Checkpoint:** Disconnect from the internet (or block outbound requests) and run the app — it loads and functions identically, with no failed network requests to any external CDN domain in the browser's network tab.
