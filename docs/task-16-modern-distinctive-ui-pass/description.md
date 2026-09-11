**Do:** Replace default/scaffold styling with an intentional design — real color palette, type scale, and a layout suited to a search tool — per the "UI/design conventions" section of CLAUDE.md. No functional changes.

**Prompt:**
> Redesign the frontend's visual styling per the "UI/design conventions" section of CLAUDE.md: pick a deliberate color palette and typography, and a layout suited specifically to a search tool (not a generic centered card grid or default Tailwind/shadcn look). This is a styling pass only — don't change any component logic, data flow, or the API layer. All existing functionality (search, filters, loading/error/empty states) must keep working exactly as before.

**Checkpoint:** Visually compare against an unstyled scaffold — the app should look like a deliberate design choice, not a default template. Re-run the full manual flow from Task 14's checkpoint — nothing functional broke.
