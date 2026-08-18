# BPE-W17 — Inspector Custom Properties (#100)

## A — Context Map

| file | lines | note |
|------|-------|------|
| `graph/property_schema_fields.py` | all | Schema → inspector rows helper |
| `graph/browse_service.py` | `get_element_for_inspector` | Attach `property_rows` |
| `web/templates/.../inspector_element.html` | Properties dl | Render rows + testids |
| `web/views.py` | `ViewBrowseInspectorElementView` | HTMX partial entry |
| `web/tests/test_view_browse.py` | inspector test | Regression |

## B — Do-Not-Do

- Do not bypass ChangeSet for writes.
- Do not log raw property secrets.

## C — SAO sections

§4 JSONB properties · §1 graph bounded context

## D — Tests

| Test | Asserts |
|------|---------|
| `test_property_schema_fields.py` | Schema merge + row ordering |
| `test_inspector_element_partial_renders_properties` | Custom keys in partial HTML |
| `VIEW-BROWSE-1-27b` (AT) | Inspector partial shows custom property |

## E — Log Story Script

| Where | Beat | Must include |
|-------|------|--------------|
| `get_element_for_inspector` | exit | property_rows= |

## F — MCP Tools

Not applicable.
