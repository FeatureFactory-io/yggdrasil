# Change Reconciliation — VIEW-BROWSE-1 Navigator Defaults

**Issue:** [#102](https://github.com/FeatureFactory-io/yggdrasil/issues/102) · **Status:** Approved 2026-08-18

## Trigger

Default graph View Browser load should show top-level **packages** with their **elements** in the left navigator (Levels=1), matching mockup package buckets.

## Approved target state

- When depth=1 and no scope filters: navigator uses `build_package_navigator_roots` over all model elements.
- Canvas subgraph remains depth=1 BFS scope.
- Package nodes use `package-toggle-{slug}` testids and expand by default.

## Spec files revised

- `docs/features/act-2-view/view-browse-navigator.feature` — scenario 25
