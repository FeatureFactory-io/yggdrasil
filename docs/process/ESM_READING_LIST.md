# ESM Reading List

Curated reading for the concepts underpinning the **Envision the System (ESM)** workflow (`.cursor/playbooks/edda/ESM/`): personas, user goals/value proposition, user journeys, information architecture, screen-flow/dialogue maps, feature files (BDD/Gherkin), and mockups/prototyping.

Primary source is Manning Publications, per request. Where Manning has no dedicated treatment of a topic, one well-known non-Manning title is listed as a supplement and clearly marked **[Non-Manning]**.

---

## TL;DR — one-book core

**[Design for Developers](https://www.manning.com/books/design-for-developers)** by Stephanie Stimac (Manning, 2023) is the single best match for ESM-02/03/04/06. Chapters 3–5 walk through almost the exact same pipeline as the ESM workflow: user research → personas → goals → information architecture → user flows/journeys → wireframes → mockups → prototypes.

If you only read one book, read chapters 3, 4, and 5 of this one.

---

## Mapped to ESM Activities

### ESM-01 — Establish Conventions
No dedicated chapter needed; this activity is Yggdrasil-specific (Screen ID traceability). For the general discipline of setting shared conventions before design work starts, see the facilitation-setup material in *Collaborative Software Design* (below).

### ESM-02 — Define User Journey (personas, goals, value proposition, journey, screens)

| Book | Publisher | Relevant chapters |
|---|---|---|
| [**Design for Developers**](https://www.manning.com/books/design-for-developers) — Stephanie Stimac | Manning | Ch. 3 *User experience basics*; Ch. 4 *User research* (4.1.2 initial data gathering, **4.1.3 user personas**, 4.1.4 user needs, **4.1.5 defining site objectives: aligning user goals and business goals**); Ch. 5.2 *User flows and user journeys* |
| [**Collaborative Software Design**](https://www.manning.com/books/collaborative-software-design) — van Kelle, Verschatse, Baas-Schwegler | Manning | Business Model Canvas (value proposition framing), Domain Storytelling (actors → your personas), customer journey mapping as input to User Story Mapping |
| *The Joy of UX* — David Platt | **[Non-Manning]**, Pearson | Ch. 1 *Personas*, Ch. 2 *What Do Users Want? (And Where, and When, and Why?)* — the clearest short treatment of personas + user motives available anywhere |
| *Value Proposition Design* — Osterwalder, Pigneur, Bernarda, Smith | **[Non-Manning]**, Wiley/Strategyzer | The Value Proposition Canvas (jobs/pains/gains ↔ products/pain-relievers/gain-creators) — the canonical model behind "value proposition" as a design artifact |

### ESM-03 — Define Information Architecture (design system, layout, navigation, components)

| Book | Publisher | Relevant chapters |
|---|---|---|
| [**Design for Developers**](https://www.manning.com/books/design-for-developers) — Stephanie Stimac | Manning | Ch. 5.1 *Information architecture* (site mapping); Ch. 6 *Web layout and composition*; Ch. 9 *Color theory*; Ch. 8 *Typography* |
| [**Usability Matters**](https://www.manning.com/books/usability-matters) — Matt Lacey | Manning | Component/interaction patterns from a "developer as accidental designer" angle — good companion once you're past IA into concrete UI decisions |

### ESM-04 — Create Dialogue Maps (screen-to-screen flows)

| Book | Publisher | Relevant chapters |
|---|---|---|
| [**Design for Developers**](https://www.manning.com/books/design-for-developers) — Stephanie Stimac | Manning | Ch. 5.2.1 *User flows* — building diagrams of the paths a user can take through screens, directly analogous to `screen-flow.drawio` |
| [**Collaborative Software Design**](https://www.manning.com/books/collaborative-software-design) — van Kelle, Verschatse, Baas-Schwegler | Manning | EventStorming / Domain Storytelling as visual-mapping techniques that generalize to any process/flow diagramming exercise |

### ESM-05 — Write Feature Files (Gherkin/BDD)

| Book | Publisher | Relevant chapters |
|---|---|---|
| [**BDD in Action, Second Edition**](https://www.manning.com/books/bdd-in-action-second-edition) — John Ferguson Smart, Jan Molak | Manning | Whole book, esp. Part 1 (discovery/collaboration) and Part 2 (writing Gherkin scenarios) |
| [**Writing Great Specifications**](https://www.manning.com/books/writing-great-specifications) — Kamil Nicieja | Manning | Whole book — organizing scenarios into a spec suite, refactoring features into abilities/business needs; the most direct match for the CRUDLF `.feature` file conventions used here |
| [**Specification by Example**](https://www.manning.com/books/specification-by-example) — Gojko Adzic | Manning | The seven process patterns behind "specification by example," which is the philosophy Gherkin scenarios implement |
| [**Effective Behavior-Driven Development**](https://www.manning.com/books/effective-behavior-driven-development) — Gáspár Nagy, Seb Rose | Manning | Discovery → Formulation → Automation — useful if the TAF step-library workflow ever needs a deeper pattern catalog |

### ESM-06 — Create Mockups (prototyped screens)

| Book | Publisher | Relevant chapters |
|---|---|---|
| [**Design for Developers**](https://www.manning.com/books/design-for-developers) — Stephanie Stimac | Manning | Ch. 5.3 *Designing your site and application* (5.3.1 wireframing, **5.3.2 UI design and full-color mockups**, 5.3.3 prototyping); Ch. 11 *Test, validate, iterate* |

### ESM-07 — Feed into Implementation
Process/handoff activity, not a design-theory topic — no dedicated reading; see *Writing Great Specifications* Ch. 6 ("the life cycle of executable specifications") for how specs stay alive once implementation starts.

---

## Suggested reading order

1. *Design for Developers* — Ch. 3, 4, 5 (covers personas → goals → IA → journeys → mockups in one continuous narrative)
2. *Collaborative Software Design* — for group facilitation and value-proposition/journey-mapping techniques when working with stakeholders rather than solo
3. *Specification by Example* → *BDD in Action, 2nd Ed.* → *Writing Great Specifications* (in that order: philosophy → practice → file organization) for ESM-05
4. *The Joy of UX* Ch. 1–2 as a fast, non-Manning refresher on personas if `Design for Developers` Ch. 4 wasn't enough

## Notes

- "Design for Developers" is explicitly written for developers who need design fluency without becoming full-time designers — a good fit for an engineering-led workflow like ESM.
- All Manning titles above are available on [manning.com](https://www.manning.com) and via Manning's liveBook (with a MEAP/Pro subscription, or standalone purchase); several have preview chapters (e.g. `livebook.manning.com/book/design-for-developers/chapter-5`).
