# Evidence ledger

The ledger is the machine-readable source behind the narrative and charts. Use one row per
atomic claim or relationship observation. Do not bury contradictory values in prose.

## Required fields

| Field | What to record |
|---|---|
| `evidence_id` | Stable ID such as `E-001`; never recycle it |
| `subject` | Exact person, organization, asset, channel, claim, or relationship |
| `claim` | One atomic statement; split compound claims |
| `finding_type` | `OBSERVED`, `INFERRED`, or `UNKNOWN` — how the report statement was formed |
| `evidence_state` | `UNKNOWN`, `OBSERVED`, `VERIFIED`, `CONTRADICTED`, or `EXPIRED` — condition of the supporting record |
| `result` | `MET`, `NOT_MET`, `UNKNOWN`, `HOLD`, or `N/A` when the row belongs to an exam or gate |
| `source_class` | Government/registry, first-party, independent editorial, platform/profile, user-supplied, private, or directory/aggregator |
| `data_classification` | PUBLIC, PRIVATE-AUTHORIZED, RESTRICTED, or SECURITY-SENSITIVE |
| `evidence_type` | Registry row, page text, transcript, metadata, screenshot, schema, review, analytics export, social export, or other named type |
| `source_title` | Exact displayed title, not a paraphrase |
| `publisher` | Entity responsible for the source |
| `url_or_record` | Exact public URL or private record locator; never expose credentials or private tokens |
| `event_date` | When the underlying event or statement occurred, if known |
| `published_date` | Source publication date, if known |
| `captured_at` | Audit timestamp with timezone |
| `quote_or_extract` | Short exact excerpt or field value within copyright limits |
| `identity_match` | The two independent attributes used to resolve a person, or `NOT_APPLICABLE` |
| `relationship_basis` | Interview, co-employment, event listing, testimonial, direct user confirmation, or `NONE` |
| `relationship_depth` | Confirmed description or `UNKNOWN`; never derive it from association |
| `source_authority` | Why this source can establish this claim; separate from status |
| `freshness` | Current, historical, stale-risk, expired, or UNKNOWN, with reason |
| `contradiction_group` | Shared ID for claims that cannot all be true |
| `permission` | Public citation, internal only, reuse approved, consent required, or UNKNOWN |
| `export_scope` | Exact artifact/audience allowed, or INTERNAL ONLY |
| `retention_disposition` | Owner, review/deletion date, and deleted or retained state |
| `used_in` | PDF page, score row, chart, action ID, schema draft, or other destination |
| `notes_next_evidence` | Limitation and the exact next record needed |

## Finding, evidence, and result tests

- **OBSERVED:** the cited source directly contains the claim. Phrase it as “the source
  states” when the underlying truth is not independently established.
- **INFERRED:** list two or more evidence IDs when possible and write the reasoning in one
  falsifiable sentence. Do not turn a plausible story into a biography fact.
- **UNKNOWN:** no adequate source or access was available. Record who can answer, what to ask,
  and what action remains blocked. Never assign a numeric zero for UNKNOWN.

An `OBSERVED` self-authored bio is not the same as an independently corroborated fact. Source
class and authority carry that distinction.

Keep the three axes separate:

- `finding_type=OBSERVED` says the row directly reflects a source; it does not by itself
  merit `evidence_state=VERIFIED`.
- `evidence_state=VERIFIED` requires suitable corroboration for that specific claim and a
  resolved identity, not merely a reachable URL.
- `result=HOLD` means a known authority, consent, safety, or contradiction gate blocks the
  action. It is not a score and does not become `NOT_MET`.
- `N/A` means the test does not apply and includes the reason. UNKNOWN means it may apply but
  was not established.

## Identity and collision ledger

Create one identity row before attribution:

| Field | Example shape |
|---|---|
| Candidate | Name + qualifier, never name alone |
| Attribute A | Current employer from source 1 |
| Attribute B | Exact handle, chronology, image, institution, or another identifier from source 2 |
| Independence | Why source 2 is not merely copying source 1 |
| Excluded namesakes | Candidate, conflicting identifiers, URL |
| Verdict | `RESOLVED`, `AMBIGUOUS`, or `NOT_THE_SUBJECT` |

If identity is `AMBIGUOUS`, facts can be inventoried as candidates but cannot be attributed in
the PDF. A prior namesake warning remains dated evidence, not an immortal conclusion; re-test
it against newer primary records.

## Knowledge Graph Explorer and panel receipt

Every audit must query the canonical [Local Service Spotlight Knowledge Graph
Explorer](https://localservicespotlight.com/knowledge-graph-explorer/) and keep these records
separate. Do not compress them into one “Knowledge Panel” field.

| Record | Required value and context |
|---|---|
| `graph_object_status` | `RESOLVED`, `AMBIGUOUS`, `NO_SAFE_OBJECT_RETURNED`, or `UNKNOWN`; include every exact Explorer query, candidate KGMID/result type/description, capture timestamp, and failure. A resolved object cites the two independent identity attributes. Use `UNKNOWN` when the Explorer was blocked or not validly queried. |
| `kgmid` | Exact safely resolved identifier or `UNKNOWN`; never assign the first plausible result by score or name alone. |
| `normal_google_panel_status` | `VISIBLE`, `NOT_VISIBLE_IN_THIS_CHECK`, or `UNKNOWN`, from an ordinary name/name-plus-role query—not a forced `?kgmid=` link—with query, date/timezone, locale/language, approximate location, device/surface, signed-in/personalization state, and screenshot/response locator. |
| `owner_claim_status` | `CLAIMED`, `NOT_CLAIMED`, or `UNKNOWN`; remain `UNKNOWN` without the authorized owner-side Google claim dashboard, a screenshot/export from that dashboard, or a Google claim receipt. Explorer defaults and public controls are not owner-dashboard proof. |
| `association_entity_graph_status` | For each ranked public-association entity, reuse `graph_object_status` and `kgmid`; add identity attributes, dated association evidence, association type, and `relationship_depth=UNKNOWN` unless separately established. |

Human-facing copy may render `NO_SAFE_OBJECT_RETURNED` as `NO SAFE OBJECT RETURNED`,
`NOT_VISIBLE_IN_THIS_CHECK` as `NOT VISIBLE IN THIS CHECK`, and `NOT_CLAIMED` as
`NOT CLAIMED`. The ledger keeps the underscore enums above; the display layer never invents a
different state.

Explorer `resultScore` measures match to that query, not authority and not a percentage. An
Explorer object is not evidence that a normal query renders a panel; a visible panel is not
evidence the owner claimed it. If either surface is blocked or untested, preserve the failed
query/context and mark the corresponding record `UNKNOWN`.

## Connection map rules

Each edge must have `from`, `to`, `association_type`, evidence ID, date, and
`relationship_depth`. Valid public association types include:

- interviewed / was interviewed by;
- appeared on the same named episode or stage;
- worked at the same organization in overlapping roles;
- listed organizer, host, sponsor, speaker, or attendee;
- gave or received a specific testimonial;
- named collaborator on a public project.

Do not upgrade any of these to friend, mentor, partner, client, warm introduction, or
endorsement without direct evidence. An event roster creates many weak edges; rank it below
repeated collaboration and label it **co-presence only**.

## Contradictions and counts

Put every incompatible value in the same `contradiction_group`, with its definition and
date. Common examples are job title, founding year, clients served, placements, revenue,
follower count, pricing, event headcount, and current location.

Resolve a group only when an accountable source defines the metric and cutoff. Otherwise show
the range and keep the public recommendation on hold. Never choose the largest marketing
number or the newest-looking page without a definition.

## Coverage receipt

Record what was actually searched:

- exact name, aliases, transliterations, prior names, handles, and company combinations;
- every language and market the subject has lived or worked in;
- owned site, employer sites, registries, publisher/event archives, podcast indexes, social
  profiles, reviews, and relevant communities;
- date window and result-page depth;
- blocked sources, paywalls, authentication limits, deletions, and timeouts;
- public outside-in sources versus credentialed sources.

“No proof exists” is permitted only after the coverage receipt supports it. Otherwise the
correct finding is UNKNOWN or “not found in the stated search scope.”

For every live search or AI-model observation, also record the exact prompt, provider/product,
model/version when surfaced, query mode, timestamp/timezone, locale/language, signed-in or
anonymous state, location/personalization state, response or screenshot locator, citations, and
any refusal, timeout, or access block. A remembered answer or undocumented run is not evidence.
