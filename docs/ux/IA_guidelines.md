# Yggdrasil Information Architecture (ESM-03)

Bootstrap 5.3+ design system for Django + HTMX. Customize only for brand and graph-specific patterns.

## Design Tokens

| Token | Value |
|-------|-------|
| Primary | `#2563eb` (blue-600) |
| Secondary | `#64748b` (slate-500) |
| Success | `#16a34a` |
| Warning | `#ca8a04` |
| Danger | `#dc2626` |
| Font | system-ui, -apple-system, "Segoe UI", Roboto |
| Spacing | Bootstrap default scale (0.25rem base) |
| Border radius | `0.375rem` (rounded) |

## Layout Patterns

### App shell (all authenticated pages)

```
┌─────────────────────────────────────────────────────────┐
│ Top navbar: logo | Elements | Relationships | Views | … │
├──────────┬──────────────────────────────┬───────────────┤
│ Filter   │ Main content                 │ Detail drawer │
│ sidebar  │ (table or Cytoscape canvas)  │ (optional)    │
│ (3 col)  │ (6–9 col)                    │ (3 col)       │
└──────────┴──────────────────────────────┴───────────────┘
```

### Dashboard / View Browser (`VIEW-BROWSE-1`)

- Left: filter panel (collapsible on mobile)
- Center: results table OR full-height Cytoscape graph
- Right: detail drawer (HTMX-loaded on row click)

### CRUDLF pages

- **LIST+FIND:** filter bar above table; pagination below
- **VIEW:** 2-column — properties left, relationships + mini-graph right
- **CREATE/EDIT:** single-column form, max-width 720px
- **DELETE:** Bootstrap modal, destructive button leftmost

## Navigation

- Top navbar: Elements, Relationships, Stereotypes, Packages, Diagrams, Change Sets, AI Chat, Ratatosk Runs
- Breadcrumbs on all non-dashboard pages: `Home > {Entity} > {Name}`
- Active nav item: `aria-current="page"`

## Component Patterns

- **Buttons:** Font Awesome icons + Bootstrap tooltips on all actions
- **Tables:** `table-hover`, sortable headers, row actions dropdown
- **Forms:** floating labels; stereotype-driven dynamic fields via HTMX
- **Modals:** delete confirmations, change-set item review
- **Empty states:** illustration + CTA
- **Badges:** health (green/amber/red), confidence %, source (Ratatosk/Manual)

## Cytoscape Graph View Pattern

- Container: `#graph-canvas`, min-height 480px, `data-testid="graph-canvas"`
- Toolbar: zoom in/out, fit, layout selector (cose, dagre), export PNG
- Node styling by stereotype color map (documented in diagram JSON)
- Click node → HTMX load detail drawer
- Double-click → navigate to `ELEMENT-VIEW_ELEMENT-1`

## AI Chat Pattern (`CHAT-ASSIST-1`)

- Message list: user (right, primary), assistant (left, light)
- Assistant messages include inline links to element view URLs
- Citation panel below assistant message: referenced elements as chips
- Input: textarea + Send; loading indicator during LLM call
- Token usage footer (observability tier 3)

## Page Header Pattern

1. **Row 1:** breadcrumbs
2. **Row 2:** title (h1) + action cluster (primary rightmost)
3. **Row 3 (detail pages):** metadata — owner, health badge, last verified

## Button Placement Rules

| Context | Order (left → right) |
|---------|----------------------|
| List header | [Secondary actions…] [Primary Create] |
| Form footer | [Cancel] [Save] |
| Modal footer | [Cancel] [Destructive] [Confirm] |
| Change review | [Reject] [Approve Selected] [Approve All High Confidence] |

## Feedback System

| Type | Mechanism | Dismiss |
|------|-----------|---------|
| Success | Django messages + Bootstrap alert | Auto 5s |
| Error | Django messages + alert-danger | Manual |
| Field validation | `invalid-feedback` under field | On fix |
| HTMX errors | `hx-target` swap alert partial | Manual |

## Component State Catalogue

All interactive elements: default, hover, focus (visible ring), active, disabled (`aria-disabled`), loading (spinner on button).

## Accessibility

- Semantic HTML (`nav`, `main`, `section`)
- ARIA labels on icon-only buttons
- Keyboard: Tab order, Escape closes modals
- Graph: keyboard focus on selected node announced via `aria-live`
