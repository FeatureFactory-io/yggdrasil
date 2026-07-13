# Project Estimation (EST)

## Level 1 SWAG (bootstrap scope)

| Work package | Size | Notes |
|--------------|------|-------|
| ESM (7 activities) | S | UX artifacts |
| DTA + SAO (18 activities) | M | Architecture decisions |
| DSP (6 activities) | S | Process config |
| DCI + DCD (14 activities) | L | EB + CI/CD |
| BSP (8 activities) | M | Django scaffold |
| BPE: graph engine | L | Models, traversal, changeset |
| BPE: CRUDLF + Cytoscape | L | First entity slice |
| BPE: Ratatosk connector | M | GitLab scan |
| BPE: MCP + Chat | M | FastMCP + LLM |

## Risk multipliers
- Bitemporal graph complexity: 1.3x
- EB first-time setup: 1.2x

## Monte Carlo (rough)
- P50 bootstrap to EB staging: 3–4 weeks
- P80: 5 weeks
- P95: 7 weeks

## Sprint close
Initialize rebaseline after first PIN iteration.
