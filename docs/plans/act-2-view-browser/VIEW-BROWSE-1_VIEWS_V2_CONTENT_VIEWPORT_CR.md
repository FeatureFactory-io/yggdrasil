# Change Reconciliation — VIEW-BROWSE-1 Views v2 (Content + Viewport)

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser)
**Activity:** BPE-08 Process Change Request (stub — not started)
**Status:** Draft placeholder
**Date:** 2026-08-18

---

## Purpose

Follow-up CR after **Views v1** ([`VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md)) ships in W14. Extends the **View** payload and UI beyond Filters + Levels.

## In scope (when opened)

| Area | Description |
|------|-------------|
| **Content** | Per-stereotype field bindings on graph nodes/edges and table columns from `Stereotype.property_schema`; content presets (e.g. “Jira Info”, “Current State”) |
| **Viewport** | Graph-only snapshot: `{ zoom, pan, center_element_id }` in View payload |
| **Payload v2** | Extend `BrowseView.payload` without breaking v1 records (nullable viewport/content sections) |

## Out of scope

- Filters, depth, presentation mode (Views v1)
- ChangeSet pipeline for BrowseView (remains ORM user preference)

## Prerequisites

- W14 Views v1 implemented (`graph.BrowseView`, save/load, `browse_view=`, `mode=` migration)
- Stereotype property schema stable enough for binding UI

## Next step

Run BPE-08 reconciliation when planning W15: read journey, features, IA, SAO, mockups; produce full matrix and approved decisions before implementation.
