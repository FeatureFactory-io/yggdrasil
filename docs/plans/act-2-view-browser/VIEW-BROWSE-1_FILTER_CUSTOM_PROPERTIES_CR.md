# Change Reconciliation — VIEW-BROWSE-1 Filter Custom Properties

**Issue:** [#101](https://github.com/FeatureFactory-io/yggdrasil/issues/101) · **Status:** Approved 2026-08-18

## Trigger

Filters panel field checklists must include all `property_schema` paths for selected stereotypes, not only static `STEREOTYPE_FIELD_SCHEMA` entries.

## Approved target state

- `stereotype_field_catalog(model_slug)` merges static + dynamic fields per metamodel stereotype.
- `build_view_field_sections` uses catalog when building checklists.
- `field_map` persistence unchanged.

## Spec files revised

- `docs/features/act-2-view/view-browse-content.feature` — scenario 81
