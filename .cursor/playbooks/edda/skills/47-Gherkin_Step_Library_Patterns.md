# Gherkin Step Library Patterns

**Skill ID**: 47
**Capability Domain**: BDD Step Engineering
**Technology Stack**: gherkin, behave, step-definitions
**Linked Activities**: 2

## Content

# Skill: Gherkin Step Library Patterns

**Capability Domain**: BDD_AUTHORING
**Technology Stack**: Gherkin+behave

## Overview

Patterns for organizing, versioning, and composing reusable Gherkin step definitions. The step library is the shared vocabulary between ESM (which writes .feature files) and TAF (which implements the steps).

## Reference Implementation

### Pattern 1: Step Library Organization

```
tests/acceptance/features/steps/
├── navigation_steps.py      # Given/When/Then for page navigation
├── form_steps.py            # Form interactions (fill, select, submit)
├── table_steps.py           # Table verification (rows, columns, sorting)
├── auth_steps.py            # Authentication (login, logout, roles)
├── assertion_steps.py       # Generic assertions (visible, contains, count)
├── dialog_steps.py          # Modal/dialog interactions
├── common_steps.py          # Utility (wait, screenshot, context)
└── CATALOG.md               # Step Library Catalog
```

### Pattern 2: Step Naming Convention

Steps should be generic and parameterized. Entity names come from parameters, not hardcoded:

```gherkin
# GOOD — reusable across any entity
Given a "Playbook" named "FeatureFactory" exists
When the user clicks "Create" button

# BAD — hardcoded to one entity
Given the FeatureFactory playbook exists
```

### Pattern 3: Step Composition in .feature Files

ESM writes scenarios by composing steps from the library like building blocks.
