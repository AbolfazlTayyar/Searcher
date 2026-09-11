# Task 24 — Browser QA pass and ingestion validation fix

## Original prompt

test these using claude in chrome:

1. Confirm the malformed rows really got excluded

   Search keyword: `+1` (or any phone-number-looking string)
   Expect: 0 results. We found rows where a phone number had leaked into the industry field due to CSV column-shift — if any show up, validation isn't catching everything.

2. Case sensitivity on keyword search

   Search: `RECRUITING` (all caps) vs `recruiting` (lowercase)
   Expect: same result count either way. The stored data is lowercase (`recruiting manager`), so this tests whether your ES analyzer is lowercasing/normalizing text search correctly.

3. Job title filter — exact vs partial

   Filter Job Title: `manager` (just the word, not the full title)
   Then filter Job Title: `recruiting manager` (the full title, exact)
   Expect: if the filter field is a keyword type (as designed), `manager` alone should return 0 results and only the exact full string matches. This is the most likely place for a UX surprise — worth deciding if users should be told "type the exact title" or if you actually want partial matching here.

4. Multi-word skill filter

   Filter Skill: `team building` (two words, as it appears in Joseph Holland's profile)
   Expect: matches only if the skill filter does exact keyword match on the whole phrase. Try `team` alone too — should return 0 if keyword-exact, confirming the same behavior as #3.

5. Combined keyword + both filters at once

   Keyword: `engineering`, Job Title: `recruiting manager`, Skill: `training`
   Expect: a result set that's a proper intersection of all three, not just one of them "winning."

6. Genuinely no-match query

   Keyword: something like `zzqxvw`
   Expect: your empty-state UI renders correctly (not a blank screen or an error).

7. Field that's frequently empty

   Filter Job Title: pick a value you can see belongs to a profile with a blank industry
   Expect: profile still returns fine and displays gracefully without an "industry" line breaking layout (check the UI doesn't show undefined/null/empty bullet artifacts for missing fields). verify the results

## Follow-up prompts (same session, after the QA pass reported failures)

> yes, dig into parse.py and ingest.py to fix it

> Keep the stricter anchor set, 60 rows is fine

> update CLAUDE.md's malformed-row percentage to match
