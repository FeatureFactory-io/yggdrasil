"""Shared metamodel guidance text for Ratatosk and Munin LLM prompts."""

from __future__ import annotations

import json
from typing import Any


def stereotype_guidance_block(st: Any) -> list[str]:
    """
    Format one Stereotype as LLM guidance lines.

    :param st: Stereotype model or dict with slug, name, description, etc.
    :return: Markdown lines for prompt injection.
    """
    if isinstance(st, dict):
        slug = str(st.get("slug") or "")
        name = str(st.get("name") or slug)
        desc = str(st.get("description") or "").strip() or "(no description)"
        schema = json.dumps(st.get("property_schema") or {}, sort_keys=True)
        rules = st.get("allowed_edge_rules") or []
    else:
        slug = str(getattr(st, "slug", "") or "")
        name = str(getattr(st, "name", "") or slug)
        desc = str(getattr(st, "description", "") or "").strip() or "(no description)"
        schema = json.dumps(getattr(st, "property_schema", None) or {}, sort_keys=True)
        rules = getattr(st, "allowed_edge_rules", None) or []
    rules_txt = ", ".join(str(r) for r in rules) if rules else "(none)"
    return [
        f"### `{slug}` — {name}",
        f"- When to use: {desc}",
        f"- property_schema: {schema}",
        f"- allowed_edge_rules (outbound): [{rules_txt}]",
    ]


def build_metamodel_guidance(metamodel: Any) -> str:
    """
    Build detailed Metamodel instruction text from Django Metamodel ORM object.

    :param metamodel: ``graph.Metamodel`` instance.
    :return: Markdown guidance block.
    """
    lines: list[str] = [
        f"# Metamodel: {metamodel.name} (slug={metamodel.slug})",
        (metamodel.description or "").strip() or "(no metamodel description)",
        "",
        "## Element stereotypes (use `stereotype` = slug)",
    ]
    for st in metamodel.stereotypes.filter(is_edge=False).order_by("slug"):
        lines.extend(stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Relationship stereotypes (use for edges only)")
    for st in metamodel.stereotypes.filter(is_edge=True).order_by("slug"):
        lines.extend(stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Packages (use `package` = slug)")
    for pkg in metamodel.packages.order_by("slug"):
        desc = (pkg.description or "").strip() or "(no description)"
        lines.append(f"- `{pkg.slug}` — {pkg.name}: {desc}")
    lines.append("")
    lines.append(
        "Rules: every candidate MUST use an element stereotype slug and package "
        "slug from the lists above. Do not invent slugs."
    )
    return "\n".join(lines)


def build_metamodel_guidance_from_stereotypes(
    items: list[dict],
    packages: list[dict] | None = None,
    *,
    metamodel_slug: str = "c4",
    metamodel_name: str = "C4",
) -> str:
    """
    Build metamodel guidance from MCP ``list_stereotypes`` / ``list_packages`` payloads.

    :param items: Stereotype dicts from MCP.
    :param packages: Optional package dicts.
    :param metamodel_slug: Metamodel slug label.
    :param metamodel_name: Display name.
    :return: Markdown guidance block.
    """
    element_slugs: set[str] = set()
    lines: list[str] = [
        f"# Metamodel: {metamodel_name} (slug={metamodel_slug})",
        "",
        "## Element stereotypes (use `stereotype` = slug)",
    ]
    for st in items:
        if st.get("is_edge"):
            continue
        slug = str(st.get("slug") or "")
        element_slugs.add(slug)
        lines.extend(stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Relationship stereotypes (use for edges only)")
    for st in items:
        if not st.get("is_edge"):
            continue
        lines.extend(stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Packages (use `package` = slug)")
    package_slugs: set[str] = set()
    for pkg in packages or []:
        slug = str(pkg.get("slug") or "")
        package_slugs.add(slug)
        desc = str(pkg.get("description") or "").strip() or "(no description)"
        lines.append(f"- `{slug}` — {pkg.get('name', slug)}: {desc}")
    if not package_slugs:
        package_slugs = {"context", "technology", "application", "code"}
        for slug in sorted(package_slugs):
            lines.append(f"- `{slug}`")
    lines.append("")
    lines.append(
        "Rules: every candidate MUST use an element stereotype slug and package "
        "slug from the lists above. Do not invent slugs."
    )
    return "\n".join(lines)
