# Task 25 — Case-insensitive filter search fix

**Do:** Verify keyword search (`q`) and both filters (`job_title`, `skill`) behave the same regardless of input casing. `q` already worked (standard analyzer lowercases both sides); `job_title`/`skill` filters didn't (`term` queries against unanalyzed `.keyword` sub-fields require exact-case matches). Fix the filters in `search_service.py` and add regression tests.

**Prompt:**
> test the search based on case sensibity or insensivity ity should work both ways i think
