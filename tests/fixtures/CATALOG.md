# Fixture Library Catalog (TFK-04)

Authoritative reference for test data used by pytest, behave AT, and ESM feature files.
See also: [`docs/architecture/test-architecture.md`](../architecture/test-architecture.md) § Fixture scopes.

**Rule:** no mocks in integration or AT tests — use JSON fixtures, FactoryBoy, or AutoFixture helpers against the real DB.

---

## Session scope — `seed.json`

**File:** [`tests/fixtures/seed.json`](seed.json)
**Loaded:** once per AT suite via `features/at/environment.py` → `context.fixtures = ["seed"]`
**Mechanism:** Django `loaddata` inside behave-django's per-scenario atomic block (rolled back after each scenario)

| PK | Model | Identity | Role |
|----|-------|----------|------|
| 1 | `auth.group` | architect | RBAC group |
| 2 | `auth.group` | viewer | RBAC group |
| 1 | `auth.user` | admin@example.com | admin (`is_staff`, `is_superuser`) |
| 2 | `auth.user` | priya@example.com | architect (group 1) |
| 3 | `auth.user` | elena@example.com | viewer (group 2) |

**Password (all seed users):** `test-pass-only-1234` (MD5 hasher in test settings)

**Load manually:**

```bash
DJANGO_SETTINGS_MODULE=yggdrasil.test_settings uv run python manage.py loaddata seed
```

---

## Suite scope — `presets/`

Loaded for a related group of scenarios when the feature's `environment.py` sets
`context.fixtures = ["presets/<name>"]`. Do **not** combine `seed` and `team_preset`
in the same scenario — they define the same PKs.

### `presets/empty_preset.json`

- **Contents:** `[]`
- **Use when:** isolation tests must start with zero users/groups (no session seed)

```bash
DJANGO_SETTINGS_MODULE=yggdrasil.test_settings uv run python manage.py loaddata presets/empty_preset
```

### `presets/team_preset.json`

- **Contents:** same auth rows as `seed.json` (admin, priya/architect, elena/viewer)
- **Use when:** a feature suite needs the team bundle without relying on session `seed`
  (e.g. E2E suite with its own `before_all` fixture list)

```bash
DJANGO_SETTINGS_MODULE=yggdrasil.test_settings uv run python manage.py loaddata presets/team_preset
```

### `presets/graph_preset.json` (stub)

- **Contents:** `[]` — **intentionally empty**
- **Reason:** `yggdrasil.graph` models do not exist yet; `loaddata` cannot load Element/Relationship rows
- **Canonical reference data:** [`mockups/views.py`](../../mockups/views.py) — `MOCK_ELEMENTS`, `MOCK_RELATIONSHIPS`, `MOCK_CHANGESETS`
- **When to populate:** implement alongside `graph` app models + `ElementFactory` / `RelationshipFactory` in BPE

Intended shape (from mockups, for feature authors):

| Entity | Count | Examples |
|--------|-------|----------|
| Elements | 6 | Payment API, Notification Service, Order Domain |
| Relationships | 6 | Mobile App →calls→ Payment API |
| ChangeSets | 3 | pending (#1), applied (#2, #3) |

---

## Test scope — FactoryBoy factories

**Location:** [`tests/fixtures/factories/`](factories/)

### `UserFactory`

```python
from tests.fixtures.factories import UserFactory

admin = UserFactory(is_admin=True)
architect = UserFactory(is_architect=True)
viewer = UserFactory(is_viewer=True)
```

Traits match SAO.md §13 RBAC: `admin` / `architect` / `viewer`.

### `ElementFactory` / `RelationshipFactory` (stubs)

Not yet usable — raise `NotImplementedError` until `yggdrasil.graph.models` ships.
Do not mock graph entities; use mockup views for AT/E2E until factories are implemented.

---

## Test scope — AutoFixture helpers

**Location:** [`tests/fixtures/autofixture/fixture_creator.py`](autofixture/fixture_creator.py)

One-call user creation when field values do not matter:

```python
from tests.fixtures.autofixture import make_admin, make_architect, make_user, make_viewer

admin = make_admin()
priya = make_architect()
elena = make_viewer()
custom = make_user("viewer")
```

Default password: `test-pass-only-1234`.

---

## Pytest usage

Root [`conftest.py`](../../conftest.py) exposes `client` and `logged_in_user` fixtures.
`logged_in_user` uses `UserFactory(is_viewer=True)` — prefer seed users when scenarios
reference priya/elena/admin by username.

---

## ESM-05 feature file guidance

When writing `.feature` files:

1. **Auth scenarios** — use seed users: `Given the user is logged in as "architect"` (maps to priya-like role via `UserFactory`; for named users, extend steps via TFK-07)
2. **Graph scenarios (mockup phase)** — scenarios assert against mockup HTML; no graph preset required
3. **Missing preset** — invoke TFK-07; do not invent inline fixture JSON in feature files
