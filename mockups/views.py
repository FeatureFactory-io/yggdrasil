import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)

# ─── Confidence banding — IA_guidelines.md §15.6 ─────────────────────────────
# Bands: >=0.85 high, 0.60-0.84 medium, 0.40-0.59 low, <0.40 vlow.
# Each mock element/relationship gets `conf_pct` (int, for CSS width) and
# `conf_band` (str, for the var(--yrg-conf-{band}) fill color) so templates
# never need to compute a percentage or pick a color themselves.

CONFIDENCE_BAND_THRESHOLDS = (
    (0.85, "high"),
    (0.60, "medium"),
    (0.40, "low"),
)


def confidence_band(confidence: float) -> str:
    """Map a 0.0-1.0 confidence score to its §15.6 semantic band.

    :param confidence: Confidence score in the closed interval [0.0, 1.0].
    :return: One of "high", "medium", "low", "vlow".
    """
    for threshold, band in CONFIDENCE_BAND_THRESHOLDS:
        if confidence >= threshold:
            return band
    return "vlow"


def annotate_confidence(items: list[dict]) -> list[dict]:
    """Attach `conf_pct` and `conf_band` to each dict's `confidence` value.

    :param items: Mock element or relationship dicts, each with a
        `confidence` key holding a 0.0-1.0 float.
    :return: The same list, mutated in place, for convenient chaining.
    """
    for item in items:
        item["conf_pct"] = round(item["confidence"] * 100)
        item["conf_band"] = confidence_band(item["confidence"])
    return items


# ─── Mock data ───────────────────────────────────────────────────────────────

MOCK_ELEMENTS = [
    {
        "id": 1,
        "name": "Payment API",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "payments-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.92,
        "properties": {"version": "2.3.1", "language": "Python", "framework": "FastAPI"},
        "relationships_in": 4,
        "relationships_out": 6,
        "last_verified": "2026-07-10",
    },
    {
        "id": 2,
        "name": "Notification Service",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "platform-team",
        "health": "yellow",
        "source": "human",
        "confidence": 1.0,
        "properties": {"version": "1.0.0", "language": "Python", "framework": "Celery"},
        "relationships_in": 2,
        "relationships_out": 3,
        "last_verified": "2026-07-14",
    },
    {
        "id": 3,
        "name": "Order Domain",
        "stereotype": "Component",
        "package": "Application",
        "owner": "fulfillment-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.87,
        "properties": {"version": "3.1.0", "language": "Python"},
        "relationships_in": 8,
        "relationships_out": 4,
        "last_verified": "2026-07-10",
    },
    {
        "id": 4,
        "name": "Fulfillment Worker",
        "stereotype": "Component",
        "package": "Application",
        "owner": "fulfillment-team",
        "health": "red",
        "source": "ratatosk",
        "confidence": 0.71,
        "properties": {"version": "2.0.0", "language": "Python"},
        "relationships_in": 2,
        "relationships_out": 5,
        "last_verified": "2026-07-10",
    },
    {
        "id": 5,
        "name": "PostgreSQL",
        "stereotype": "System",
        "package": "Technology",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.99,
        "properties": {"version": "15.2"},
        "relationships_in": 7,
        "relationships_out": 0,
        "last_verified": "2026-07-10",
    },
    {
        "id": 6,
        "name": "Mobile App",
        "stereotype": "System",
        "package": "Context",
        "owner": "mobile-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"platform": "iOS + Android"},
        "relationships_in": 0,
        "relationships_out": 3,
        "last_verified": "2026-07-10",
    },
]

MOCK_RELATIONSHIPS = [
    {
        "id": 1,
        "from_element": "Mobile App",
        "from_id": 6,
        "edge_stereotype": "calls",
        "to_element": "Payment API",
        "to_id": 1,
        "confidence": 0.95,
        "source": "ratatosk",
        "properties": {"protocol": "HTTPS", "async": False},
    },
    {
        "id": 2,
        "from_element": "Payment API",
        "from_id": 1,
        "edge_stereotype": "depends_on",
        "to_element": "PostgreSQL",
        "to_id": 5,
        "confidence": 0.99,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 3,
        "from_element": "Payment API",
        "from_id": 1,
        "edge_stereotype": "calls",
        "to_element": "Notification Service",
        "to_id": 2,
        "confidence": 0.92,
        "source": "ratatosk",
        "properties": {"protocol": "AMQP", "async": True},
    },
    {
        "id": 4,
        "from_element": "Order Domain",
        "from_id": 3,
        "edge_stereotype": "depends_on",
        "to_element": "Payment API",
        "to_id": 1,
        "confidence": 0.87,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 5,
        "from_element": "Fulfillment Worker",
        "from_id": 4,
        "edge_stereotype": "reads_from",
        "to_element": "PostgreSQL",
        "to_id": 5,
        "confidence": 0.71,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 6,
        "from_element": "Order Domain",
        "from_id": 3,
        "edge_stereotype": "serves",
        "to_element": "Fulfillment Worker",
        "to_id": 4,
        "confidence": 0.85,
        "source": "ratatosk",
        "properties": {},
    },
]

annotate_confidence(MOCK_ELEMENTS)
annotate_confidence(MOCK_RELATIONSHIPS)

MOCK_CHANGESETS = [
    {
        "id": 1,
        "run_id": "run-003",
        "source": "ratatosk",
        "submitted": "2026-07-14 09:12",
        "operations": 6,
        "mode": "manual",
        "status": "pending",
        "summary": (
            "I analysed 3 services, 12 modules, and 4 external dependencies. "
            "The model now contains 16 elements and 24 relationships across the Technology package. "
            "3 operations are awaiting your review — mainly around module-to-service ownership."
        ),
        "ops": [
            {
                "id": 1,
                "op": "Add Element",
                "detail": '"Notification Service" → Container / Technology',
                "confidence": 0.92,
                "status": "pending",
            },
            {
                "id": 2,
                "op": "Link Element",
                "detail": "Notification Service →depends_on→ Payment API",
                "confidence": 0.91,
                "status": "pending",
            },
            {
                "id": 3,
                "op": "Add to Diagram",
                "detail": "Notification Service → Container Diagram C1",
                "confidence": 0.65,
                "status": "pending",
            },
            {
                "id": 4,
                "op": "Update Element",
                "detail": "Order Domain: owner → fulfillment-team (was: payments-team)",
                "confidence": 0.88,
                "status": "pending",
            },
            {
                "id": 5,
                "op": "Delete Element",
                "detail": "LegacyBatch (removed module — 0 active relationships)",
                "confidence": 0.95,
                "status": "pending",
            },
            {
                "id": 6,
                "op": "Add Relationship",
                "detail": "Mobile App →calls→ Notification Service",
                "confidence": 0.78,
                "status": "pending",
            },
        ],
    },
    {
        "id": 2,
        "run_id": "run-002",
        "source": "human",
        "submitted": "2026-07-13 14:45",
        "operations": 2,
        "mode": "auto",
        "status": "applied",
        "summary": "Manual element creation: Fulfillment Worker component added with 2 outbound relationships.",
        "ops": [
            {
                "id": 1,
                "op": "Add Element",
                "detail": '"Fulfillment Worker" → Component / Application',
                "confidence": 1.0,
                "status": "accepted",
            },
            {
                "id": 2,
                "op": "Add Relationship",
                "detail": "Fulfillment Worker →reads_from→ PostgreSQL",
                "confidence": 1.0,
                "status": "accepted",
            },
        ],
    },
    {
        "id": 3,
        "run_id": "run-001",
        "source": "ratatosk",
        "submitted": "2026-07-10 08:00",
        "operations": 21,
        "mode": "auto",
        "status": "applied",
        "summary": "Initial bootstrap: 16 elements and 18 relationships added across Technology and Application packages.",
        "ops": [],
    },
]

MOCK_RUNS = [
    {
        "id": 3,
        "trigger": "ratatosk bootstrap ./repo --model Yggdrasil",
        "status": "complete",
        "started": "2026-07-14 09:10",
        "duration": "2m 14s",
        "candidates": 22,
        "operations": 6,
        "changeset_id": 1,
    },
    {
        "id": 2,
        "trigger": "manual GUI create",
        "status": "complete",
        "started": "2026-07-13 14:44",
        "duration": "0m 08s",
        "candidates": 2,
        "operations": 2,
        "changeset_id": 2,
    },
    {
        "id": 1,
        "trigger": "ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4",
        "status": "complete",
        "started": "2026-07-10 08:00",
        "duration": "4m 31s",
        "candidates": 48,
        "operations": 21,
        "changeset_id": 3,
    },
]

MOCK_TOKENS = [
    {
        "id": 1,
        "name": "laptop-ratatosk",
        "created": "2026-06-01",
        "last_used": "2026-07-14",
        "scope": "read-write",
    },
    {
        "id": 2,
        "name": "cursor-mcp",
        "created": "2026-06-15",
        "last_used": "2026-07-13",
        "scope": "read-only",
    },
]

# ─── Form option lists (EDIT screens pre-select the current value) ──────────

ELEMENT_STEREOTYPE_OPTIONS = ["System", "Container", "Component", "Person", "External"]
ELEMENT_PACKAGE_OPTIONS = ["Context", "Technology", "Application", "Code"]
RELATIONSHIP_EDGE_STEREOTYPE_OPTIONS = ["calls", "depends_on", "serves", "reads_from", "contains"]

# ─── Views ───────────────────────────────────────────────────────────────────


def auth_login(request):
    """AUTH-LOGIN-1: Login form."""
    logger.info("Mockup: auth_login | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/auth/login.html", {})


def auth_token(request):
    """AUTH-TOKEN-1: API token management."""
    logger.info("Mockup: auth_token | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/auth/token.html", {"tokens": MOCK_TOKENS})


def munin_briefing(request):
    """MUNIN-BRIEFING-1: Post-run architectural briefing."""
    logger.info("Mockup: munin_briefing | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/munin/briefing.html",
        {
            "run": MOCK_RUNS[0],
            "changeset": MOCK_CHANGESETS[0],
            "auto_applied": 37,
            "queued": 3,
            "skipped": 2,
        },
    )


def view_browse(request):
    """VIEW-BROWSE-1: View Browser."""
    logger.info("Mockup: view_browse | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/view/browse.html", {"elements": MOCK_ELEMENTS})


def view_export(request):
    """EXPORT-BRIEFING-1: Export modal."""
    logger.info("Mockup: view_export | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/view/export.html",
        {
            "element_count": len(MOCK_ELEMENTS),
            "relationship_count": len(MOCK_RELATIONSHIPS),
        },
    )


def view_history(request):
    """VIEW-HISTORY-1: Model history / diff."""
    logger.info("Mockup: view_history | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/view/history.html", {"changesets": MOCK_CHANGESETS})


def element_list(request):
    """ELEMENT-LIST+FIND-1: Elements list & search."""
    logger.info("Mockup: element_list | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/element/list.html",
        {
            "elements": MOCK_ELEMENTS,
            "element_count": len(MOCK_ELEMENTS),
        },
    )


def element_view(request, id):
    """ELEMENT-VIEW_ELEMENT-1: Element detail."""
    logger.info(
        "Mockup: element_view | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    element = next((e for e in MOCK_ELEMENTS if e["id"] == id), MOCK_ELEMENTS[0])
    rels = [r for r in MOCK_RELATIONSHIPS if r["from_id"] == id or r["to_id"] == id]
    return render(request, "mockups/element/view.html", {"element": element, "relationships": rels})


def element_create(request):
    """ELEMENT-CREATE_ELEMENT-1: Create element form."""
    logger.info("Mockup: element_create | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/element/create.html", {"elements": MOCK_ELEMENTS})


def element_edit(request, id):
    """ELEMENT-EDIT_ELEMENT-1: Edit element form."""
    logger.info(
        "Mockup: element_edit | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    element = next((e for e in MOCK_ELEMENTS if e["id"] == id), MOCK_ELEMENTS[0])
    return render(
        request,
        "mockups/element/edit.html",
        {
            "element": element,
            "elements": MOCK_ELEMENTS,
            "stereotype_options": ELEMENT_STEREOTYPE_OPTIONS,
            "package_options": ELEMENT_PACKAGE_OPTIONS,
        },
    )


def relationship_list(request):
    """RELATIONSHIP-LIST+FIND-1: Relationships list."""
    logger.info(
        "Mockup: relationship_list | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(
        request,
        "mockups/relationship/list.html",
        {
            "relationships": MOCK_RELATIONSHIPS,
            "relationship_count": len(MOCK_RELATIONSHIPS),
        },
    )


def relationship_view(request, id):
    """RELATIONSHIP-VIEW_RELATIONSHIP-1: Relationship detail."""
    logger.info(
        "Mockup: relationship_view | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    rel = next((r for r in MOCK_RELATIONSHIPS if r["id"] == id), MOCK_RELATIONSHIPS[0])
    return render(request, "mockups/relationship/view.html", {"relationship": rel})


def relationship_create(request):
    """RELATIONSHIP-CREATE_RELATIONSHIP-1: Create relationship form."""
    logger.info(
        "Mockup: relationship_create | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(request, "mockups/relationship/create.html", {"elements": MOCK_ELEMENTS})


def relationship_edit(request, id):
    """RELATIONSHIP-EDIT_RELATIONSHIP-1: Edit relationship form."""
    logger.info(
        "Mockup: relationship_edit | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    rel = next((r for r in MOCK_RELATIONSHIPS if r["id"] == id), MOCK_RELATIONSHIPS[0])
    return render(
        request,
        "mockups/relationship/edit.html",
        {
            "relationship": rel,
            "elements": MOCK_ELEMENTS,
            "edge_stereotype_options": RELATIONSHIP_EDGE_STEREOTYPE_OPTIONS,
        },
    )


def changeset_list(request):
    """CHANGESET-LIST+FIND-1: ChangeSet queue."""
    logger.info("Mockup: changeset_list | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/changeset/list.html",
        {
            "changesets": MOCK_CHANGESETS,
            "changeset_count": len(MOCK_CHANGESETS),
        },
    )


def changeset_view(request, id):
    """CHANGESET-VIEW_CHANGESET-1: ChangeSet review."""
    logger.info(
        "Mockup: changeset_view | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    cs = next((c for c in MOCK_CHANGESETS if c["id"] == id), MOCK_CHANGESETS[0])
    return render(request, "mockups/changeset/view.html", {"changeset": cs})


def ratatosk_run_list(request):
    """RATATOSK_RUN-LIST+FIND-1: Run list."""
    logger.info(
        "Mockup: ratatosk_run_list | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(
        request,
        "mockups/ratatosk_run/list.html",
        {
            "runs": MOCK_RUNS,
            "run_count": len(MOCK_RUNS),
        },
    )


def ratatosk_run_view(request, id):
    """RATATOSK_RUN-VIEW_RATATOSK_RUN-1: Run detail."""
    logger.info(
        "Mockup: ratatosk_run_view | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    run = next((r for r in MOCK_RUNS if r["id"] == id), MOCK_RUNS[0])
    cs = next((c for c in MOCK_CHANGESETS if c.get("id") == run.get("changeset_id")), None)
    return render(request, "mockups/ratatosk_run/view.html", {"run": run, "changeset": cs})
