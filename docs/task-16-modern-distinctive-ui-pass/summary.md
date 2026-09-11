## What was implemented

- **`frontend/src/index.css`** (new): defines the design system as CSS custom properties — a warm cream/ink palette (`--color-bg: #f6f4ee`, `--color-ink`, `--color-muted`, `--color-border`) with a forest-green accent (`--color-accent: #2f6f62`) and a matching error palette, plus a type pairing of Fraunces (serif, for the app title and profile names) and IBM Plex Mono (for body text and all form controls). Also holds every component-level style: the header, search bar, filter fields, results list, and profile cards.
- **`frontend/index.html`**: added `<link>` tags to load Fraunces and IBM Plex Mono from Google Fonts (with `preconnect` hints).
- **`frontend/src/main.tsx`**: imports the new `index.css` so it applies globally.
- **`frontend/src/App.tsx`**: wrapped the page in a `.app` container with a `.app__header` holding the title and a new subtitle ("LinkedIn profile index"); added `className`s to compose the layout — search bar prominent at the top, filters as inline fields directly beneath it (not a sidebar or a generic form), single-column result cards below.
- **`frontend/src/components/SearchBar.tsx`**: added the `search-bar` class only.
- **`frontend/src/components/Filters.tsx`**: added `filters`/`filters__field`/`filters__label`/`filters__input` classes; labels moved into a `<span>` so they can be styled independently of the input.
- **`frontend/src/components/ResultsList.tsx`**: added classes for each render branch (`results__status`, `results__status--error`, `results__count`, `results__list`). Restructured `ProfileCard` markup to use semantic block elements (`profile-card__name`, `__meta`, `__location`, `__summary`, `__skills`) with a left-accent-bordered card; merged the job title and industry into a single `profile-card__meta` line joined by a middot when both are present, instead of two separate inline spans.

## Deviations from the description

None functionally. The `ProfileCard` job-title/industry line was consolidated into one styled row (previously two independent conditional `<span>`s) — this is a presentation-only change to *how* the same two fields are laid out, not to what data is fetched, computed, or which state (loading/error/empty/populated) is shown. No hooks, state, props, or `src/api/` files were touched.

## Files changed

- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/SearchBar.tsx`
- `frontend/src/components/Filters.tsx`
- `frontend/src/components/ResultsList.tsx`
- `frontend/src/index.css` (new)

## Verification

- `npm run build` (`tsc -b && vite build`) passes with no type errors.
- Full manual end-to-end re-run of Task 14's checkpoint, against the real backend + Elasticsearch (Docker Desktop was cold-started for this; the frontend was served as a static Vite build rather than via `npm run dev`, since the sandboxed environment blocked Node from binding any listening socket — confirmed with a raw `node -e http.createServer(...).listen()` test — while Python bound normally):
  - Default load returns the full 283-profile result set.
  - Keyword search ("engineer") narrows to 2 matches after debounce.
  - Job title filter alone ("recruiting manager") narrows to 2 results.
  - Job title + skill combined ("recruiting manager" + "recruiting") applies AND logic correctly (2 results, both fields present on the same profile).
  - A nonsense skill value renders the "No profiles match your search." empty state, not a blank screen.
- Visual comparison: the result reads as a deliberate design (serif display type, mono UI text, warm cream ground, green accent, left-border profile cards, inline filter chips under a prominent search bar) rather than a default Tailwind/shadcn scaffold (no gradient, no rounded-full buttons, no centered card grid).
