# Activity: Create Mockups

**Activity ID**: 40
**Order**: 6
**Phase**: Inception
**Dependencies**: Predecessor: Activity 39 (Write Feature Files)

## Description

Create Mockups

## Guidance

# Create Mockups (Prototyped Screens)

## Objective

Build functional prototypes with mocked data to validate UX before full implementation.

## Layout

Mockups live in a dedicated `mockups/` package at the repo root — separate from production code.

```
mockups/
  __init__.py          # package marker; demo/design reference only
  urls.py              # URL patterns for all mockup screens (canonical inventory)
  views.py             # views with hardcoded MOCK_* data fixtures
src/yggdrasil/web/templates/mockups/
  base.html            # shared shell — banner, navbar, global mockup nav
  {entity}/
    {operation}.html   # e.g. templates/mockups/diagram/list.html
src/yggdrasil/web/static/js/
  mockup-{feature}.js  # optional client-side interactivity (sessionStorage, etc.)
```

`mockups` is **not** in `INSTALLED_APPS` — it is a plain module included from `yggdrasil/urls.py`.

---

## Gating — DEBUG only

Mockup routes are mounted only when `settings.DEBUG` is `True`.
In all other environments (test, production) they return 404.

```python
# src/yggdrasil/urls.py
if settings.DEBUG:
    urlpatterns.append(path("mockups/", include("mockups.urls")))
```

This means mockups are automatically available with `runserver` (dev settings set `DEBUG=True`) and automatically disabled under pytest and production.

---

## Mockup chrome (required on every screen)

Every mockup screen **must** extend `mockups/base.html`. Do **not** duplicate mockup chrome inside individual templates.

Two elements are always visible (except where a full-bleed screen explicitly hides the footer — see below):

### 1. Top banner — `.hg-mockup-banner`

Fixed at the top of the viewport. Signals that the screen is design reference only.

```html
<div class="hg-mockup-banner">
  Mockup · design reference only · not connected to live data
</div>
```

- Lives in `templates/mockups/base.html` only.
- Never remove or hide in individual mockup templates.
- Navbar is offset below it (`top: 24px`).

### 2. Global screen inventory — `.hg-mockup-nav`

Footer bar listing **all** registered mockup screens. This is the canonical cross-link index for designers, reviewers, and agents jumping between prototypes.

```html
<div class="container-fluid px-4 pb-4 mt-3">
  <div class="hg-mockup-nav" data-testid="mockup-screen-nav">
    <strong>Mockup screens:</strong>
    <!-- one link per registered mockups/urls.py route -->
    …
    {% block mockup_nav_extra %}{% endblock %}
  </div>
</div>
```

**Rules:**

| Rule | Detail |
|---|---|
| **Single source** | Maintain links in `base.html` only — **never** add a second per-page “Mockup screens:” block. |
| **Keep in sync** | When you add a route in `mockups/urls.py`, add a link to `base.html` in the same change. |
| **Page-specific hints** | Use `{% block mockup_nav_extra %}` for optional suffix text (e.g. sessionStorage reset key on interactive mockups). Do not fork the nav. |
| **`data-testid`** | Root footer nav: `mockup-screen-nav`. |

**Current inventory** (maintain this list in `base.html` as routes grow):

| Link label | URL name | Screen ID (typical) |
|---|---|---|
| Login | `mockup_auth_login` | AUTH-LOGIN-1 |
| Tokens | `mockup_auth_token` | AUTH-TOKEN-1 |
| Briefing | `mockup_munin_briefing` | MUNIN-BRIEFING-1 |
| View Browser | `mockup_view_browse` | VIEW-BROWSE-1 |
| Export | `mockup_view_export` | EXPORT-BRIEFING-1 |
| History | `mockup_view_history` | VIEW-HISTORY-1 |
| Elements | `mockup_element_list` | ELEMENT-LIST+FIND-1 |
| Create Element | `mockup_element_create` | ELEMENT-CREATE_ELEMENT-1 |
| Relationships | `mockup_relationship_list` | RELATIONSHIP-LIST+FIND-1 |
| Diagrams | `mockup_diagram_list` | DIAGRAM-LIST+FIND-1 |
| Create Diagram | `mockup_diagram_editor_create` | DIAGRAM-CREATE_DIAGRAM-1 |
| Edit Diagram #1 | `mockup_diagram_editor` id=1 | DIAGRAM-EDITOR-1 |
| ChangeSets | `mockup_changeset_list` | CHANGESET-LIST+FIND-1 |
| ChangeSet review | `mockup_changeset_view` id=1 | CHANGESET-VIEW_CHANGESET-1 |
| Runs | `mockup_ratatosk_run_list` | RATATOSK_RUN-LIST+FIND-1 |

Representative **detail/edit** routes (element view, relationship view, run view, etc.) are reachable from list rows — they do not need footer links unless they are primary entry points.

**Full-bleed exception:** `VIEW-BROWSE-1` hides `.hg-mockup-nav` via page CSS (`body.yrg-view-browser .hg-mockup-nav { display: none; }`) to preserve three-panel layout height. The **banner stays visible**.

---

## Process

### 1. Add URL patterns

Register each screen in `mockups/urls.py`. URL names follow `mockup_{entity}_{operation}`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path("{entity}/",          views.{entity}_list,   name="mockup_{entity}_list"),
    path("{entity}/create/",   views.{entity}_create, name="mockup_{entity}_create"),
    path("{entity}/<int:id>/", views.{entity}_detail, name="mockup_{entity}_detail"),
]
```

Then add a footer link in `templates/mockups/base.html` (see **Mockup chrome** above).

### 2. Create views with mock data

All mock data lives as module-level constants (`MOCK_*`). Views have no DB access and no auth checks.

```python
import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

MOCK_ITEMS = [...]  # hardcoded list of dicts

def {entity}_list(request):
    """FOB-{ENTITY}-LIST+FIND-1: description."""
    logger.info("Mockup: {entity}_list | user=%s", getattr(request.user, "username", "anonymous"))
    context = {"items": MOCK_ITEMS, "item_count": len(MOCK_ITEMS)}
    return render(request, "mockups/{entity}/list.html", context)
```

### 3. Create templates

**File location:** `src/yggdrasil/web/templates/mockups/{entity}/{operation}.html`

**Always extend the mockup base:**

```html
{% extends "mockups/base.html" %}
{% load static %}

{% block screen_id %}{ENTITY-LIST+FIND-1}{% endblock %}
{% block title %}{Entity}{% endblock %}

{% block content %}
<div data-testid="{entity}-list-page">
  <!-- screen content — LIST+FIND, VIEW, etc. per IA_guidelines.md -->
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function () {
  console.log('[mockup:{entity}-list+find-1] page loaded');
});
</script>
{% endblock %}
```

**Optional — interactive mockups** (play-pretend flows, sessionStorage):

```html
{% block mockup_nav_extra %}
 <span class="text-muted ms-2" data-testid="{entity}-mockup-store-hint">
   · Reset store: clear sessionStorage key <code>ygg-mock-{feature}</code>
 </span>
{% endblock %}
```

Additional conventions:

- Follow `docs/ux/IA_guidelines.md` for LIST+FIND tables, page headers, modals, and `data-testid` naming (`docs/features/CATALOG.md`).
- Bootstrap 5.3+ components throughout.
- Font Awesome icons on all buttons.
- Bootstrap tooltips on interactive elements (initialized globally in `base.html`).
- `data-testid` on all interactive elements.
- Represent UI states: loading, empty, error, success.
- Semantic HTML (`nav`, `main`, `section`), ARIA labels, keyboard navigation.
- **Page headers look real:** Visible title and subtitle use production copy — no Screen IDs, no “interactive mockup” or sessionStorage jargon in `.hg-page-header`. Screen traceability: `{% block screen_id %}` → HTML comment in base; `data-testid` on containers and controls.
- Mockup signaling is **only** via `.hg-mockup-banner` (top) and `.hg-mockup-nav` (footer inventory). Interactive mockups may append sessionStorage reset hints via `{% block mockup_nav_extra %}` in the footer nav only.

### 4. Add accessibility

- Semantic HTML structure
- ARIA labels and roles on interactive elements
- Keyboard navigation support
- Focus management for modals and alerts

---

## Deliverables

- ✅ `mockups/urls.py` — URL patterns for all CRUDLF screens, names as `mockup_{entity}_{operation}`
- ✅ `mockups/views.py` — mock data constants + view functions with INFO-level logging
- ✅ Templates at `src/yggdrasil/web/templates/mockups/{entity}/{operation}.html`
- ✅ Each template extends `mockups/base.html` (inherits `.hg-mockup-banner` + `.hg-mockup-nav`)
- ✅ New routes linked in `base.html` global mockup nav inventory (`data-testid="mockup-screen-nav"`)
- ✅ No duplicate per-page mockup nav blocks
- ✅ Each template has `data-testid="{entity}-{operation}-page"` on the root container
- ✅ Each template has `console.log('[mockup:…]')` calls at key interaction points
- ✅ All UI states represented (empty, loaded, error, success)
- ✅ Accessibility attributes (ARIA, semantic HTML, keyboard nav)
- ✅ Mockups accessible at `/mockups/{entity}/` when `DEBUG=True`; return 404 otherwise

---

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **User Journey** (Document, Required) — produced by Define User Journey (#36).
- **IA Guidelines** (Document, Required) — produced by Define Information Architecture (#37).
- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).

## Agent

None

## Skill

**Title**: Django + HTMX Frontend Implementation Patterns
**Capability Domain**: FRONTEND_FRAMEWORK
**Technology Stack**: Django+HTMX+Graphviz

## Rules

- **Diagrams Element By Element** (`do-diagrams-element-by-element`)
- **Look Via Human Eye** (`do-look-via-human-eye`)
- **View Drawio Diagrams** (`do-view-drawio-diagrams`)

## Artifacts Produced

- **HTML Mockups** (Code) - Required
- **HTML Mockups Template** (Template) - Optional

## Artifacts Consumed

- **User Journey** (Document) - Required
- **IA Guidelines** (Document) - Required
- **Screen Flow / Dialogue Map** (Diagram) - Required

## Notes

No additional notes.
