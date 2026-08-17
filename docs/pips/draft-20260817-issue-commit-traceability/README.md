# PIP draft: BPE/MIN commit–issue traceability

**Trigger:** W13 depth traversal (#93) — monolithic commit, issue created after code, no per-slice issue comments.

**Playbook:** Edda (id 3)

**Strategy:** ALTER existing Rule and Activity guidance — extend, do not rewrite.

| Entity | ID | Change |
|--------|-----|--------|
| Rule Github Issues | 14 | `always_apply: true` + BPE/MIN traceability section |
| Rule Small Increments | 4 | Active issue #N: commit + comment per slice |
| Activity Plan Feature | 96 | Step 8 hard gate; commit strategy + success criteria |
| Activity Implement Backend | 97 | Step 5 issue comment; required rule |
| Activity Execute (MIN-04) | 181 | Per-slice trail; checkpoint footer Refs #N |

**Local draft bodies:** this directory (`activity-*.md`, `rule-*.md`).

**Lesson learned source:** GitHub #93 retroactive slice split (2026-08-17).
