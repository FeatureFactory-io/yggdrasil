"""Unit tests for ratatosk discovery cleanup helpers."""

from __future__ import annotations

from ratatosk.discovery.runner import (
    _cleanup,
    _humanize_element_name,
    _normalize_package_slug,
    _parse_readme_architecture_table,
    _prioritize_targets,
    _reconcile,
    _reconcile_incremental,
)


def test_normalize_package_slug_maps_container_to_technology() -> None:
    """File-path packages map to C4 technology for containers."""
    slugs = {"context", "technology", "application", "code"}
    assert _normalize_package_slug("src/payment_api", "container", slugs) == "technology"


def test_normalize_package_slug_maps_component_to_application() -> None:
    """File-path packages map to C4 application for components."""
    slugs = {"context", "technology", "application", "code"}
    assert _normalize_package_slug("src.billing_worker.worker", "component", slugs) == "application"


def test_humanize_element_name_splits_camel_case() -> None:
    """Class-style names become human-readable element titles."""
    assert _humanize_element_name("BillingWorker") == "Billing Worker"
    assert _humanize_element_name("Payment API") == "Payment API"


def test_parse_readme_architecture_table_sample_webapp() -> None:
    """README path map table yields manifest element names."""
    text = """
| Element | Stereotype | Path |
|---------|------------|------|
| Payment API | Container | `src/payment_api/app.py` |
| Order Service | Container | `src/order_service/app.py` |
| Order Domain | Component | `src/order_domain/service.py` |
| Billing Worker | Component | `src/billing_worker/worker.py` |
"""
    items = _parse_readme_architecture_table(text)
    names = {item["name"] for item in items}
    assert names == {"Payment API", "Order Service", "Order Domain", "Billing Worker"}


def test_cleanup_accepts_llm_candidates_with_path_packages() -> None:
    """Real LLM path packages survive cleanup via stereotype defaults."""
    raw = [
        {
            "name": "Payment API",
            "stereotype": "container",
            "package": "src/payment_api",
            "confidence": 0.95,
        },
        {
            "name": "BillingWorker",
            "stereotype": "component",
            "package": "src.billing_worker.worker",
            "confidence": 0.9,
        },
        {
            "name": "FastAPI",
            "stereotype": "external",
            "package": "fastapi",
            "confidence": 0.99,
        },
    ]
    element_slugs = {"container", "component", "system", "person", "external"}
    package_slugs = {"context", "technology", "application", "code"}
    accepted = _cleanup(raw, element_slugs, package_slugs)
    names = {item["name"] for item in accepted}
    assert names == {"Payment API", "Billing Worker"}
    assert all(item["package"] in package_slugs for item in accepted)


def test_prioritize_targets_puts_readme_first() -> None:
    """README.md is always extracted before per-file targets."""
    tree = ["src/a.py", "README.md", "src/b.py"]
    targets = ["src/a.py", "src/b.py"]
    assert _prioritize_targets(tree, targets)[0] == "README.md"


def test_reconcile_bootstrap_rescan_deletes_all_existing() -> None:
    """Bootstrap re-scan wipes every existing slug and re-adds candidates."""
    by_slug = {
        "payment-api": {"id": 1, "name": "Payment API", "slug": "payment-api"},
        "legacy-batch": {"id": 2, "name": "LegacyBatch", "slug": "legacy-batch"},
    }
    candidates = [{"name": "Payment API", "stereotype": "container", "confidence": 0.9}]
    buckets = _reconcile(candidates, by_slug, bootstrap_rescan=True)
    assert len(buckets.to_delete) == 2
    assert buckets.to_delete[0]["confidence"] == 1.0
    assert len(buckets.to_add) == 1
    assert buckets.unchanged == []
    assert buckets.to_update == []


def test_all_bucket_operations_bootstrap_puts_deletes_first() -> None:
    """Bootstrap handoff applies wipe before adds so get_or_create gets fresh slugs."""
    from ratatosk.discovery.runner import DeltaBuckets, _all_bucket_operations

    buckets = DeltaBuckets(
        to_add=[
            {"name": "Auth", "stereotype": "component", "package": "application", "confidence": 0.9}
        ],
        to_delete=[
            {"name": "Legacy", "element_id": 99, "confidence": 1.0},
        ],
    )
    ops = _all_bucket_operations(buckets, bootstrap_rescan=True)
    assert ops[0]["op_type"] == "delete_element"
    assert ops[1]["op_type"] == "add_element"
    assert ops[0]["confidence"] == 1.0


def test_reconcile_incremental_deletes_unmatched_slugs() -> None:
    """Update mode deletes existing elements missing from new candidates."""
    by_slug = {
        "payment-api": {"id": 1, "name": "Payment API", "slug": "payment-api"},
        "legacy-batch": {"id": 2, "name": "LegacyBatch", "slug": "legacy-batch"},
    }
    candidates = [{"name": "Payment API", "stereotype": "container", "confidence": 0.9}]
    buckets = _reconcile_incremental(candidates, by_slug)
    assert len(buckets.unchanged) == 1
    assert len(buckets.to_delete) == 1
    assert buckets.to_delete[0]["name"] == "LegacyBatch"
