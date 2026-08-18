# BPE-W19 — Navigator Default Package Tree (#102)

## A — Context Map

| file | note |
|------|------|
| `web/browse_helpers.py` | `_should_use_package_navigator`, `build_package_navigator_roots` |
| `graph/browse_service.py` | `list_all_element_summaries` |
| `web/templates/.../navigator_tree_node.html` | Package folder icon + testids |

## D — Tests

| Test | Asserts |
|------|---------|
| `test_default_navigator_shows_package_buckets` | Package toggles + elements at default load |

## E — Log Story Script

| Where | Beat | Must include |
|-------|------|--------------|
| `build_package_navigator_roots` | exit | package_count= |

## F — MCP

Not applicable.
