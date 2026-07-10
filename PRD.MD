# Context
Yggdrasil is a part of the FeatureFactory Family of the systems.
FeatureFactory is a framework to build AI-native organizations.
There is human factor - building Octopus organization; has nothing to do with the software - pure culture and org. design. It all starts with the "nerve ring" team building a platform and Playbooks how to use it for the "arm" teams.
Mimir is the system to store, serve, and evolve playbooks - via PIPs.
All projects run by the "arm" teams are tracked by Hugin - who can access Playbooks, spot deviations and/or failures, and direct Human attention there.
But are these projects meaningful for the organization? To set priorities and focus attention we need to understand who do we serve, what is our value chain, which capabilities we already have and which we do not, which systems/processes/org. units we have for this, which apps they use, which data they provide, what infra components these app rely upon, which technology stacks we employ for this, which suppliers provide them etc.

*Yggdrasil gives leadership a single source of truth on the organization's value chain, capabilities, enabling systems etc. — so every strategic decision and investment is grounded in what actually exists, not what people assume. 
For organization's AI Yggdrasil feeds the the full picture of what it is and what it can do — unlocking a depth of context no human team could hold, and a quality of work no individual could achieve alone.*

Essentially its AI-maintained knowledge repository - what we have, what we can do, whats its current state etc. It follows certain metamodel (Zachman, TOGAF etc) to organize this information, essentially enabling enabling Model-Driven-Engineering (MDE) for the AI operating as an agent or as an assistant in Agentic Development Environment (ADE).

# Personas & their Jobs to Be Done (JTDs)

## Organizational Level

### Technology sunset/sunrise roadmaps
### Cost Breakdown Structure - by Vendor, 

## Program / Portfolio Level

## Project Level

## Team Level (multiple teams in a big project)


## IT Management
### Replace application/stack

# Data coming from

1. Ratatosk scanning CMDB
Reads ServiceNow, OpenView whatnot -> identifies assets, their repos, metamodels used, current state of the artifacts (think: "this project uses C4 to capture System Architecture Overview; Components are fine but everything else is missing") -> launches subagents to discover gaps and bring Models into shape.

2. Ratatosk scanning unstructured dumps
Scan Confluence/shared folders/email boxes etc -> maps them into the metamodel used by organization: reconstructs value chain, org chart, capabilities, tech stacks etc.

3. Ratatosk scanning GitLab/GitHub/Jira
We can discover both assets and their current state from there - for codebases with the high fidelity, with the issues - more or less high (depends on the state of the issues - details, how stale they are etc.), infra components (where pipelines deploy etc.)

4. Ratatosk agent inside the CICD pipelines
Works well when the landscape is already mapped - reads whats going on inside the incoming changes, reconciles against metamodel used in the Project (example: OpenUP and its static and behavioral representations), decides what needs to be updated (example: Component View, Screen Flow View), plans what exactly has to be updated (example: add "Apply humbling" button to screen X, add modsToolbar to the Component View).








# The flow



# Key features