# Yggdrasil Information Architecture Guidelines

> **ESM Activity 03 artifact.**
> Adopts the **Huginn design system** — Bootstrap 5.3.8 base, Huginn brand tokens, same component vocabulary.
> Companion documents: `docs/features/user_journey.md` · `docs/conventions.md`
> Last updated: July 2026 — initial capture.

---

## Philosophy

Bootstrap-first. Use Bootstrap 5.3.8 utilities, components, and CSS variables as the first choice.
Customize only when Bootstrap cannot express the requirement or when brand identity demands it.
All Huginn design tokens (`--hg-*`) are adopted verbatim — Yggdrasil extends, never replaces them.

Every component must be:
- **Testable** — `data-testid` on all interactive elements
- **Accessible** — semantic HTML, ARIA attributes, keyboard-navigable
- **Traceable** — Screen IDs flow through journey → dialogue map → feature file → Django template → tests

---

## Table of Contents

1. [Technology Baseline](#1-technology-baseline)
2. [Design Tokens](#2-design-tokens)
3. [Skeleton & Layout](#3-skeleton--layout)
4. [Navigation](#4-navigation)
5. [Component Kit](#5-component-kit)
6. [Behavior & Interactions](#6-behavior--interactions)
7. [Icon System — Font Awesome Free](#7-icon-system--font-awesome-free)
8. [Charts & Graph Visualization](#8-charts--graph-visualization)
9. [Accessibility](#9-accessibility)
10. [Screen ID Convention](#10-screen-id-convention)
11. [Page Header Pattern](#11-page-header-pattern)
12. [CRUDLF Page Templates](#12-crudlf-page-templates)
13. [Button Placement Rules](#13-button-placement-rules)
14. [Feedback / Notification System](#14-feedback--notification-system)
15. [Component State Catalogue](#15-component-state-catalogue)

---

## 1. Technology Baseline

| Concern | Library | Version | Load |
|---|---|---|---|
| CSS framework | Bootstrap | 5.3.8 | CDN — `cdn.jsdelivr.net/npm/bootstrap@5.3.8` |
| Icons | Font Awesome Free | 6.7.2 | CDN — `cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2` |
| Charts | Apache ECharts | 5.5.1 | CDN — `cdn.jsdelivr.net/npm/echarts@5.5.1` |
| Graph | Cytoscape.js | 3.x | CDN — `cdn.jsdelivr.net/npm/cytoscape@3` |
| Interactivity | HTMX | 2.0.4 | CDN — `unpkg.com/htmx.org@2.0.4` |

**CDN policy**: no `integrity` SRI attributes — keep CDN links clean; revisit for production hardening via subresource integrity once versions stabilise.

**FA Free constraint**: only `fa-solid` (filled), `fa-regular` (limited free subset), and `fa-brands` are available. `fa-light`, `fa-thin`, `fa-sharp`, `fa-duotone` are Pro-only and must not appear in any template.

**Cytoscape.js** is loaded on pages that render the View Browser graph mode, the Element detail ego-graph, and the Diagram editor (Part II). It is not loaded globally — include it only where needed via a page-level `{% block extra_js %}`.

**Bootstrap upgrade policy**: track 5.3.x patch releases; evaluate minor bumps (5.4+, 6.x) as an explicit ADR.

---

## 2. Design Tokens

All tokens are CSS custom properties on `:root`. Yggdrasil inherits the full Huginn token set; Yggdrasil-specific additions are marked `/* yrg */`.

### 2.1 Brand Tokens (inherited from Huginn)

```css
:root {
  /* Primary — slate-blue */
  --hg-primary:     #1f3a5f;
  --hg-primary-700: #16294a;   /* hover / active */
  --hg-primary-100: #e7eef7;   /* tinted bg, callout panels */

  /* Accent — muted gold, used sparingly */
  --hg-accent:      #c9a227;
  --hg-accent-700:  #8e7012;

  /* Surface / ink */
  --hg-bg-body:     #f5f7fa;
  --hg-bg-surface:  #ffffff;
  --hg-bg-elevated: #ffffff;
  --hg-bg-subtle:   #f0f3f8;
  --hg-ink:         #1a1f2e;
  --hg-ink-muted:   #5a6478;
  --hg-border:      #e3e7ee;
  --hg-border-strong: #c8cfdb;

  /* Bootstrap overrides */
  --bs-primary:          var(--hg-primary);
  --bs-primary-rgb:      31, 58, 95;
  --bs-body-bg:          var(--hg-bg-body);
  --bs-body-color:       var(--hg-ink);
  --bs-border-color:     var(--hg-border);
  --bs-link-color:       var(--hg-primary);
  --bs-link-color-rgb:   31, 58, 95;
  --bs-link-hover-color: var(--hg-primary-700);
}
```

### 2.2 RYG Semantic Tokens (locked)

These drive element health, ChangeSet confidence, and status signalling. Never repurpose for decoration.

```css
:root {
  --hg-red:    #dc3545;
  --hg-orange: #fd7e14;
  --hg-yellow: #ffc107;
  --hg-green:  #198754;
  --hg-blue:   #0dcaf0;
  --hg-grey:   #6c757d;

  /* Semantic aliases for clarity */
  --hg-status-red:    var(--hg-red);
  --hg-status-orange: var(--hg-orange);
  --hg-status-yellow: var(--hg-yellow);
  --hg-status-green:  var(--hg-green);
  --hg-status-blue:   var(--hg-blue);
  --hg-status-grey:   var(--hg-grey);
}
```

**RYG usage in Yggdrasil:**

| Colour | Element / ChangeSet context | Examples |
|---|---|---|
| Red | Element health: critical / ChangeSet item: rejected | Health badge, confidence very-low |
| Orange | Element health: degraded / confidence: low | Warning in briefing, confidence badge |
| Yellow | Element health: at-risk | Confidence: medium |
| Green | Element health: OK / ChangeSet applied / connected | Applied badge, accepted operation |
| Blue | ChangeSet: pending (awaiting review) | Pending badge |
| Grey | Source: stale / ChangeSet rolled back / Part II inactive | Rolled-back badge, inactive stereotype |

### 2.3 Yggdrasil-Specific Tokens

```css
:root {
  /* Source badges — yrg */
  --yrg-source-ratatosk: #6f42c1;   /* purple — Ratatosk (automated) */
  --yrg-source-human:    var(--hg-primary);
  --yrg-source-mcp:      #0dcaf0;   /* blue — MCP client */

  /* Confidence band — yrg */
  --yrg-conf-high:    var(--hg-green);
  --yrg-conf-medium:  var(--hg-yellow);
  --yrg-conf-low:     var(--hg-orange);
  --yrg-conf-vlow:    var(--hg-red);

  /* Graph canvas — yrg */
  --yrg-graph-bg:     #f8f9fb;
  --yrg-node-fill:    var(--hg-primary-100);
  --yrg-node-stroke:  var(--hg-primary);
  --yrg-edge-stroke:  var(--hg-ink-muted);
}
```

### 2.4 Spacing

Use Bootstrap's spacing utilities (`m-0…m-5`, `p-0…p-5`) as first choice.

```css
:root {
  --hg-card-padding:  1.2rem 1.25rem;
  --hg-card-gap:      1rem;
  --hg-section-gap:   2rem;
  --hg-rail-padding:  0.85rem 1rem;
}
```

### 2.5 Typography

Brand typeface: **Montserrat** (self-hosted in `static/fonts/` or loaded from Google Fonts CDN). Fallback: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.

```css
:root {
  --hg-font-sans: "Montserrat", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --hg-font-mono: "JetBrains Mono", "Fira Code", ui-monospace, monospace;

  /* Sizes */
  --hg-fs-page-title: 1.75rem;
  --hg-fs-h1:  2rem;
  --hg-fs-h2:  1.5rem;
  --hg-fs-h3:  1.25rem;
  --hg-fs-body: 1rem;
  --hg-fs-sm:  0.875rem;
  --hg-fs-xs:  0.78rem;
  --hg-fs-2xs: 0.7rem;
  --hg-fs-3xs: 0.65rem;
  --hg-fs-card-name: 1rem;

  /* Weights */
  --hg-fw-regular:  400;
  --hg-fw-medium:   500;
  --hg-fw-semibold: 600;
  --hg-fw-bold:     700;

  /* Line heights */
  --hg-lh-body:  1.6;
  --hg-lh-tight: 1.25;

  /* Tracking */
  --hg-track-brand: -0.01em;
  --hg-track-caps:  0.06em;
}

/* Huginn-standard utility classes */
.hg-page-title { font-size: var(--hg-fs-page-title); font-weight: var(--hg-fw-semibold); }
.hg-card-name  { font-size: var(--hg-fs-card-name);  font-weight: var(--hg-fw-semibold); }
.hg-label-caps { font-size: 0.68rem; text-transform: uppercase; letter-spacing: var(--hg-track-caps); }
```

### 2.6 Borders, Radii, Shadows

```css
:root {
  --hg-radius:    8px;   /* cards, rails, panels */
  --hg-radius-lg: 12px;
  --hg-radius-md: 6px;   /* inputs, swatches */
  --hg-radius-sm: 4px;   /* buttons, nav-links */
  --hg-radius-pill: 999px;

  --hg-shadow-card-hover: 0 4px 14px rgba(31, 58, 95, 0.12);
  --hg-shadow-popover:    0 8px 24px rgba(31, 58, 95, 0.16);
  --hg-shadow-toast:      0 4px 12px rgba(0, 0, 0, 0.15);
}
```

---

## 3. Skeleton & Layout

### 3.1 Page Shell

Every page follows this structure:

```
<nav .yrg-navbar>           ← fixed top, primary + gold accent border-bottom
<div .hg-page-header>       ← white bar: breadcrumb / title + subtitle + top actions
<main .container-fluid>     ← body bg (#f5f7fa), px-4 py-3
  [page-specific content]
</main>
```

The navbar is `position: fixed; top: 0`. Add `padding-top: calc(56px + 1px)` to `body` to compensate for the fixed bar height.

### 3.2 Layout Patterns

| Pattern | Used by | Bootstrap structure |
|---|---|---|
| **Full-width table** | LIST+FIND screens | `table-responsive` inside `col-12` |
| **View Browser** | `VIEW-BROWSE-1` | Filter panel (top, collapsible) + results area + detail drawer (offcanvas right) + Munin panel (collapsible right) |
| **Single-column form** | CREATE / EDIT screens | `col-md-8 col-lg-6`, centred in `row justify-content-center` |
| **Detail 2-pane** | VIEW screens | `col-lg-8` (properties) + `col-lg-4` (ego-graph + state panel) |
| **Chat 2-pane** | `CHAT-MUNIN-1` | `col-lg-8` (thread) + `col-lg-4` (context panel), fixed height with scroll |
| **ChangeSet review** | `CHANGESET-VIEW_CHANGESET-1` | Full-width table + inline action row |
| **Briefing** | `MUNIN-BRIEFING-1` | `col-lg-8` centred, narrative + structured data blocks |
| **History diff** | `VIEW-HISTORY-1` | `col-lg-3` (timeline rail) + `col-lg-9` (diff panel) |

### 3.3 Navbar CSS

```css
.yrg-navbar {
  background: var(--hg-primary);
  border-bottom: 3px solid var(--hg-accent);
}
.yrg-navbar .navbar-brand {
  color: #fff;
  font-weight: var(--hg-fw-semibold);
  font-family: var(--hg-font-sans);
  letter-spacing: var(--hg-track-brand);
}
.yrg-navbar .navbar-brand .accent { color: var(--hg-accent); }
.yrg-navbar .nav-link {
  color: rgba(255, 255, 255, 0.82);
  padding: 0.5rem 0.9rem;
  border-radius: var(--hg-radius-sm);
  transition: background 0.12s;
}
.yrg-navbar .nav-link:hover  { color: #fff; background: rgba(255, 255, 255, 0.07); }
.yrg-navbar .nav-link.active { color: #fff; background: rgba(255, 255, 255, 0.13); }
```

---

## 4. Navigation

### 4.1 Primary Nav Items

| Nav item | Route | Screen | Icon |
|---|---|---|---|
| View Browser | `/views/` | `VIEW-BROWSE-1` | `fa-solid fa-layer-group` |
| Elements | `/elements/` | `ELEMENT-LIST+FIND-1` | `fa-solid fa-circle-dot` |
| Relationships | `/relationships/` | `RELATIONSHIP-LIST+FIND-1` | `fa-solid fa-link` |
| ChangeSets | `/changesets/` | `CHANGESET-LIST+FIND-1` | `fa-solid fa-code-branch` |
| Runs | `/runs/` | `RATATOSK_RUN-LIST+FIND-1` | `fa-solid fa-terminal` |

**Right side of navbar**: `fa-solid fa-gear` Settings (→ `AUTH-TOKEN-1`) · `fa-solid fa-circle-user` username.

**Default landing after login**: `VIEW-BROWSE-1` (View Browser).

**Part II nav items** (not in MVP navbar, accessible via Settings/admin):

| Nav item | Route | Screen |
|---|---|---|
| Stereotypes | `/metamodel/stereotypes/` | `STEREOTYPE-LIST+FIND-1` |
| Packages | `/metamodel/packages/` | `PACKAGE-LIST+FIND-1` |
| Diagrams | `/metamodel/diagrams/` | `DIAGRAM-LIST+FIND-1` |

### 4.2 Breadcrumbs

Used on all non-list screens (VIEW, CREATE, EDIT nested under a parent entity):

```html
<nav aria-label="breadcrumb">
  <ol class="breadcrumb mb-0">
    <li class="breadcrumb-item"><a href="/elements/">Elements</a></li>
    <li class="breadcrumb-item active" aria-current="page">Notification Service</li>
  </ol>
</nav>
```

Breadcrumb lives in the page header bar (`.hg-page-header`), above the title row.

### 4.3 Active State

Set `aria-current="page"` on the active nav link and add Bootstrap `.active` class.

---

## 5. Component Kit

### 5.1 Atoms

#### Buttons

All buttons carry a Font Awesome icon. Icon-only buttons (table row actions) require `aria-label` and a Bootstrap tooltip.

```html
<!-- Primary action -->
<button class="btn btn-primary" data-bs-toggle="tooltip" title="Create a new element"
        data-testid="create-element-btn">
  <i class="fa-solid fa-plus me-1"></i> Create Element
</button>

<!-- Secondary / outline -->
<button class="btn btn-outline-secondary btn-sm" data-bs-toggle="tooltip" title="Export as Mermaid"
        data-testid="export-mermaid-btn">
  <i class="fa-solid fa-file-export me-1"></i> Export
</button>

<!-- Danger -->
<button class="btn btn-danger" data-bs-toggle="tooltip" title="Delete this element"
        data-testid="delete-element-btn">
  <i class="fa-solid fa-trash me-1"></i> Delete
</button>

<!-- Accept (ChangeSet operation) -->
<button class="btn btn-success btn-sm" data-testid="accept-operation-btn">
  <i class="fa-solid fa-check me-1"></i> Accept
</button>

<!-- Reject (ChangeSet operation) -->
<button class="btn btn-outline-danger btn-sm" data-testid="reject-operation-btn">
  <i class="fa-solid fa-xmark me-1"></i> Reject
</button>
```

Bootstrap btn overrides:

```css
.btn-primary {
  --bs-btn-bg:                 var(--hg-primary);
  --bs-btn-border-color:       var(--hg-primary);
  --bs-btn-hover-bg:           var(--hg-primary-700);
  --bs-btn-hover-border-color: var(--hg-primary-700);
  --bs-btn-active-bg:          var(--hg-primary-700);
  --bs-btn-color:              #fff;
}
.btn-outline-primary {
  --bs-btn-color:              var(--hg-primary);
  --bs-btn-border-color:       var(--hg-primary);
  --bs-btn-hover-bg:           var(--hg-primary);
  --bs-btn-hover-border-color: var(--hg-primary);
  --bs-btn-hover-color:        #fff;
}
```

#### Status Badges

```html
<!-- Element health -->
<span class="badge" style="background: var(--hg-green)" aria-label="health: ok">OK</span>
<span class="badge" style="background: var(--hg-orange)" aria-label="health: degraded">Degraded</span>
<span class="badge" style="background: var(--hg-red)" aria-label="health: critical">Critical</span>

<!-- ChangeSet status -->
<span class="badge" style="background: var(--hg-blue); color: #000">Pending</span>
<span class="badge" style="background: var(--hg-green)">Applied</span>
<span class="badge" style="background: var(--hg-orange)">Rolled back</span>
<span class="badge" style="background: var(--hg-grey)">Rejected</span>

<!-- Source badge -->
<span class="badge" style="background: var(--yrg-source-ratatosk)">Ratatosk</span>
<span class="badge" style="background: var(--hg-primary)">Human</span>
<span class="badge" style="background: var(--yrg-source-mcp); color: #000">MCP</span>

<!-- Confidence -->
<span class="badge" style="background: var(--yrg-conf-high)">High</span>
<span class="badge" style="background: var(--yrg-conf-medium); color: #000">Medium</span>
<span class="badge" style="background: var(--yrg-conf-low)">Low</span>
```

#### Confidence Bar

Inline progress-style indicator used in LIST+FIND tables and detail panels:

```html
<div class="yrg-confidence" title="Confidence: 0.87" aria-label="Confidence 87%">
  <div class="yrg-confidence-track">
    <div class="yrg-confidence-fill" style="width: 87%; background: var(--yrg-conf-high);"></div>
  </div>
  <span class="yrg-confidence-label">0.87</span>
</div>
```

```css
.yrg-confidence       { display: flex; align-items: center; gap: 0.4rem; }
.yrg-confidence-track { flex: 1; height: 4px; background: var(--hg-border); border-radius: 999px; overflow: hidden; }
.yrg-confidence-fill  { height: 100%; border-radius: 999px; transition: width 0.2s; }
.yrg-confidence-label { font-size: var(--hg-fs-xs); color: var(--hg-ink-muted); min-width: 2.5rem; }
```

#### Form Inputs

```html
<div class="mb-3">
  <label for="name" class="form-label">Name <span class="text-danger">*</span></label>
  <input type="text" class="form-control" id="name" name="name"
         placeholder="e.g. Notification Service" required
         data-testid="element-name-input">
  <div class="invalid-feedback">Name is required.</div>
</div>

<div class="mb-3">
  <label for="stereotype" class="form-label">Stereotype</label>
  <select class="form-select" id="stereotype" name="stereotype"
          data-testid="element-stereotype-select">
    <option value="">— choose —</option>
    <option value="system">System</option>
    <option value="container">Container</option>
    <option value="component">Component</option>
    <option value="person">Person</option>
    <option value="external">External</option>
  </select>
</div>

<div class="mb-3">
  <label for="package" class="form-label">Package</label>
  <select class="form-select" id="package" name="package"
          data-testid="element-package-select">
    <option value="context">Context</option>
    <option value="container">Container</option>
    <option value="component">Component</option>
    <option value="code">Code</option>
  </select>
</div>
```

### 5.2 Molecules

#### Element Card (View Browser grid mode)

Used in graph-adjacent list results; not the primary LIST+FIND table view but an optional tile layout.

```html
<article class="yrg-element-card" data-testid="element-card">
  <div class="health-bar {red|orange|yellow|green}"></div>
  <div class="card-body p-3">
    <div class="d-flex align-items-start justify-content-between mb-1">
      <h3 class="hg-card-name mb-0">
        <i class="fa-solid fa-circle-dot me-1" style="color: var(--hg-primary); font-size: 0.75rem;"></i>
        {element-name}
      </h3>
      <span class="badge" style="background: var(--yrg-source-ratatosk); font-size: 0.65rem;">{stereotype}</span>
    </div>
    <p class="text-muted small mb-2">{package} · {owner}</p>
    <div class="d-flex align-items-center gap-2">
      <div class="yrg-confidence" title="Confidence: {score}">
        <div class="yrg-confidence-track" style="width: 80px;">
          <div class="yrg-confidence-fill" style="width: {pct}%; background: var(--yrg-conf-high);"></div>
        </div>
        <span class="yrg-confidence-label">{score}</span>
      </div>
    </div>
  </div>
  <div class="card-foot d-flex justify-content-between align-items-center px-3 py-2">
    <span class="small text-muted">
      <i class="fa-solid fa-clock-rotate-left me-1" style="font-size: 0.7rem;"></i>
      {last-verified}
    </span>
    <span class="badge" style="background: var(--yrg-source-ratatosk); font-size: 0.65rem;">{source}</span>
  </div>
</article>
```

```css
.yrg-element-card {
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
  border-radius: var(--hg-radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.15s, transform 0.15s;
  cursor: pointer;
}
.yrg-element-card:hover {
  box-shadow: var(--hg-shadow-card-hover);
  transform: translateY(-1px);
}
.yrg-element-card .health-bar        { height: 4px; }
.yrg-element-card .health-bar.red    { background: var(--hg-red); }
.yrg-element-card .health-bar.orange { background: var(--hg-orange); }
.yrg-element-card .health-bar.yellow { background: var(--hg-yellow); }
.yrg-element-card .health-bar.green  { background: var(--hg-green); }
.yrg-element-card .card-foot {
  background: #fafbfd;
  border-top: 1px solid var(--hg-border);
  font-size: var(--hg-fs-xs);
}
```

#### LIST+FIND Table

Standard across all entity list screens. Columns vary per entity; row actions are consistent.

```html
<div class="table-responsive">
  <table class="table table-hover align-middle" data-testid="{entity}-table">
    <thead class="table-light">
      <tr>
        <th>{Col1}</th>
        <th>{Col2}</th>
        <th class="text-end">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr data-testid="{entity}-row">
        <td>{value}</td>
        <td>{value}</td>
        <td class="text-end">
          <div class="btn-group btn-group-sm" role="group">
            <button class="btn btn-outline-secondary" data-bs-toggle="tooltip" title="View"
                    aria-label="View" data-testid="view-{entity}-btn">
              <i class="fa-solid fa-eye" aria-hidden="true"></i>
            </button>
            <button class="btn btn-outline-secondary" data-bs-toggle="tooltip" title="Edit"
                    aria-label="Edit" data-testid="edit-{entity}-btn">
              <i class="fa-solid fa-pen" aria-hidden="true"></i>
            </button>
            <button class="btn btn-outline-danger" data-bs-toggle="tooltip" title="Delete"
                    aria-label="Delete" data-testid="delete-{entity}-btn">
              <i class="fa-solid fa-trash" aria-hidden="true"></i>
            </button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

**Columns by entity:**

| Entity | Columns |
|---|---|
| Element | Name · Stereotype · Package · Owner · Health · Confidence · Source · Actions |
| Relationship | From Element · Stereotype · To Element · Confidence · Source · Actions |
| ChangeSet | ID · Source · Submitted · Operations · Mode · Status · Actions |
| Ratatosk Run | Run ID · Trigger · Started · Duration · Candidates · Operations · ChangeSet · Status |

#### Empty State

```html
<div class="text-center py-5" data-testid="{entity}-empty-state">
  <i class="fa-solid fa-{icon} fa-2x mb-3 d-block" style="color: var(--hg-border);"
     aria-hidden="true"></i>
  <p class="mb-1 fw-medium text-muted">{No entities yet.}</p>
  <p class="small mb-3 text-muted">{Explanatory sentence.}</p>
  <a href="{create-url}" class="btn btn-primary btn-sm" data-testid="empty-state-cta">
    <i class="fa-solid fa-plus me-1" aria-hidden="true"></i> {CTA Label}
  </a>
</div>
```

**Empty state copy by screen:**

| Screen | Copy | CTA |
|---|---|---|
| `ELEMENT-LIST+FIND-1` | No elements yet — run Ratatosk bootstrap or create manually. | Create Element |
| `RELATIONSHIP-LIST+FIND-1` | No relationships yet. | Create Relationship |
| `CHANGESET-LIST+FIND-1` | No pending ChangeSets. | — (no CTA) |
| `RATATOSK_RUN-LIST+FIND-1` | No runs yet — bootstrap via CLI or API. | — |

#### ChangeSet Operation Row

Used inside `CHANGESET-VIEW_CHANGESET-1`. Each row is one planned graph operation.

```html
<tr class="yrg-cs-operation" data-testid="cs-operation-row" data-status="{pending|accepted|rejected}">
  <td class="text-muted small">{#}</td>
  <td>
    <span class="badge bg-secondary">{op-type}</span>
    <!-- e.g. Add Element, Link Element, Add to Diagram -->
  </td>
  <td>
    <strong>{target name}</strong>
    <span class="text-muted ms-1 small">→ {stereotype} / {package}</span>
  </td>
  <td>
    <div class="yrg-confidence">
      <div class="yrg-confidence-track" style="width: 60px;">
        <div class="yrg-confidence-fill" style="width:{pct}%; background: var(--yrg-conf-high);"></div>
      </div>
      <span class="yrg-confidence-label">{score}</span>
    </div>
  </td>
  <td>
    <span class="badge {status-class}">{status}</span>
  </td>
  <td class="text-end">
    <div class="btn-group btn-group-sm">
      <button class="btn btn-outline-success" data-testid="accept-op-btn">
        <i class="fa-solid fa-check" aria-hidden="true"></i>
      </button>
      <button class="btn btn-outline-danger" data-testid="reject-op-btn">
        <i class="fa-solid fa-xmark" aria-hidden="true"></i>
      </button>
      <button class="btn btn-outline-secondary" data-bs-toggle="collapse"
              data-bs-target="#do-other-{id}" data-testid="do-other-btn">
        Do Other
      </button>
    </div>
    <div id="do-other-{id}" class="collapse mt-2">
      <textarea class="form-control form-control-sm" rows="2"
                placeholder="e.g. Don't add to Container diagram — it's an external system."
                data-testid="do-other-input-{id}"></textarea>
      <button class="btn btn-sm btn-primary mt-1" data-testid="do-other-submit-{id}">
        <i class="fa-solid fa-rotate-left me-1"></i> Reprocess
      </button>
    </div>
  </td>
</tr>
```

#### Side Rail

Used in View Browser (detail drawer) and ChangeSet summary panel.

```html
<aside class="hg-rail" aria-label="{Rail title}">
  <h6 class="hg-label-caps mb-2">{Section title}</h6>
  <div class="hg-rail-item">
    <i class="fa-solid fa-{icon}" aria-hidden="true"></i>
    <div>
      <div class="fw-medium small">{Title}</div>
      <div class="text-muted" style="font-size: var(--hg-fs-xs);">{Detail}</div>
    </div>
  </div>
</aside>
```

```css
.hg-rail {
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
  border-radius: var(--hg-radius);
  padding: var(--hg-rail-padding);
}
.hg-rail-item {
  display: flex; gap: 0.5rem;
  padding: 0.4rem 0;
  font-size: var(--hg-fs-sm);
  border-bottom: 1px dashed var(--hg-border);
}
.hg-rail-item:last-child { border-bottom: none; }
.hg-rail-item > i        { color: var(--hg-orange); margin-top: 0.12rem; flex-shrink: 0; }
.hg-rail-item.err > i   { color: var(--hg-red); }
```

#### Munin Briefing Block

The narrative block at the top of `MUNIN-BRIEFING-1`. Distinct from plain text — visually signals AI output.

```html
<div class="yrg-munin-block" data-testid="munin-summary">
  <div class="yrg-munin-block-header">
    <i class="fa-solid fa-brain me-2" aria-hidden="true"></i>
    <span class="hg-label-caps">Munin's Summary</span>
  </div>
  <p class="mb-0">{narrative paragraph}</p>
</div>
```

```css
.yrg-munin-block {
  background: var(--hg-primary-100);
  border: 1px solid #c4d3e8;
  border-left: 4px solid var(--hg-primary);
  border-radius: var(--hg-radius);
  padding: 1rem 1.25rem;
}
.yrg-munin-block-header {
  display: flex; align-items: center;
  color: var(--hg-primary);
  font-size: var(--hg-fs-sm);
  font-weight: var(--hg-fw-semibold);
  margin-bottom: 0.5rem;
}
```

### 5.3 Organisms

#### Page Header

```html
<div class="hg-page-header">
  <div class="container-fluid px-4">
    <!-- Row 1: Breadcrumb (detail screens only) -->
    <nav aria-label="breadcrumb" class="mb-1">
      <ol class="breadcrumb mb-0 small">
        <li class="breadcrumb-item"><a href="/elements/">Elements</a></li>
        <li class="breadcrumb-item active" aria-current="page">{Entity Name}</li>
      </ol>
    </nav>

    <!-- Row 2: Title + action cluster -->
    <div class="d-flex justify-content-between align-items-center">
      <div>
        <h1 class="hg-page-title mb-0">
          {Page Title}
          <span class="badge bg-secondary ms-2" style="font-size: 0.75rem;">{count}</span>
        </h1>
        <p class="text-muted small mb-0">{subtitle — last sync, model name, etc.}</p>
      </div>
      <div class="d-flex gap-2">
        {action buttons — see §13 for placement rules}
      </div>
    </div>

    <!-- Row 3: Metadata sub-row (detail / VIEW screens only) -->
    <div class="yrg-meta-row mt-1">
      <span><i class="fa-solid fa-tag me-1" aria-hidden="true"></i>{stereotype}</span>
      <span>·</span>
      <span><i class="fa-solid fa-layer-group me-1" aria-hidden="true"></i>{package}</span>
      <span>·</span>
      <span class="badge" style="background: var(--yrg-source-ratatosk);">{source}</span>
    </div>
  </div>
</div>
```

```css
.hg-page-header {
  background: var(--hg-bg-surface);
  border-bottom: 1px solid var(--hg-border);
  padding: 1rem 0;
}
.yrg-meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--hg-fs-xs);
  color: var(--hg-ink-muted);
}
```

**Row 3 (metadata sub-row)** is present on VIEW screens only. On LIST+FIND and CREATE/EDIT it is omitted.

---

## 6. Behavior & Interactions

### 6.1 HTMX Swap Patterns

| Trigger | `hx-target` | `hx-swap` | Notes |
|---|---|---|---|
| View Browser filter form | `#results-container` | `innerHTML` | Debounced `hx-trigger="input changed delay:300ms"` |
| Inline filter apply | `#results-container` | `innerHTML` | Full results refresh |
| Detail drawer (element click) | `#detail-drawer` | `innerHTML` | Offcanvas right panel |
| ChangeSet "Do Other" reprocess | `#cs-operation-{id}` | `outerHTML` | Replaces just that operation row |
| Form submit | `#form-container` | `outerHTML` | Replaces form section on success |
| Toast (server push) | `#toast-container` | `beforeend` | JS auto-shows new toast |
| Page-level redirect | — | — | Django returns `HX-Redirect`; HTMX follows |
| Munin chat message | `#chat-thread` | `beforeend` | Append assistant turn |

CSRF injection (in `base.html`):

```js
document.body.addEventListener("htmx:configRequest", (evt) => {
  evt.detail.headers["X-CSRFToken"] = document.cookie
    .split("; ")
    .find(r => r.startsWith("csrftoken="))
    ?.split("=")[1] ?? "";
});
```

### 6.2 View Browser Filter Panel

The filter panel collapses to a single summary line when collapsed:

```html
<div id="filter-panel" class="yrg-filter-panel">
  <div class="yrg-filter-summary collapsed-only text-muted small">
    <!-- Shown only when panel is collapsed -->
    <i class="fa-solid fa-filter me-1"></i>
    {active filter summary — e.g. "Package: Container · Stereotype: Component · 2 rules"}
    <button class="btn btn-link btn-sm p-0 ms-2"
            data-bs-toggle="collapse" data-bs-target="#filter-body">
      Edit filters
    </button>
  </div>
  <div id="filter-body" class="collapse show">
    <!-- Package selector, stereotype multi-select, advanced filter builder, time-travel picker -->
    …
    <div class="d-flex gap-2 mt-2">
      <button class="btn btn-primary btn-sm" data-testid="apply-filters-btn">Apply</button>
      <button class="btn btn-outline-secondary btn-sm" data-testid="clear-filters-btn">Clear</button>
      <button class="btn btn-outline-secondary btn-sm ms-auto" data-testid="save-view-btn">
        <i class="fa-solid fa-floppy-disk me-1"></i> Save View
      </button>
    </div>
  </div>
</div>
```

```css
.yrg-filter-panel {
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
  border-radius: var(--hg-radius);
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
}
```

**Time Travel banner** — shown when `?as_of=` is present in URL:

```html
<div class="alert alert-warning d-flex align-items-center gap-2 py-2" role="status"
     data-testid="time-travel-banner">
  <i class="fa-solid fa-clock-rotate-left" aria-hidden="true"></i>
  <span>Viewing model as of <strong>{date}</strong>.</span>
  <a href="?{current-filters}" class="ms-auto btn btn-sm btn-warning">Back to current</a>
  <a href="{history-url}" class="btn btn-sm btn-outline-warning">Compare with now →</a>
</div>
```

### 6.3 Toast Notifications

```html
<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3"
     aria-live="polite" aria-atomic="true">

  <!-- Success -->
  <div class="toast align-items-center text-bg-success border-0 show" role="alert"
       data-bs-autohide="true" data-bs-delay="4000" data-testid="success-toast">
    <div class="d-flex">
      <div class="toast-body">
        <i class="fa-solid fa-circle-check me-2" aria-hidden="true"></i> {Message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  </div>

  <!-- Error — manual dismiss only -->
  <div class="toast align-items-center text-bg-danger border-0 show" role="alert"
       data-bs-autohide="false" data-testid="error-toast">
    <div class="d-flex">
      <div class="toast-body">
        <i class="fa-solid fa-circle-exclamation me-2" aria-hidden="true"></i> {Message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  </div>

</div>
```

### 6.4 Confirmation Modals

Used for destructive operations: Delete Element, Delete Relationship, Roll Back ChangeSet.

```html
<div class="modal fade" id="{action}Modal" tabindex="-1"
     aria-labelledby="{action}ModalLabel" data-testid="{action}-modal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="{action}ModalLabel">{Confirm Action}?</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <p>{Consequence sentence.}</p>
        <!-- Blast-radius detail (Delete Element only) -->
        <div class="yrg-blast-radius" data-testid="blast-radius-panel">
          <p class="hg-label-caps mb-1">Affected</p>
          <ul class="small text-muted mb-0">
            <li>{N} relationship(s) will be orphaned.</li>
            <li>{M} diagram placement(s) will be removed.</li>
          </ul>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-danger" data-testid="{action}-confirm-btn">
          <i class="fa-solid fa-trash me-1" aria-hidden="true"></i> Delete
        </button>
      </div>
    </div>
  </div>
</div>
```

```css
.yrg-blast-radius {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: var(--hg-radius-sm);
  padding: 0.65rem 0.85rem;
  margin-top: 0.75rem;
}
```

### 6.5 Loading / Empty / Error States

Every list and data region must handle all three:

| State | Pattern |
|---|---|
| Loading | `<div class="spinner-border spinner-border-sm text-secondary" role="status"><span class="visually-hidden">Loading…</span></div>` centred in the target container |
| Empty | `.yrg-empty-state` (§5.2) |
| Error | `<div class="alert alert-danger" role="alert"><i class="fa-solid fa-circle-exclamation me-2"></i>{message} <button …>Retry</button></div>` |

---

## 7. Icon System — Font Awesome Free

**Only `fa-solid` (filled) as the primary style.** `fa-regular` is available for the limited free subset; `fa-brands` for vendor logos.

### 7.1 Standard Icon Mapping

| Action / Concept | Icon class |
|---|---|
| Create / Add | `fa-solid fa-plus` |
| Edit | `fa-solid fa-pen` |
| View / Inspect | `fa-solid fa-eye` |
| Delete | `fa-solid fa-trash` |
| Save | `fa-solid fa-floppy-disk` |
| Cancel | `fa-solid fa-xmark` |
| Accept / Approve | `fa-solid fa-check` |
| Reject | `fa-solid fa-xmark` |
| Reprocess ("Do Other") | `fa-solid fa-rotate-left` |
| Roll back | `fa-solid fa-rotate-left` |
| Search | `fa-solid fa-magnifying-glass` |
| Filter | `fa-solid fa-filter` |
| Export | `fa-solid fa-file-export` |
| View Browser | `fa-solid fa-layer-group` |
| Element (vertex) | `fa-solid fa-circle-dot` |
| Relationship (edge) | `fa-solid fa-link` |
| ChangeSet | `fa-solid fa-code-branch` |
| Ratatosk Run | `fa-solid fa-terminal` |
| Stereotype | `fa-solid fa-tag` |
| Package | `fa-solid fa-layer-group` |
| Diagram | `fa-solid fa-sitemap` |
| Model / Graph | `fa-solid fa-diagram-project` |
| Munin (AI) | `fa-solid fa-brain` |
| History / Time travel | `fa-solid fa-clock-rotate-left` |
| Confidence | `fa-solid fa-gauge-high` |
| Blast radius | `fa-solid fa-burst` |
| API token | `fa-solid fa-key` |
| Settings | `fa-solid fa-gear` |
| Status: OK | `fa-solid fa-circle-check` (green) |
| Status: Warning | `fa-solid fa-triangle-exclamation` (orange) |
| Status: Error | `fa-solid fa-circle-exclamation` (red) |
| Status: Syncing | `fa-solid fa-circle-half-stroke fa-spin` |
| Auto-applied | `fa-solid fa-arrows-rotate` |
| Pending (ChangeSet) | `fa-solid fa-hourglass-half` |
| User | `fa-solid fa-circle-user` |
| GitLab | `fa-brands fa-gitlab` |
| GitHub | `fa-brands fa-github` |

### 7.2 Icon Usage Rules

- Always pair an icon with visible text on non-icon-only controls.
- Icon-only controls (table row actions) **must** have `aria-label` + Bootstrap `title` tooltip.
- Use `me-1` between icon and label text.
- Decorative icons: add `aria-hidden="true"`.
- Never use icons as the sole carrier of meaning without a text or ARIA alternative.

---

## 8. Charts & Graph Visualization

### 8.1 Apache ECharts (Metrics)

Used in `MUNIN-BRIEFING-1` (confidence distribution), `RATATOSK_RUN-VIEW_RATATOSK_RUN-1` (extraction stats), and any future analytics views.

**Token palette for charts:**

```js
const HG = {
  primary: "#1f3a5f",
  red:     "#dc3545",
  orange:  "#fd7e14",
  yellow:  "#ffc107",
  green:   "#198754",
  blue:    "#0dcaf0",
  muted:   "#5a6478",
  border:  "#e3e7ee",
};
```

Standard series colour order: `HG.primary`, `HG.green`, `HG.orange`, `HG.red`, `HG.yellow`.

**Chart conventions:**
- Grid: `left: "5%"`, `right: "3%"`, `containLabel: true`.
- Tooltip: `trigger: "axis"`, `backgroundColor: HG.primary`.
- Legend: top-right, `fontSize: 11`.
- X-axis label: `color: HG.muted`.
- Y-axis: no border, `splitLine.lineStyle.color: HG.border`.
- Call `chart.resize()` on window resize.

### 8.2 Cytoscape.js (Graph Visualization)

Used in `VIEW-BROWSE-1` (graph mode), `ELEMENT-VIEW_ELEMENT-1` (ego-graph), `DIAGRAM-LIST+FIND-1` (Part II layout editor).

**Standard Cytoscape styles:**

```js
const cytoscapeStyle = [
  {
    selector: "node",
    style: {
      "background-color": "#e7eef7",      // --hg-primary-100
      "border-width": 1.5,
      "border-color": "#1f3a5f",          // --hg-primary
      "label": "data(name)",
      "font-size": "11px",
      "font-family": "Montserrat, system-ui, sans-serif",
      "color": "#1a1f2e",                 // --hg-ink
      "text-valign": "center",
      "text-wrap": "ellipsis",
      "text-max-width": "80px",
      "width": 60,
      "height": 60,
    },
  },
  {
    selector: "node[health = 'red']",
    style: { "border-color": "#dc3545", "border-width": 3 },
  },
  {
    selector: "node[health = 'green']",
    style: { "border-color": "#198754", "border-width": 2 },
  },
  {
    selector: "edge",
    style: {
      "line-color": "#5a6478",            // --hg-ink-muted
      "target-arrow-color": "#5a6478",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      "label": "data(stereotype)",
      "font-size": "9px",
      "color": "#5a6478",
      "text-rotation": "autorotate",
      "text-margin-y": -6,
      "width": 1.5,
    },
  },
  {
    selector: ":selected",
    style: {
      "border-color": "#c9a227",          // --hg-accent
      "border-width": 3,
    },
  },
];

const cytoscapeLayout = { name: "cose", animate: false, padding: 32 };
```

**Container:**

```html
<div id="graph-canvas" class="yrg-graph-canvas" data-testid="graph-canvas"
     style="height: 480px; background: var(--yrg-graph-bg); border-radius: var(--hg-radius);
            border: 1px solid var(--hg-border);">
</div>
```

---

## 9. Accessibility

### 9.1 Semantic HTML

| Context | Element |
|---|---|
| Top navigation | `<nav aria-label="Primary navigation">` |
| Page main content | `<main>` |
| Side rail / detail panel | `<aside aria-label="{rail title}">` |
| Entity card | `<article>` |
| Data table | `<table>` with `aria-label` or `<caption>` |
| Filter region | `<section aria-label="Filter panel">` |
| Status summary | `role="status"` or `aria-live="polite"` |
| Chat thread | `aria-live="polite"` on the thread container |

### 9.2 ARIA Requirements

- Icon-only buttons: `aria-label="{action}"`.
- All form inputs: `<label>` explicitly linked via `for`/`id`.
- Dynamic HTMX regions: wrap in `aria-live="polite"`.
- Modals: `aria-labelledby` → modal title; `tabindex="-1"` on `.modal`.
- Colour-only status badges: add `aria-label` with text value.
- Cytoscape graph: provide a table-mode fallback (the table/graph toggle in `VIEW-BROWSE-1` already serves this).

### 9.3 Keyboard Navigation

- Tab order follows visual reading order.
- Modal dialogs trap focus while open (Bootstrap).
- Dropdowns navigable via arrow keys (Bootstrap).
- Cytoscape graph: keyboard pan/zoom via arrow keys + `+`/`-`. Provide "Open as table" escape.

### 9.4 Contrast

| Pair | Ratio |
|---|---|
| `--hg-ink` (#1a1f2e) on white | 16.6:1 ✓ |
| White on `--hg-primary` (#1f3a5f) | 8.2:1 ✓ |
| `--hg-ink-muted` (#5a6478) on white | 4.9:1 ✓ |
| White on `--hg-red` (#dc3545) | 4.6:1 ✓ |
| White on `--hg-green` (#198754) | 4.5:1 ✓ |

---

## 10. Screen ID Convention

### 10.1 Format

```
{ENTITY}-{OPERATION}-{VERSION}
```

- `{ENTITY}` — uppercase entity name (see §10.3)
- `{OPERATION}` — CRUDLF operation (see §10.2)
- `{VERSION}` — integer, starts at `1`

### 10.2 Operations

Standard CRUDLF:

| Operation | Pattern | Example |
|---|---|---|
| `LIST+FIND` | List with search/filter — entry point | `ELEMENT-LIST+FIND-1` |
| `CREATE_{ENTITY}` | Creation form | `ELEMENT-CREATE_ELEMENT-1` |
| `VIEW_{ENTITY}` | Read-only detail | `ELEMENT-VIEW_ELEMENT-1` |
| `EDIT_{ENTITY}` | Edit form | `ELEMENT-EDIT_ELEMENT-1` |
| `DELETE_{ENTITY}` | Deletion confirmation | `ELEMENT-DELETE_ELEMENT-1` |

Yggdrasil extensions:

| Operation | Used by | Example |
|---|---|---|
| `BROWSE` | View Browser | `VIEW-BROWSE-1` |
| `HISTORY` | Model history diff | `VIEW-HISTORY-1` |
| `BRIEFING` | Post-run briefing / export | `MUNIN-BRIEFING-1` · `EXPORT-BRIEFING-1` |
| `TOKEN` | API token management | `AUTH-TOKEN-1` |
| `ASSIST` | Munin chat panel | `CHAT-MUNIN-1` |

### 10.3 Traceability Chain

Each Screen ID must appear in:

1. **`docs/features/user_journey.md`** — `#### Screen: {ID}` heading
2. **`docs/ux/2_dialogue-maps/screen-flow.md`** — box label in Mermaid diagram
3. **Feature file** — `Feature: {ID} …` title in `docs/features/act-N/`
4. **Django template** — HTML comment `<!-- Screen: {ID} -->` on first line of `{% block content %}`
5. **Tests** — `data-testid` values reference the Screen ID; test docstrings cite it

Grep-friendly: `grep -r "ELEMENT-LIST+FIND-1" .` finds every artefact for that screen.

### 10.4 Complete Screen Inventory

| Screen ID | Act | Description | Phase |
|---|---|---|---|
| `AUTH-LOGIN-1` | 0 | Login form | MVP |
| `AUTH-TOKEN-1` | 0 | API token management | MVP |
| `MUNIN-BRIEFING-1` | 1 | Post-run architectural briefing | MVP |
| `VIEW-BROWSE-1` | 2 | View Browser — filter panel + table/graph results | MVP |
| `EXPORT-BRIEFING-1` | 2 | Export modal (Mermaid / Markdown deck / JSON) | MVP |
| `VIEW-HISTORY-1` | 2 | Model history timeline and A/B diff | MVP |
| `ELEMENT-LIST+FIND-1` | 3 | Elements list & search | MVP |
| `ELEMENT-VIEW_ELEMENT-1` | 3 | Element detail | MVP |
| `ELEMENT-CREATE_ELEMENT-1` | 3 | Create element form | MVP |
| `ELEMENT-EDIT_ELEMENT-1` | 3 | Edit element form | MVP |
| `ELEMENT-DELETE_ELEMENT-1` | 3 | Delete confirmation + blast-radius | MVP |
| `RELATIONSHIP-LIST+FIND-1` | 4 | Relationships list & search | MVP |
| `RELATIONSHIP-VIEW_RELATIONSHIP-1` | 4 | Relationship detail | MVP |
| `RELATIONSHIP-CREATE_RELATIONSHIP-1` | 4 | Create relationship form | MVP |
| `RELATIONSHIP-EDIT_RELATIONSHIP-1` | 4 | Edit relationship form | MVP |
| `RELATIONSHIP-DELETE_RELATIONSHIP-1` | 4 | Delete confirmation | MVP |
| `CHANGESET-LIST+FIND-1` | 7 | ChangeSet queue | MVP |
| `CHANGESET-VIEW_CHANGESET-1` | 7 | ChangeSet review (Accept / Reject / Do Other) | MVP |
| `CHAT-MUNIN-1` | 8 | Munin chat panel (embedded in `VIEW-BROWSE-1`) | MVP |
| `RATATOSK_RUN-LIST+FIND-1` | 9 | Ratatosk run list | MVP |
| `RATATOSK_RUN-VIEW_RATATOSK_RUN-1` | 9 | Run detail (extraction log + Munin blackboard) | MVP |
| `STEREOTYPE-LIST+FIND-1` | 10 | Stereotype definitions | Part II |
| `PACKAGE-LIST+FIND-1` | 10 | Package hierarchy | Part II |
| `DIAGRAM-LIST+FIND-1` | 10 | Diagram list + graph editor | Part II |

---

## 11. Page Header Pattern

Every page that is not a full-bleed canvas (View Browser graph mode, Cytoscape editor) uses the standard page header. The header has up to three rows; which rows appear depends on the screen type.

### 11.1 Row Definitions

| Row | Always present? | Content |
|---|---|---|
| **Row 1 — Breadcrumb** | VIEW, EDIT, CREATE only | `<nav aria-label="breadcrumb">` with parent list link → current entity name |
| **Row 2 — Title + action cluster** | All screens | `<h1 class="hg-page-title">` + optional count badge; action cluster right-aligned (see §13) |
| **Row 3 — Metadata sub-row** | VIEW screens only | Stereotype · Package · Source badge · Last verified |

### 11.2 Header by Screen Type

| Screen type | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| LIST+FIND | ✗ | Title + count + [Create {Entity}] | ✗ |
| VIEW | ✓ parent list | Title + [Edit] [Delete] | ✓ stereotype · package · source |
| CREATE | ✓ parent list | "Create {Entity}" + [Cancel] | ✗ |
| EDIT | ✓ parent list + entity name | "Edit {Entity Name}" + [Cancel] | ✗ |
| DELETE (modal) | (inside modal header) | — | — |
| VIEW-BROWSE-1 | ✗ | "View Browser" + saved-views dropdown + [Export] | ✗ |
| MUNIN-BRIEFING-1 | ✗ | "Ratatosk Run #{id}" + [Review ChangeSet →] | Run metadata (source, timestamp) |
| CHANGESET-VIEW | ✓ changesets list | "ChangeSet #{id}" + [Accept All] [Reject All] [Roll Back] | Source · Mode badge · Submitted |

### 11.3 Page Subtitle

The subtitle line (directly below the title) follows these conventions:

| Screen | Subtitle pattern |
|---|---|
| LIST+FIND | `{N} elements · last synced {time}` |
| VIEW-BROWSE-1 | `{N} results · model: {model name}` |
| CHANGESET-VIEW | `{N} operations · submitted {time} · mode: {Auto\|Manual}` |
| MUNIN-BRIEFING-1 | `Run #{id} · {N} ops auto-applied · {M} queued` |

---

## 12. CRUDLF Page Templates

### 12.1 List+Find

```
┌─ Page Header (title + count badge + [Create]) ─────────────────────────────┐
│                                                                              │
├─ Filter bar (inline, single row for simple filters) ───────────────────────┤
│  Search input · Stereotype select · Package select · Source select · [Clear] │
│                                                                              │
├─ Results ───────────────────────────────────────────────────────────────────┤
│  .table-responsive > table.table.table-hover                                │
│    thead.table-light > (entity-specific columns) | Actions                  │
│    tbody > rows with row-actions btn-group-sm at text-end                   │
│                                                                              │
│  (empty state when tbody is empty)                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Column layout**: Full-width `col-12`. No side rail.
- **Actions column**: always last, `text-end`. Contains btn-group-sm with View / Edit / Delete icon buttons.
- **Pagination**: Bootstrap `.pagination` below the table when result count > page size.
- **Empty state**: centred inside the results area (see §5.2).

### 12.2 View (Detail)

```
┌─ Page Header (breadcrumb + title + [Edit] [Delete]) ───────────────────────┐
│                                                                              │
├─ Main area ─────────────────────────────────────────────────────────────────┤
│  col-lg-8                          │  col-lg-4                              │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────┐ │
│  │ Properties card              │  │  │ State panel (health, confidence, │ │
│  │ (JSONB fields, key-value)    │  │  │  provenance, last verified)      │ │
│  └──────────────────────────────┘  │  └──────────────────────────────────┘ │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────┐ │
│  │ Relationships table          │  │  │ Ego-graph (Cytoscape, 240px)     │ │
│  │ (inbound + outbound tabs)    │  │  └──────────────────────────────────┘ │
│  └──────────────────────────────┘  │                                        │
└────────────────────────────────────┴────────────────────────────────────────┘
```

- **No full-page actions** that are destructive — Delete always opens a confirmation modal.
- **Edit** navigates to the EDIT screen; it does not inline-edit on the VIEW screen.

### 12.3 Create / Edit

```
┌─ Page Header (breadcrumb + title + [Cancel]) ──────────────────────────────┐
│                                                                              │
├─ Form area ─────────────────────────────────────────────────────────────────┤
│  row justify-content-center                                                 │
│    col-md-8 col-lg-6                                                        │
│      <form>                                                                 │
│        [field groups ordered: required fields first, optional last]         │
│        [dynamic sections: Properties (stereotype-driven), Relationships,   │
│                           Diagram placement]                                │
│        <div class="d-flex justify-content-end gap-2 mt-4">                 │
│          [Cancel] [Save] ← rightmost                                        │
│        </div>                                                               │
│      </form>                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Field order**: Name (required) → Stereotype → Package → Owner → Properties (dynamic) → Relationships → Diagram hints.
- **Validation**: `novalidate` on `<form>`; Bootstrap `.was-validated` class applied on submit attempt; `.invalid-feedback` below each field.
- **Dynamic properties**: shown/hidden via HTMX `hx-get` swap when Stereotype changes — fetches the stereotype's property schema and renders the matching fields.

### 12.4 Delete (Modal)

Delete never gets a full page. It is always a Bootstrap modal triggered from a row action or the VIEW screen.

Modal structure: see §6.4. The blast-radius panel is mandatory for Element deletion; optional for Relationship deletion.

After confirmation, Django returns `HX-Redirect` to the parent LIST+FIND URL with a success toast.

---

## 13. Button Placement Rules

### 13.1 Universal Rules

1. **Primary action is always the rightmost button** in its cluster.
2. **Destructive actions (Delete, Roll Back) are always the leftmost** in their cluster, visually separated when possible.
3. **Cancel is always to the left of Save/Submit.**
4. **Bulk actions** (Accept All, Reject All) sit in the page header action cluster, not inline with individual rows.

### 13.2 Placement Table

| Context | Cluster position | Left → right order |
|---|---|---|
| LIST+FIND page header | Top-right of header bar | [Secondary actions…] [Create {Entity}] |
| CREATE / EDIT form footer | Bottom-right of form column | [Cancel] [Save] |
| VIEW page header | Top-right of header bar | [Delete] [Edit] |
| DELETE modal footer | Modal footer, right-aligned | [Cancel] [Delete] |
| ChangeSet page header | Top-right of header bar | [Roll Back] [Reject All] [Accept All] |
| ChangeSet operation row | Right end of row | [Accept] [Reject] [Do Other] |
| Munin Briefing header | Top-right of header bar | [Review ChangeSet →] |
| View Browser filter bar | Bottom of filter panel | [Clear] · (spacer) · [Save View] [Apply] |
| Export modal footer | Modal footer, right-aligned | [Cancel] [Export as JSON] [Export as Mermaid] [Export as Markdown Deck] |

### 13.3 Button Variant by Action Type

| Action type | Variant |
|---|---|
| Primary (create, save, apply, accept) | `btn-primary` |
| Secondary / neutral (cancel, clear, back) | `btn-secondary` or `btn-outline-secondary` |
| Destructive (delete, roll back, reject) | `btn-danger` or `btn-outline-danger` |
| Warning (reprocess, re-run) | `btn-outline-warning` |
| Export / download | `btn-outline-secondary` |

---

## 14. Feedback / Notification System

### 14.1 Feedback Types and Mechanisms

| Type | UI component | Position | Auto-dismiss | Trigger |
|---|---|---|---|---|
| **Success** | Bootstrap Toast `text-bg-success` | Bottom-right, fixed | Yes — 4 000 ms | Django `messages.success()` → HTMX `HX-Trigger: showToast` |
| **Error** | Bootstrap Toast `text-bg-danger` | Bottom-right, fixed | **No** — manual dismiss | Django `messages.error()` → `HX-Trigger: showToast` |
| **Warning** | Bootstrap Toast `text-bg-warning text-dark` | Bottom-right, fixed | Yes — 6 000 ms | Django `messages.warning()` |
| **Info** | Bootstrap Toast `text-bg-info text-dark` | Bottom-right, fixed | Yes — 4 000 ms | Django `messages.info()` |
| **Field validation** | `.invalid-feedback` below each field | Inline, in form | N/A — cleared on correction | Bootstrap `.was-validated` on form + HTML5 + Django form errors |
| **Page-level error** | `<div class="alert alert-danger" role="alert">` | Top of main content | No | Server error, 404, permission denied |
| **Time Travel banner** | `<div class="alert alert-warning">` | Top of View Browser results | No — until URL cleared | `?as_of=` present in URL |
| **Munin progress** | Inline `<div class="spinner-border">` + live text | Inside the target container | N/A | HTMX polling or SSE |

### 14.2 Backend → Frontend Protocol

**HTMX response headers for toasts:**

```python
# views/base.py
def htmx_response(request, content="", status=200, *, toast_type=None, toast_msg=None, redirect_to=None):
    response = HttpResponse(content, status=status)
    if redirect_to:
        response["HX-Redirect"] = redirect_to
    if toast_type and toast_msg:
        response["HX-Trigger"] = json.dumps({
            "showToast": {"type": toast_type, "message": toast_msg}
        })
    return response
```

**Frontend listener** (in `base.html`):

```js
document.body.addEventListener("showToast", (evt) => {
  const { type, message } = evt.detail;
  const toast = buildToast(type, message);
  document.getElementById("toast-container").appendChild(toast);
  bootstrap.Toast.getOrCreateInstance(toast).show();
});
```

### 14.3 Django Messages → Toast Mapping

| `messages` level | Toast variant | Auto-dismiss |
|---|---|---|
| `SUCCESS` | `text-bg-success` | 4 000 ms |
| `WARNING` | `text-bg-warning text-dark` | 6 000 ms |
| `ERROR` | `text-bg-danger` | Manual |
| `INFO` | `text-bg-info text-dark` | 4 000 ms |

### 14.4 Munin Agentic Operations (long-running)

For `do_other` reprocessing and multi-step Munin operations, use HTMX polling:

```html
<div id="munin-progress" hx-get="/changesets/{id}/status/" hx-trigger="every 2s"
     hx-swap="outerHTML" data-testid="munin-progress">
  <div class="d-flex align-items-center gap-2 text-muted small">
    <div class="spinner-border spinner-border-sm" role="status">
      <span class="visually-hidden">Munin is reprocessing…</span>
    </div>
    Munin is replanning — {step description}…
  </div>
</div>
```

When complete, the server returns the updated operation row HTML (no polling attribute) and triggers a `showToast` event.

---

## 15. Component State Catalogue

### 15.1 Required Components

All states must be implemented for: Button, Input, Select, Table Row, ChangeSet Operation Row, Element Card, Confidence Bar, Toast, Modal.

### 15.2 Button States

| State | Visual treatment | Notes |
|---|---|---|
| Default | `btn-primary` / `btn-outline-*` base styles | — |
| Hover | Background → `--hg-primary-700`; 120ms ease | Bootstrap handles via `--bs-btn-hover-bg` |
| Focus | Blue `box-shadow` focus ring (`0 0 0 0.25rem rgba(31, 58, 95, 0.25)`) | Bootstrap's `.btn:focus-visible` |
| Active / pressed | Background → `--hg-primary-700` | Bootstrap `--bs-btn-active-bg` |
| Disabled | `opacity: 0.65`; `cursor: not-allowed` | Add `disabled` attr + `aria-disabled="true"` |
| Loading | Replace label with `<span class="spinner-border spinner-border-sm me-1">` + "Saving…"; disable button | Prevent double-submit |

### 15.3 Input States

| State | Visual treatment |
|---|---|
| Default | Bootstrap `.form-control` base |
| Focus | `border-color: --hg-primary`; `box-shadow: 0 0 0 0.25rem rgba(31, 58, 95, 0.25)` |
| Valid | `.is-valid` — green border + `<div class="valid-feedback">` |
| Invalid | `.is-invalid` — red border + `<div class="invalid-feedback">` |
| Disabled | `disabled` attr; `background: #e9ecef`; `cursor: not-allowed` |
| Read-only | `readonly` attr; `background: var(--hg-bg-subtle)` |

### 15.4 Table Row States

| State | Visual treatment |
|---|---|
| Default | No background |
| Hover | `table-hover` applies `--bs-table-hover-bg` (light grey) |
| Selected | `table-active` class; background `var(--hg-primary-100)` |
| Loading (HTMX swap) | Add `opacity: 0.5` + pointer-events-none during the swap |

### 15.5 ChangeSet Operation Row States

| Status | Row treatment |
|---|---|
| Pending | Default row; action buttons active |
| Accepted | `table-success` (`background: #d1e7dd`); action buttons hidden; `fa-check` icon |
| Rejected | `table-danger` (`background: #f8d7da`); action buttons hidden; `fa-xmark` icon |
| Processing (Do Other) | `opacity: 0.6`; Munin spinner shown inline |

### 15.6 Confidence Bar States

| Confidence band | Fill colour | Label |
|---|---|---|
| ≥ 0.85 | `--yrg-conf-high` (green) | numeric score |
| 0.60 – 0.84 | `--yrg-conf-medium` (yellow) | numeric score |
| 0.40 – 0.59 | `--yrg-conf-low` (orange) | numeric score |
| < 0.40 | `--yrg-conf-vlow` (red) | numeric score |

### 15.7 Toast States

| State | Visual |
|---|---|
| Entering | Bootstrap slide-in from bottom-right (built-in) |
| Visible | Fully opaque |
| Auto-dismissing | Bootstrap fade-out on timer |
| Manual dismiss | User clicks × → Bootstrap fade-out |

### 15.8 Modal States

| State | Visual |
|---|---|
| Closed | `display: none` |
| Opening | Bootstrap `.fade` + `.show` transition (150ms) |
| Open | Backdrop `rgba(0,0,0,0.5)`; modal centred; focus trapped |
| Submitting | Confirm button enters Loading state (§15.2); Cancel disabled |
| Closing | Bootstrap fade-out |

### 15.9 Element Card (View Browser tile)

| State | Visual |
|---|---|
| Default | Border `--hg-border`; no shadow |
| Hover | `box-shadow: --hg-shadow-card-hover`; `translateY(-1px)` |
| Selected | Border `--hg-accent` (gold); `box-shadow` maintained |
| Loading | `opacity: 0.5`; `pointer-events: none` |

### 15.10 Cytoscape Node / Edge States

| State | Visual |
|---|---|
| Default | Node: fill `--hg-primary-100`, stroke `--hg-primary` 1.5px |
| Hover | Node border widens to 2.5px via `mouseover` handler |
| Selected | Node border `--hg-accent` (gold) 3px |
| Health: OK | Border `--hg-green` |
| Health: degraded | Border `--hg-orange` |
| Health: critical | Border `--hg-red` |
| Edge default | Stroke `--hg-ink-muted` 1.5px |
| Edge selected | Stroke `--hg-accent` 2px |
