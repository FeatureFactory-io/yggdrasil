# Change Reconciliation — VIEW-BROWSE-1 Inspector Custom Properties

**Feature:** `VIEW-BROWSE-1` · **Issue:** [#100](https://github.com/FeatureFactory-io/yggdrasil/issues/100)
**Activity:** BPE-08 · **Status:** Approved 2026-08-18

## Trigger

Inspector must render persisted element `properties` (e.g. OpenUP Actor on `*-mvp`) with human labels ordered by `Stereotype.property_schema`.

## Reconciliation matrix

| Layer | Drift? | Action |
|-------|--------|--------|
| User journey | Y | Inspector Properties section lists schema + stored custom keys |
| `view-browse-inspector.feature` | Y | AT scenario for custom property rows |
| IA guidelines | N | Existing Properties dl pattern |
| Prior plan (W15) | Y | Inspector full properties beyond field_map |
| As-built | Y | Template loop missed schema ordering / empty values |

## Approved target state

- `get_element_for_inspector` emits `property_rows: [{key, label, value}]` merged from schema + stored JSON.
- Template renders rows with `inspector-property-key-*` / `inspector-property-value-*` testids.
- Empty values display `—`.

## Spec files revised

- `docs/features/act-2-view/view-browse-inspector.feature` — scenario 27b
