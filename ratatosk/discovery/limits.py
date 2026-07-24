"""Discovery scout bounds for Ratatosk bootstrap (SAO §17)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("ratatosk.discovery.limits")

DEFAULT_MAX_EXTRACT_TARGETS = 50
MAX_EXTRACT_TARGETS_CEILING = 1000
DEFAULT_MAX_FILE_READS_PER_RUN = 1000
MAX_FILE_READS_PER_RUN_CEILING = 1000

README_SOURCE = "README.md"
SAO_ARCHITECTURE_SOURCE = "docs/architecture/SAO.md"


@dataclass(frozen=True)
class DiscoveryLimits:
    """
    Configurable ceilings for bootstrap file extraction.

    :param max_extract_targets: Planner may request up to this many paths.
    :param max_file_reads_per_run: Hard stop on disk reads per run (SAO scout bound).
    """

    max_extract_targets: int = DEFAULT_MAX_EXTRACT_TARGETS
    max_file_reads_per_run: int = DEFAULT_MAX_FILE_READS_PER_RUN

    @property
    def effective_cap(self) -> int:
        """Minimum of extract target ceiling and file-read hard stop."""
        return min(self.max_extract_targets, self.max_file_reads_per_run)


def clamp_int_limit(
    raw: object,
    *,
    default: int,
    ceiling: int,
    name: str,
) -> int:
    """
    Parse and clamp an integer scout bound.

    :param raw: Raw env/YAML value.
    :param default: Value when unset or invalid.
    :param ceiling: Maximum allowed value.
    :param name: Config key name for logs.
    :return: Clamped integer in ``[1, ceiling]``.
    """
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        logger.info(
            "clamp_int_limit | name=%s branch=invalid_input raw=%r using_default=%s",
            name,
            raw,
            default,
        )
        value = default
    if value < 1:
        logger.warning(
            "clamp_int_limit | name=%s branch=below_min raw=%s using=1",
            name,
            value,
        )
        return 1
    if value > ceiling:
        logger.warning(
            "clamp_int_limit | name=%s branch=above_ceiling requested=%s ceiling=%s",
            name,
            value,
            ceiling,
        )
        return ceiling
    return value


def cap_extract_targets(targets: list[str], limits: DiscoveryLimits) -> list[str]:
    """
    Apply effective scout cap to an ordered target list.

    :param targets: Prioritized relative paths.
    :param limits: Discovery limits from config.
    :return: Target list truncated to ``limits.effective_cap``.
    """
    cap = limits.effective_cap
    capped = targets[:cap]
    dropped = len(targets) - len(capped)
    logger.info(
        "cap_extract_targets | input=%s cap=%s effective_cap=%s "
        "max_extract_targets=%s max_file_reads=%s dropped=%s head=%s",
        len(targets),
        cap,
        limits.effective_cap,
        limits.max_extract_targets,
        limits.max_file_reads_per_run,
        dropped,
        capped[:5],
    )
    return capped


def prioritize_targets(
    tree: list[str],
    targets: list[str],
    limits: DiscoveryLimits | None = None,
) -> list[str]:
    """
    Order extract targets with architecture docs first, then apply cap.

    :param tree: Full repository file tree.
    :param targets: Planner-selected paths (subset of tree).
    :param limits: Optional limits; defaults apply when omitted.
    :return: Ordered, capped target paths.
    """
    effective = limits or DiscoveryLimits()
    ordered: list[str] = []
    for preferred in (README_SOURCE, SAO_ARCHITECTURE_SOURCE):
        if preferred in tree and preferred not in ordered:
            ordered.append(preferred)
    for rel in targets:
        if rel not in ordered:
            ordered.append(rel)
    return cap_extract_targets(ordered, effective)
