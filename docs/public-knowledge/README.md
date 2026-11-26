# Local Service Spotlight public knowledge graph

This folder is the public map of the knowledge Local Service Spotlight deliberately wants humans, search engines, AI systems and agents to be able to find, cite, reuse and improve.

It does **not** mean "dump every private file on the internet." The public layer contains methods, evidence that is already public or cleared for public use, public relationships and credits, public case studies, public training, public agent instructions, public entity facts, and public descriptions of how the system works. Credentials, private client data, private calls, private learner records, contracts, unpublished personal information and other restricted material stay out.

## Browse the knowledge

Use the [Knowledge Library](https://if-then-builder-journey.local-servic-8436.chatgpt.site/knowledge/) to find a method, public source or useful next action. It connects the existing IF/THEN Builder Journey with the maintained knowledge owners; the source pages and repositories remain the places to cite and improve the work.

| View | What it helps you find |
|---|---|
| [Source directory](https://if-then-builder-journey.local-servic-8436.chatgpt.site/knowledge/sources/) | Existing method hubs, task recipes, training sources, Spotlight sites, public relationships and proof |
| [Agent entry](https://if-then-builder-journey.local-servic-8436.chatgpt.site/knowledge/for-agents/) | Source IDs, provenance and the route from a question to its maintained owner |
| [Knowledge catalog JSON](https://if-then-builder-journey.local-servic-8436.chatgpt.site/knowledge/catalog.json) | The site's derived public browse projection, with links back to canonical sources |
| [Public video index JSON](https://if-then-builder-journey.local-servic-8436.chatgpt.site/knowledge/videos.json) | Existing public video entries and their source links |
| [Public video library](https://if-then-builder-journey.local-servic-8436.chatgpt.site/library/all/) | The same video entries in a browsable human view |

The library groups destinations without replacing the source catalog's IDs. Its video index reuses the existing public library; an entry is source metadata, not a claim that the recording was reviewed or that a learner completed it. Source revisions and coverage are recorded in the published views.

## Why this exists

Local Service Spotlight has several kinds of knowledge that were historically easy to separate:

- long-form articles and canonical concept pages;
- local-service Spotlight sites by category;
- course material and training;
- one-minute videos, podcasts and interviews;
- public proof and case studies;
- public people/company/entity relationships;
- agent skills, runbooks and quality standards;
- the IF/THEN "choose your own adventure" recommendation system;
- AI Builder and operator journeys;
- local SEO execution and measurement.

The public knowledge graph connects those pieces so a person or agent can start from a question and find:

**entity → claim → evidence → method → action → proof → next step**

The public web is the collaboration surface. Private systems remain the execution and evidence surface where required.

## The operating model

### 1. One canonical owner per idea

A topic has one canonical owner whenever possible. Supporting pages, Spotlight vertical pages, courses, videos and social posts should point to that owner rather than create competing versions.

The maintained public registry is [canonical-masters.json](../canonical-masters.json).

Examples already in the registry include:

- Content Factory
- SEO Tree
- Article Guidelines
- Entity Linking
- Nine Triangles
- Dennis Yu podcast appearances

When a duplicate is found, reconcile unique evidence into the canonical owner and turn the duplicate into a supporting page, archive, or redirect only after the owning function approves it.

### 2. Publish evidence, not just assertions

A public claim should answer:

- What is being claimed?
- Who or what is the claim about?
- What evidence supports it?
- Where did the evidence come from?
- When was it checked?
- What is still unknown?
- What action should the reader take next?

A polished page without provenance is not a knowledge asset.

### 3. Training is a view over the same knowledge

Courses should not become a second source of truth.

A Skool lesson, Academy lesson, workshop or certification gate should point back to the public canonical method or evidence page when that information is public. The lesson adds sequence, exercises, accountability and proof requirements.

That means a method can be:

- discoverable on the open web;
- taught inside Skool;
- executed by an AI Builder;
- reused by an agent skill;
- applied on a Spotlight site;
- measured through client results;

without maintaining five unrelated versions.

### 4. Spotlight sites are vertical views of the graph

A vertical Spotlight site should not invent a separate universe of methods.

It should reuse the same public entities, methods and proof, but change:

- the category;
- the examples;
- the people;
- the services;
- the local queries;
- the language and visuals;
- the lead path.

A roofing page and an HVAC page may both teach the same entity-linking or Content Factory method while showing different category proof.

### 5. Public relationships are first-class entities

Public relationships may include:

- podcast appearances;
- interviews;
- conference participation;
- co-created content;
- public client case studies;
- public partnerships;
- public mentorship or apprenticeship stories;
- public citations and credits.

Publish what the evidence supports. Do not turn a public interaction into an unsupported claim of friendship, endorsement, customer status, investment, or partnership.

### 6. Agents read the same map humans do

The human pages and the machine-readable catalog describe the same public topics.

Useful public agent surfaces include:

- this repository;
- [llms.txt](../../llms.txt);
- [agent-setup.json](../../agent-setup.json);
- public skills;
- public canonical-master registry;
- public HTML/article pages;
- sitemaps and internal links on the websites.

Private repositories may hold implementation records, access routes and unpublished evidence. Public agents should never need those private stores merely to understand the public method.

## Core knowledge families

### Content and authority

- [Content Factory](https://blitzmetrics.com/content-factory/)
- [Article Guidelines](https://localservicespotlight.com/article-guidelines/)
- [Entity Linking](https://blitzmetrics.com/entity-linking/)
- [SEO Tree](https://blitzmetrics.com/seo-tree/)
- [Nine Triangles public locator](https://blitzmetrics.com/nine-triangles/)
- [Knowledge Graph Explorer](https://localservicespotlight.com/knowledge-graph-explorer/)

### Builders, training and execution

- [AI Builder Program](https://localservicespotlight.com/ai-builder-program/)
- [Install agent skills](https://localservicespotlight.com/install/)
- [Portable agent setup](../../START-HERE.md)
- [Learn → Do → Teach](../agent-setup/LEARN-DO-TEACH.md)
- [How knowledge propagates](../../HOW-KNOWLEDGE-PROPAGATES.md)

### Recommendation and journey logic

- [IF/THEN public method](IF-THEN.md)
- [Spotlight + training integration](SPOTLIGHT-AND-TRAINING.md)

### Spotlight network

The Spotlight network uses shared methods and proof while presenting niche-specific public pages. The mothership is [Local Service Spotlight](https://localservicespotlight.com/). The vertical network should route category-specific users to the most relevant proof, person, method and next action instead of copying generic text across domains.

## Public knowledge object model

Each useful public object should be representable as one of these:

| Object | Meaning | Example |
|---|---|---|
| Entity | A person, business, place, concept, tool or program | Content Factory |
| Claim | A specific statement about an entity | "Content Factory has four stages" |
| Evidence | Public support for a claim | article, video, case study, source document |
| Method | A repeatable way to do something | entity linking |
| Trigger | A situation that calls for guidance | "If your GBP is suspended..." |
| Recommendation | The action for that trigger | verify/recover before publishing changes |
| Proof | Evidence the action was performed | screenshot, metric, published URL, accepted result |
| Outcome | Whether the larger goal was achieved | more qualified calls, accepted Lighthouse result |
| Relationship | A publicly evidenced connection between entities | podcast guest appearance |
| Journey state | The person's current stage | candidate, apprentice, operator |
| Asset | A reusable media/document artifact | one-minute video, PDF, template |

The machine-readable starter catalog is [catalog.json](catalog.json).

## Public vs private boundary

### Publish by default when cleared

- methods and frameworks;
- public articles and public videos;
- public case studies with permission;
- public professional biographies;
- public event/podcast credits;
- public training instructions;
- public software/agent instructions;
- public category examples;
- aggregated or intentionally public outcome metrics;
- public source links and citations.

### Keep private unless specifically cleared

- passwords, tokens, cookies or login routes;
- private learner identity/progress;
- private client records and CRM data;
- unpublished client financials;
- private calls or meeting transcripts;
- unreleased media;
- contracts;
- private addresses, phone numbers or other personal data not intentionally public;
- internal accusations or sensitive personnel notes;
- security findings that would increase risk;
- anything whose rights/permission are unresolved.

UNKNOWN stays UNKNOWN. "No recorded restriction" is not the same as public permission.

## Publication loop

1. **Discover** a useful fact, method, proof or relationship.
2. **Resolve** the canonical topic/entity owner.
3. **Verify** the evidence and publication rights.
4. **Normalize** it into entity/claim/evidence/action/proof fields.
5. **Publish** or improve the canonical public page.
6. **Link** related Spotlight pages, courses, videos, social posts and agent instructions back to it.
7. **Distribute** derivatives through the Content Factory.
8. **Measure** search visibility, AI citations, referral traffic, leads and completed actions.
9. **Learn** from outcomes and update the canonical owner rather than start another silo.

## Search and AI discoverability

The public layer should be technically ordinary and crawlable:

- stable HTTPS URLs;
- descriptive titles and headings;
- crawlable internal links;
- XML sitemaps;
- canonical URLs;
- useful text in HTML, not only video or images;
- source citations;
- public author/entity pages;
- relevant structured data where supported;
- descriptive images and video metadata;
- no accidental `noindex`;
- explicit crawler policy rather than bot-blocking by accident.

Search/AI optimization is not a separate writing genre. The objective is to make genuine knowledge easy to crawl, understand, verify and cite.

## Contribution rule

When you learn something useful:

**update the existing canonical object first.**

Create a new object only when it is a genuinely distinct entity, method, trigger, proof, or relationship.

That is how the public web, the training, the agent skills and the delivery system become one accumulating asset instead of four departments maintaining four memories.
