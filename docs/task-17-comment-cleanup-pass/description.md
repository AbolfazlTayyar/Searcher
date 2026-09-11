### Task 17 — Comment cleanup pass
**Do:** Audit comments across backend and frontend per the "Comment density" section of CLAUDE.md — remove noise, keep only comments that explain non-obvious why.

**Prompt:**
> Go through every file in backend/src and frontend/src and clean up comments per the "Comment density" section of CLAUDE.md: remove any comment that just restates what the next line of code already says, and keep only comments explaining non-obvious reasoning (e.g. the CSV malformation handling, any tradeoffs). Do not change any logic — comments only.

**Checkpoint:** Spot-check a handful of files — remaining comments all pass the "why, not what" test. No behavior changed (existing tests from Tasks 10 and 15 still pass).
