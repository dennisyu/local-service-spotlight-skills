# Public knowledge publishing standard

This standard governs what Local Service Spotlight should expose to the public web and how agents should transform internal knowledge into public, citable assets.

## 1. Publication is a transformation, not a data dump

"Publish what we know" means:

> publish the useful, supportable, rights-cleared knowledge contained in our work.

It does not mean exposing raw private systems.

Before publication, classify a candidate as:

- **PUBLIC** — already public or explicitly cleared;
- **PUBLIC_AFTER_REVIEW** — useful but requires source/rights/factual review;
- **PRIVATE** — operational/private information that should not be exposed;
- **UNKNOWN** — publication status cannot be established.

Only PUBLIC material can be automatically distributed.

## 2. Every public page should have a job

A public asset should primarily be one of:

- **canonical concept owner** — definitive explanation of one concept;
- **entity page** — public identity and evidence for a person/company/program;
- **method page** — repeatable process;
- **proof/case-study page** — evidence and result;
- **trigger/recommendation page** — situation-specific advice;
- **vertical page** — category-specific view of a shared method or offer;
- **journey page** — what someone should do at a stage;
- **reference/index page** — routes humans and agents to owners;
- **media page** — transcript/context around a video, podcast or visual asset.

If a page has no distinct job, it is probably a duplicate.

## 3. Canonical fields

At minimum, store:

- `id`
- `type`
- `title`
- `canonical_url`
- `summary`
- `entities[]`
- `claims[]`
- `evidence[]`
- `related[]`
- `audiences[]`
- `verticals[]`
- `publication_status`
- `last_verified`
- `owner_function`

A claim should also carry:

- exact claim text;
- evidence URL(s);
- evidence class;
- date verified;
- caveats/unknowns.

## 4. One source, many derivatives

A public canonical object can feed:

- a Local Service Spotlight article;
- a niche Spotlight article;
- a Skool lesson;
- a one-minute video;
- a YouTube description;
- a LinkedIn/Facebook/Instagram post;
- an email;
- a sales proof packet;
- an agent skill/reference;
- an IF/THEN recommendation;
- an internal QA checklist.

Derivatives should link back to the canonical owner when practical.

Do not manually rewrite the same method from memory for every channel.

## 5. Relationship publishing rules

A relationship edge is publishable only when its public evidence supports the exact relationship label.

Good labels:
- appeared on;
- interviewed by;
- spoke at;
- co-authored;
- featured in;
- client case study (with permission);
- public partner;
- public employer;
- public student/apprentice story.

Bad inferences:
- friend;
- endorsement;
- customer;
- investor;
- partner;
- mentor;

unless the evidence actually supports those terms.

## 6. Course and training rules

Training should reference the public knowledge graph instead of hiding all knowledge behind the course.

Keep public:
- the method;
- the definition;
- public examples;
- public proof;
- the basic next action.

Use the course/community for:
- sequencing;
- exercises;
- accountability;
- private feedback;
- client-specific implementation;
- assessments;
- certification;
- access to people/leads/tools.

This creates inbound search and AI visibility without giving away private client work or scarce support.

## 7. IF/THEN rules

An IF/THEN object contains:

- **IF** — the observable situation;
- **THEN** — the recommendation;
- **WHY** — why this recommendation fits;
- **EVIDENCE** — who/what supports it;
- **DO** — the smallest next action;
- **VERIFY** — how we know the action happened;
- **OUTCOME** — the larger result to measure;
- **NEXT** — where to route after the result.

If the source is a public video, link the exact public source and timestamp when possible.

If the source is private, publish the derived method only when rights and confidentiality permit; do not expose the private recording.

## 8. Spotlight rules

Each vertical should have:

- one clear category identity;
- real category people and proof;
- category-specific service/query language;
- local examples;
- links to shared canonical methods;
- category-specific trigger/recommendation pages;
- measurable calls/leads/outcomes;
- a clear operator/owner.

Avoid mass-generated pages whose only difference is a swapped city or keyword.

## 9. Search and AI technical checklist

For every publishable canonical page:

- HTTP 200;
- self-canonical or correct canonical;
- indexable;
- included in sitemap when appropriate;
- reachable through normal internal links;
- meaningful title/H1;
- visible explanatory body text;
- author/entity context when relevant;
- source/evidence links;
- `datePublished` / `dateModified` where appropriate;
- relevant schema.org markup only when accurate;
- useful image `alt`, dimensions and `og:image`;
- video metadata/transcript when video is central;
- no accidental robots/firewall block for desired search crawlers;
- no secrets/private identifiers in HTML/source.

## 10. Distribution checklist

After canonical publication:

- link from the relevant hub;
- add/update the Content Library;
- add the entity/claim to the machine catalog;
- create one or more short derivatives;
- point niche Spotlight pages at it;
- point relevant Skool lessons at it;
- add to an IF/THEN branch if it answers a trigger;
- update relevant agent skill/reference;
- submit/update sitemap and normal discovery paths;
- measure search/AI/referral/lead behavior.

## 11. Measurement

Measure knowledge as a system, not pageviews alone.

Useful metrics:
- indexed canonical pages;
- canonical pages with verified sources;
- public entity coverage;
- unresolved duplicate-topic count;
- organic impressions/clicks;
- AI citations/referrals;
- mentions/links earned;
- video/social reach;
- actions completed from IF/THEN recommendations;
- qualified local-service leads;
- verified client outcomes;
- builders who progress to the next journey state;
- support cost per successful outcome.

## 12. Correction rule

When evidence changes:

1. update the canonical owner;
2. update the machine catalog;
3. propagate important corrections to derivatives;
4. preserve a dated receipt of what changed;
5. do not silently overwrite material where historical context matters.
