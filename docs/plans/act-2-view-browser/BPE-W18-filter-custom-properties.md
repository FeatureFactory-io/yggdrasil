# BPE-W18 — Filter Custom Properties (#101)

## A — Context Map

| file | note |
|------|------|
| `graph/property_schema_fields.py` | `merge_field_definitions`, `field_paths_from_property_schema` |
| `graph/browse_service.py` | `stereotype_field_catalog` |
| `graph/browse_content.py` | `build_view_field_sections` |
| `web/browse_helpers.py` | `_content_panel_fields` loads catalog |

## D — Tests

| Test | Asserts |
|------|---------|
| `test_filter_panel_lists_custom_property_schema_fields` | Actor schema paths in filter panel |

## E — Log Story Script

| Where | Beat | Must include |
|-------|------|--------------|
| `stereotype_field_catalog` | exit | stereotype_count= |

## F — MCP

Not applicable.
