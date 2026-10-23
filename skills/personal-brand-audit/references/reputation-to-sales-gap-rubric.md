# Reputation-to-Sales Gap Audit — Scoring Rubric

**Status: IN FORCE — Version 1.0.0. Approved by Dennis Yu, 2026-10-22.**

Approval: Dennis Yu approved draft v2 (1.0.0-draft.2) as version **1.0.0** on
2026-10-22, with the calibration protocol (§5) in force. Scores issued under
this rubric are **CALIBRATION-PROVISIONAL** until anchor calibration is
recorded under that protocol.

Drafted by Happy (Muse), revised per independent critique before approval.
Method: AUDIT-METHOD-2026.10.02 (blitzmetrics.com/how-we-audit). Worked
calibrations: the two Gemini pilot proof inventories (§6).

---

## 1. Exam identity

| Field | Value |
|---|---|
| Exam name | Reputation-to-Sales Gap Audit |
| Rubric ID | `reputation-to-sales-gap` |
| Version | 1.0.0 |
| What it measures | **Proof relative to the buyer, offer and sales destination** (method exam table). The distance between the reputation the subject demonstrably has and the belief a specific buyer must reach, at a specific sales destination, to buy a specific offer. |
| Subject | A named person or named principal whose personal reputation carries the offer (the paid-full personal-brand product). A business-entity variant is out of scope for v1.0 (see §7, open question 4). |
| Product tier served | `paid-full` only. Not valid for `bulk-screening` records (which are never an accepted audit) and not valid as a headline score inside a `free-diagnostic` (bounded scope; a diagnostic may cite component findings without a total). |
| Report container | The 20-page blueprint, gated by UAQG 1.1.0. This rubric scores the subject's reputation-to-sales system; UAQG scores the report. The two scores are different instruments and are never combined. |
| Relationship to other exams | A separate exam. It sits alongside Brand Authority (v1.0 per the pinned public contract; the method names v1.1 as current — scores are never trended across versions) and SEO & Growth (seven weighted components, person-site pass 80), and may appear in the same report as separate exam lines with separate receipts. **Scores from different exams are never averaged, blended, or shown as a trend or validation against each other.** A change to this rubric's components, weights, gate, or pass line requires a new version; scores from different versions must not be shown as a direct trend. |
| Use rule | Cite evidence IDs beneath every component score and beneath every satisfied or failed sub-test that carries the score. Do not change the components, weights, sub-tests, gate, or pass line inside a client report. |

**Why this exam exists alongside Brand Authority:** Brand Authority measures the
authority assets a person has accumulated. This exam measures whether those assets —
and the offer they support — actually connect: whether the right buyer, looking in
the places buyers look, can resolve who the subject is, find proof matched to the
decision they are making, understand the offer, and act on it without the chain
breaking. A subject can hold real authority and still leak the sale at any one of
those links. That leak is the gap this exam scores.

---

## 2. Scoring mechanics, evidence classes, and definitions

### 2.1 Counted sub-tests replace interpolation

- Seven components, each scored **0–100**. Each component's score is **computed,
  never judged directly**: each of the four scored bands (25, 50, 75, 100) is
  decomposed into **five binary sub-tests** (§3). A sub-test is satisfied or not;
  the scorer's only judgment is whether the named condition holds, and every
  satisfied or failed sub-test that carries the score cites evidence IDs.
- **Score rule.** Let B be the highest band whose five sub-tests are *all*
  satisfied. The component score is B plus **5 points per satisfied sub-test in
  the next band above B**. If all four bands are fully satisfied the score is 100.
  If no band is fully satisfied, the score is 5 × (satisfied 25-band sub-tests).
  If zero 25-band sub-tests are satisfied and no harm condition (§2.4) holds, the
  score is **5** — the performed-coverage floor — and the basis line must say so.
  (0 is reserved for named harm; see §2.4.)
- Each component carries a fixed **weight** (§4, summing to 100). A component's
  contribution is `score × weight ÷ 100`. The headline total is the sum of the
  seven contributions, **calculated in code from the component scores** — never
  estimated, never adjusted by hand.
- The pass decision is made on the **unrounded** total. Display rounding happens
  after the decision and must not change it (display rule in §5).

### 2.2 Evidence classes — item-scoped, tagged at inventory time

Every proof-inventory item is tagged when the inventory is built, and the tag
travels with the item into every component:

- **SELF-CLAIM** — the item exists only as a claim on a surface the subject
  controls (own site, own profile, own pages). A self-claim proves publication,
  never the result claimed.
- **FIRM-UNATTRIBUTED** — the item is the subject's firm's proof (case studies,
  metrics, credentials, reviews of the firm) in which the subject does not appear,
  or where no primary source publicly ties the subject to the firm in the claimed
  role (see the public-tie rule, §2.3).
- **INDEPENDENTLY CORROBORATED** — the item is confirmed by a source in an
  acceptable corroboration class (§2.5) with a locator a reviewer can re-open.

Class rules:

- A band sub-test may be satisfied **only** by items of the class the sub-test
  names. Where a sub-test names no class, SELF-CLAIM items may satisfy it only in
  the 25 and 50 bands.
- The 75-band and 100-band sub-tests in Components 2 and 6 may be satisfied
  **only** by INDEPENDENTLY CORROBORATED items.
- An item whose status is UNKNOWN, or whose subject match is ambiguous (§2.6),
  satisfies **no** sub-test in any component.
- Unattributed and self-claimed evidence is not worthless — it is how the 25 band
  is earned across this exam — but no accumulation of it crosses into the upper
  bands of the components where the decoupling failure occurred.

### 2.3 Attribution rule and the public-tie rule

- Proof counts toward this exam only where it is publicly attributable to the
  subject.
- **Public-tie rule.** Firm-level proof and firm-platform corroboration count
  toward the subject's components only where a primary source publicly ties the
  subject to the firm in the role claimed — a registry or exchange filing, a
  professional-register entry, or the firm's own roster page presenting the
  subject in that role. Where such a tie exists, firm-keyed evidence (e.g.,
  reviews on the firm's listings) is attributable to the subject and is tagged
  INDEPENDENTLY CORROBORATED or SELF-CLAIM by its source, as any other item.
  Where no such tie exists, the firm's items are FIRM-UNATTRIBUTED and the class
  rules in §2.2 apply to them.

### 2.4 Zero is reserved — harm conditions

A component scores 0 only when coverage establishes an *active harmful condition*
named in that component's harm list in §3 — a state that affirmatively misleads
or blocks the buyer. Verified absence of a capability is scored through the
25-band sub-tests, never 0. Whenever a 0 is given, the scorer names the condition
and its evidence IDs, and an independent second reviewer must confirm it before
the result is final (§5).

### 2.5 Definitions the anchors turn on

- **Audit window.** The 90 days ending on the capture date. "Current" publishing,
  cadence, and activity are judged inside this window unless a sub-test states a
  different period. The window and capture date are receipt fields.
- **Independent corroboration — acceptable source classes.** (i) Records of a
  regulator, exchange, court, or professional register; (ii) the
  credential-issuing institution's own records (university, hospital, certifying
  body); (iii) a third-party platform's own data (review platform, directory)
  captured with a locator; (iv) editorial coverage by a publisher with no
  disclosed commercial relationship to the subject. Never corroboration: the
  subject's or the firm's own pages, surfaces the subject controls, paid
  placements, and syndicated copies of a single origin (ten copies of one press
  release are one origin). This holds for credentials exactly as for outcomes.
- **Checked absence.** Coverage was performed as specified and the thing sought
  was not found. A checked absence is scored through the sub-tests. Only an
  unperformed, blocked, or inaccessible check produces UNKNOWN (§5).
- **Material.** A claim, defect, or gap is material if a buyer relying on it
  could change a decision, or if it changes a band outcome in any component.

### 2.6 Namesake precondition and subject match

Component 1's identity resolution — the named entity tie (a primary-source match
on name + firm/role, per §3 Component 1) — must be completed and recorded in the
receipt **before** any other component is scored. Every evidence item carries the
method's subject-match field. An item whose subject match is ambiguous is
UNKNOWN for its component rather than scored. Evidence gathered against a
namesake is the accuracy failure this precondition exists to prevent; it is not
excused by the collision also being scored inside Component 1.

### 2.7 Evidence ownership — one item, one score

Each evidence item scores in **exactly one primary component**. Other components
may cite the item as diagnosis, without score effect. Concretely:

- Reviews and ratings evidence scores **only** in Component 6. Component 2's
  definition excludes review evidence as score-bearing (it remains a buyer-belief
  input to the gap map).
- Component 4 scores only what the destination *states*; Component 5 only
  whether the path *mechanically works*. Neither imports the other's result.
- Absence of an owned entity home is scored in Component 1. Components 3, 5, and
  7 score the channels, path, and capture mechanics **as they exist** — a path
  to a firm page can still be smooth; capture on a firm page still captures. The
  absence itself is not re-charged in those components.

### 2.8 Scoring receipt

For each component record: rubric ID and version, score or UNKNOWN, coverage
performed, evidence IDs, band reached and the sub-tests satisfied/failed that
carry the score, evidence classes relied on, capture date, and reviewer. For
Component 1, graph identity, visible panel, and owner claim are recorded as
three separate fields. For Component 7, the layers covered and the anchor set
used are required fields. Any 0 score and any identity-gate engagement (§5)
records its second-reviewer confirmation here.

---

## 3. Components

Each component states: its definition, the buyer question, its pinned evidence
frame, its harm conditions (score 0), and its twenty sub-tests (five per band).
A producer may extend a pinned frame — never narrow it — and extensions are
recorded in the receipt.

### Component 1 — Identity Resolution & Entity Clarity — weight 15

**Definition.** Whether a buyer — or an AI assistant advising one — starting from
the subject's name can resolve the subject into one correct, unambiguous entity:
the right person, at the right firm, in the role they claim, with no namesake
collision and no contradiction left standing between sources.

**Buyer question.** *"Am I looking at the right person, and is the role they
present real?"*

**Pinned frame — the minimum surface set.** (S1) the qualified-name SERP (query,
locale, device, and capture time recorded); (S2) the owned entity home or name
domain; (S3) the firm's own roster/about page; (S4) the primary professional
profile (LinkedIn or the category equivalent); (S5) the primary-source register
for the claimed role where one exists (exchange, registry, professional
register); (S6) Knowledge Panel state; (S7) graph-record state (Wikidata/KGMID
or equivalent).

**Harm conditions (score 0).** The subject's main identity surface identifies
the wrong person or firm; **or** a live graph or SERP record merges the subject
with a namesake; **or** the subject is not resolvable to any real person from
the surface set. (A primary-source contradiction of the claimed role is *not* a
Component 1 harm condition in v2: it is scored through the sub-tests below —
chiefly the failed 50-band tests — and it engages the identity gate in §5. The
fact is charged once, as a verdict condition, not twice as score and cap.)

**25-band sub-tests.**
1. At least one surface in the set resolves unambiguously to the subject.
2. The subject's name and claimed firm co-occur on at least one surface.
3. A primary professional profile for the subject exists.
4. The subject is distinguishable from namesakes on at least one surface.
5. At least one surface states a role for the subject.

**50-band sub-tests.**
1. The entity home or firm page **and** one primary profile agree on name, firm,
   and role.
2. Subject-relevant results are at least half of the qualified-name SERP's first
   page.
3. A primary-source register entry confirms name + firm + role — or the receipt
   records that no register exists for this role category.
4. No material title inconsistency stands among the surfaces checked (recorded
   minor staleness does not fail this test).
5. No namesake holds the top result for the qualified name.

**75-band sub-tests.**
1. The entity home ranks first for the qualified name.
2. Titles agree across every surface in the set.
3. At least two of the three identity states are positively evidenced — graph
   record / visible panel / owner claim. The component's basis line states all
   three fields, whatever their state.
4. Person/entity schema with a stable `@id` is present on the entity home.
5. Every owned surface points to one canonical identity (no competing canonical
   domain or profile).

**100-band sub-tests.**
1. All three identity states are positively evidenced.
2. The entity home ranks first for the qualified name **and** for the name-only
   query in the market locale.
3. The schema `@id` is linked to the graph record via `sameAs`.
4. Namesakes are clearly separated on both queries.
5. No stale or contradictory surface exists anywhere in the extended set.

### Component 2 — Buyer-Matched Proof Inventory — weight 20

**Definition.** Whether proof exists that matches what *this* buyer must believe
to buy *this* offer: demonstrated outcomes, case results, credentials, and dated
third-party appearances or publications, attributable to the subject and current
enough to rely on. **Review and rating evidence is not score-bearing here** — it
scores only in Component 6 (§2.7).

**Buyer question.** *"Why should I believe this person can deliver the outcome I
am buying?"*

**Proof types.** (A) demonstrated outcomes / case results naming the subject;
(B) credentials and institutional appointments; (C) dated third-party
appearances, press, and publications attributable to the subject; (D)
institutional or executive record (offices held, filings, registers).

**Public evidence sources.** The audit's proof inventory (evidence IDs with
source, date, subject match, evidence class); case studies and published results
naming the subject; credential and institution records; dated third-party
appearances, press, and publications; the subject's own pages — admissible as
publication, classed SELF-CLAIM.

**Harm conditions (score 0).** Material proof presented to buyers is contradicted
by a primary source (e.g., results claimed for work the record assigns to
someone else) and the claim stands uncorrected.

**25-band sub-tests.**
1. At least one proof item attributable to the subject exists, in any class.
2. At least two attributable proof items exist in the inventory.
3. At least one item is dated, or verified as a current standing record at
   capture.
4. At least one item relates to the offer category being sold.
5. No score-carrying item's subject match is ambiguous.

**50-band sub-tests.**
1. At least one substantive attributable item matched to the offer: a named
   outcome, an issuer-verifiable credential, or a dated third-party appearance.
2. At least one score-carrying item is INDEPENDENTLY CORROBORATED.
3. Score-carrying items are current: dated within five years, or a standing
   record verified at capture.
4. Attributable proof spans at least two proof types (any class).
5. At least one item is findable from the entity home or the firm page.

**75-band sub-tests** *(INDEPENDENTLY CORROBORATED items only)*.
1. Corroborated proof spans at least two proof types.
2. At least one corroborated outcome item is matched to the specific offer and
   buyer.
3. At least one credential or institutional item is verified against the issuer
   or register itself — not a bio page.
4. Corroboration comes from at least two distinct origins.
5. No material attribution or recency gap is recorded against the score-carrying
   items.

**100-band sub-tests** *(INDEPENDENTLY CORROBORATED items only)*.
1. Corroborated items span at least three proof types, including outcomes.
2. Every score-carrying item carries an openable locator.
3. At least one outcome is quantified from a source other than the subject.
4. At least one corroborated item is dated within the audit window, or a
   standing record was re-verified at capture.
5. The proof is presented at the sales destination, and the destination's items
   match inventory IDs.

### Component 3 — Proof Findability & Distribution — weight 15

**Definition.** Whether a buyer who never types the subject's name can still
encounter the proof before deciding: non-name search visibility, and the
channels the buyer actually uses carrying attributable proof to them, currently
and repeatedly. Channels are scored **as they exist**; the absence of an entity
home is charged in Component 1, not here (§2.7).

**Buyer question.** *"Will I ever see this proof before I decide — or only if I
already know the name?"*

**Pinned frames.**
- **Query set.** Constructed from the frozen GCT: at least **six** non-name
  queries — at least three offer terms × at least two market terms (locality
  and/or buyer terms) — recorded **verbatim** in the receipt. A producer may add
  queries, never substitute or drop them after seeing results.
- **Channel set.** Fixed at brief time from the buyer + offer category, using the
  default category sets in Appendix B, and recorded in the receipt. A producer
  may extend it, never narrow it.
- **Cadence window.** The 90-day audit window (§2.5).

**Public evidence sources.** The pinned query set's SERPs (queries, locale,
device, capture time recorded); the subject's content library and its
indexation; video and short-form channels; social/professional profiles and
their publishing cadence inside the window; cross-references between channels
and toward the destination.

**Harm conditions (score 0).** The subject's findable channels actively route
buyers to a namesake, a former employer, or a dead property as the primary
result for offer-relevant queries.

**25-band sub-tests.**
1. At least one channel in the category set carries attributable proof content —
   not merely a bare profile.
2. At least one proof content item exists on a set channel.
3. Activity inside the window on at least one channel, **or** a substantial
   attributable archive exists.
4. No set channel's primary result misroutes (to a namesake or dead property).
5. At least one discovery surface exists beyond name search (topic-indexed
   content, a listing, or a channel archive).

**50-band sub-tests.**
1. At least one channel carries attributable proof with activity inside the
   window.
2. At least one pinned non-name query returns subject or publicly-tied-firm
   proof on the first page.
3. At least two set channels carry proof content.
4. At least one channel cross-refers to another owned surface or to the
   destination.
5. Proof content on the carrying channels is subject-attributable (subject match
   recorded).

**75-band sub-tests.**
1. Publishing inside the window on at least two priority channels.
2. At least two pinned queries return subject proof on the first page.
3. At least one channel shows engagement evidence captured with a locator.
4. All priority channels are cross-linked toward one destination.
5. At least three dated publishing events inside the window across the set.

**100-band sub-tests.**
1. At least three pinned queries return subject proof on the first page,
   including at least one top-3 placement.
2. Dated items appear in each 30-day segment of the window on at least one
   channel.
3. Engagement evidence on at least two channels, each with a locator.
4. Every set channel carries proof and routes to the same destination.
5. At least one non-name asset carries a captured reach metric (views or
   impressions) with a locator.

---

### Component 4 — Offer Clarity at the Destination — weight 15

**Definition.** Whether the sales destination — the entity home or offer page
named in the frozen brief, the page the proof routes to — states, clearly enough
for a qualified buyer to self-select: who the offer is for, what problem it
solves, what the offer is, what the entry step is, and what proof supports it.
This component scores **only what the destination states** (§2.7). Competing
destinations are Component 1 diagnosis, not re-charged here; whether the path
from the destination works is Component 5.

**Buyer question.** *"What exactly am I buying, is it for me, and what happens if
I say yes?"*

**Public evidence sources.** The destination pages themselves; the frozen GCT
frame (goal, buyer, offer) as supplied or labeled INFERRED; consistency between
what the proof promises and what the destination states.

**Harm conditions (score 0).** The destination materially misstates the offer,
the subject's role in delivering it, or the terms. (A destination that does not
exist is not charged here; a dead destination is a broken primary route and is
charged in Component 5.)

**25-band sub-tests.**
1. The destination page exists and loads.
2. The destination names the offer area (services, treatments, or equivalent
   listed).
3. A contact route is present on the destination.
4. The subject is named or presented on the destination.
5. The offer category is identifiable from the destination.

**50-band sub-tests.**
1. The audience is stated or unambiguously targeted.
2. The problem or need is stated.
3. The offer is stated — what is delivered.
4. A next step exists on the page.
5. Supporting proof is present on the destination.

**75-band sub-tests.**
1. The subject's role in delivering the offer is explicit.
2. The entry step is explicit and singular — one clear first step.
3. Proof cited on the page matches inventory items and is attributable.
4. At least one qualifying term is stated (price range, timeframe, capacity, or
   eligibility).
5. Nothing on the destination contradicts the proof that routes to it.

**100-band sub-tests.**
1. The full self-selection set is explicit: audience, problem, offer, entry step,
   the subject's role, supporting proof, and qualifying terms.
2. On-page proof IDs match the inventory items the distribution channels cite.
3. The destination states what happens after the entry step.
4. Differentiation — why this provider — is stated.
5. Every claim about the subject on the destination is consistent with the
   primary sources in the checked set.

### Component 5 — Buying Path Integrity — weight 15

**Definition.** Whether the path from first proof touch to the sales
destination's action — inquire, book, apply, buy — works end to end: every link
present, every step low-friction, no dead end between belief and action. This
component scores **only whether the path mechanically works** (§2.7): a path to
a firm page can score well here while the destination's clarity (Component 4)
and the identity behind it (Component 1) score separately.

**Buyer question.** *"I believe it. How do I act on it, right now?"*

**Public evidence sources.** The destination's calls to action and their targets
(each link checked for reachability and expected content, per the method's link
states); booking/scheduling routes; contact routes (form, phone, messaging);
self-assessment or application steps; response-route evidence where public.

**Harm conditions (score 0).** The primary buying route is broken: the main CTA
errors; the booking route is dead; the only published contact route reaches the
wrong party; **or the destination the proof routes to does not exist.**

**25-band sub-tests.**
1. At least one contact route is live (it resolves).
2. At least one CTA is present on the destination.
3. No checked route errors out.
4. A route is visible on the destination without search.
5. At least one route belongs to the destination's owner (not a third-party dead
   listing).

**50-band sub-tests.**
1. A buyer can complete an inquiry or booking today, end to end, on at least one
   route.
2. The path is completable in at most three steps from the destination landing.
3. A low-commitment first step exists (assessment, intro call, or equivalent),
   or direct booking with stated expectations.
4. Routes are consistent across the destination and the primary proof surfaces
   checked.
5. Every CTA on the destination resolves to its expected content — no dead end.

**75-band sub-tests.**
1. A single obvious primary path exists (one primary CTA pattern).
2. Direct scheduling is live, or a guided first step is live.
3. At least one proof surface hands off directly to the destination action.
4. The post-inquiry expectation is stated (what happens next).
5. The mobile path was checked and works (recorded).

**100-band sub-tests.**
1. Guided first step, direct scheduling, and a confirmation step are all live.
2. Zero broken or misdirected links in the full checked set.
3. A response-time expectation is published.
4. The path works from every priority channel.
5. No unexplained gate (paywall, login wall) stands before inquiry anywhere on
   the path.

### Component 6 — Independent Trust Corroboration — weight 10

**Definition.** Whether the belief the proof asks for is confirmed by parties
other than the seller, in the places buyers check: reviews and ratings on
third-party platforms, independent directories, and third-party coverage — with
locators a reviewer can re-open. The subject's own pages are **not**
corroboration sources for this component.

**Buyer question.** *"Do people who are not selling me something confirm this?"*

**Pinned frame — the platform set.** Fixed per offer category in **Appendix A**.
The set, the queries run, and the capture receipts are recorded in the receipt. A
producer may extend the set, never narrow it.

**Coverage rule (this resolves draft.1's self-contradiction).** This component
is **scored whenever the recorded platform sweep was performed** — the full
Appendix A set for the offer category, swept and recorded. A performed sweep
that finds no attributable corroboration is a **checked absence** and scores
through the sub-tests below (normally in the 25 band). Unattributable
corroboration is not corroboration *of the subject*: attribution is constitutive
of this component, so "corroboration exists but cannot be attributed to this
subject" is a finding the sweep reports — scored as absence of corroboration —
not a reason to mark the component UNKNOWN. The component is **UNKNOWN only when
the sweep itself was blocked or inaccessible** (a platform unreachable, results
not retrievable), and the receipt must name the blocked source.

**Public evidence sources.** The Appendix A platforms for the offer category;
third-party editorial coverage; firm-keyed platform evidence (e.g., reviews on
the firm's listings) counts only under the §2.3 public-tie rule.

**Harm conditions (score 0).** Independent sources materially contradict the
destination's claims (e.g., a pattern of reviews reporting the opposite of the
advertised outcome) and the contradiction is nowhere addressed.

**25-band sub-tests.**
1. The category platform sweep was performed and recorded (set, queries,
   receipts).
2. Every item relied on carries a locator in the ledger.
3. No independent source contradicts the destination's claims.
4. At least one corroboration-adjacent item exists in any class — a self-published
   testimonial or metric, an unrated third-party listing, or an attributable
   review.
5. Subject match is recorded for every item relied on.

**50-band sub-tests.**
1. Attributable reviews or ratings exist on at least one set platform.
2. Review volume is captured with a locator.
3. Rating level is captured with a locator.
4. The carrying platform is one buyers for this category actually check (per
   Appendix A).
5. The corroboration is broadly consistent with the destination's claims.

**75-band sub-tests** *(attributable corroboration only)*.
1. Attributable corroboration exists on at least two set platforms.
2. At least one attributable review is dated within the last 12 months.
3. Attributable volume is non-trivial for the category: at least ten attributable
   reviews across the set.
4. The captured rating level is consistent with the destination's claims (no
   material gap).
5. Negative signal, where present, is visibly answered.

**100-band sub-tests** *(attributable corroboration only)*.
1. At least three set platforms carry attributable corroboration.
2. Attributable reviews exist dated within the audit window.
3. Volume and rating are captured at audit time, with locators, on every
   carrying platform.
4. Independent editorial or directory corroboration exists beyond review
   platforms (at least one attributable item).
5. All corroboration is consistent with the claims; any contradiction is
   resolved or disclosed on the destination.

### Component 7 — Follow-Up Capture & Measurement — weight 10

**Definition.** Whether interest that does not convert on the first visit is kept:
a capture mechanism at the destination, a nurture/follow-up route, and a
measurement loop (Metrics → Analysis → Action or equivalent) that shows whether
reputation is turning into sales over time.

**Buyer question.** *"If I am not ready today, does anything keep this alive — and
does anyone measure whether the reputation is producing sales?"*

**Two layers, two anchor sets.**
- The **public layer** — capture assets on the destination, visible nurture
  content, published review cadence — is scored with the **public anchor set**
  below, whose upper bands are reachable on public evidence alone.
- The **authorized-records layer** — CRM, follow-up sequences, analytics, MAA
  records, supplied under the engagement — is scored with the **full anchor
  set**: the public set's sub-tests apply, except that the dated-review sub-tests
  (50-band test 4; 75-band tests 2–3; 100-band tests 1, 4, 5) may be satisfied by
  dated records in the authorized layer instead of public artifacts; the 75 band
  additionally requires at least two dated MAA-style records with logged
  actions, and the 100 band requires records spanning at least two review
  cycles plus one closed-loop example (metric → analysis → action → re-measured).
- The receipt states **which layers were covered and which anchor set was used**
  (required fields, §2.8). Scores under the two sets are the same exam, but the
  receipt must never let a public-set score masquerade as a full-set one.

**Coverage floor.** This component is UNKNOWN only when the destination itself
could not be inspected *and* no authorized records were supplied. Where the
public layer was inspected, the component is scored on the covered layers under
the public anchor set.

**Public evidence sources.** Capture assets on the destination (lead magnet,
assessment, newsletter, booking reminder); visible nurture content; published
review cadence; the recorded ad-library check for returning-visitor mechanisms.

**Harm conditions (score 0).** A capture mechanism exists but is deceptive or
broken in a way that harms the buyer (e.g., a published assessment that collects
data and returns nothing, against its stated promise).

**25-band sub-tests (public set).**
1. At least one static contact endpoint is live.
2. At least one endpoint sits on the destination itself.
3. No capture asset present is broken or deceptive.
4. At least one non-transactional content asset is reachable from the destination
   (a route for the not-ready buyer).
5. Contact endpoints are consistent across the destination and the listings
   checked.

**50-band sub-tests (public set).**
1. A capture asset exists on the destination (lead magnet, assessment, newsletter
   signup, booking reminder) and is live.
2. The capture asset is reachable within two clicks of the destination landing.
3. A visible follow-up route exists (email list, messaging opt-in, subscription).
4. At least one dated public review/update artifact exists (an MAA-style post, a
   results update, a changelog).
5. The capture asset delivers what it promises (spot-checked to a confirmation or
   a delivered resource).

**75-band sub-tests (public set).**
1. Capture and the follow-up route are connected (capture feeds the route —
   stated or evident).
2. At least two dated public review artifacts exist within the last 12 months.
3. The review artifacts record actions taken, not only metrics.
4. Capture is promoted from at least one proof surface beyond the destination.
5. A returning-visitor mechanism is publicly observable (retargeting or
   remarketing evidence from the recorded ad-library check, or a dated content
   series built for return visits).

**100-band sub-tests (public set).**
1. At least three dated review artifacts exist, with recorded follow-through
   actions.
2. Capture is offered at at least two points (the destination plus at least one
   proof surface).
3. Follow-up route content is publicly visible or described.
4. The review artifacts name sales-outcome metrics (inquiries, bookings), not
   only reach.
5. A dated review artifact exists within the audit window.

---

## 4. Weights

The weights are unchanged from draft.1 — the critique found no defect in them,
and each link of the buyer chain is now charged once (§2.7), which is what the
additive sum assumes.

| # | Component | Weight | One-line justification |
|---:|---|---:|---|
| 1 | Identity Resolution & Entity Clarity | 15 | The gate every later link depends on: proof attached to the wrong or an unverifiable identity converts for someone else, or no one. |
| 2 | Buyer-Matched Proof Inventory | 20 | The exam's core: it measures proof, and proof matched to this buyer and offer is the asset every other component distributes or wastes. |
| 3 | Proof Findability & Distribution | 15 | Proof a buyer never encounters does not exist commercially; discovery is a full link in the chain, not a multiplier on the others. |
| 4 | Offer Clarity at the Destination | 15 | Belief without a determinable offer stalls at the destination; clarity is where reputation becomes a decision. |
| 5 | Buying Path Integrity | 15 | A broken or friction-heavy path voids every upstream point at the moment of action. |
| 6 | Independent Trust Corroboration | 10 | Decisive for skeptical buyers but partially downstream of Components 2–3; weighted below the proof it corroborates. |
| 7 | Follow-Up Capture & Measurement | 10 | Protects future conversion rather than today's; real, but the smallest share of the present gap. |
| | **Total** | **100** | |

**No cap exists in v2.** Draft.1's Unreconciled-Identity Cap (59) is abolished
per F-5: it charged the identity contradiction twice (once inside Component 1,
once against the total) and compressed totals for a purpose — "no pass may stand
on an unreconciled identity" — that a verdict gate achieves exactly. The gate is
stated as a pass condition in §5. The totals in §6 are reported uncapped; where
the gate is engaged, the report says so beside the total.

---

## 5. Coverage, missing data, the pass conditions, and calibration

**Coverage.** Each component in §3 names its required evidence sources and its
pinned frame. A component may be scored only when its required coverage was
actually performed and recorded in the receipt. Coverage performed and finding
nothing is a checked absence and is scored; coverage not performed is not a
score.

**UNKNOWN is null, never zero.** If a required source for a component was
unperformed, blocked, or inaccessible — or the available evidence cannot
distinguish absence from inaccessibility — the component is **UNKNOWN**. It
contributes nothing and is never entered as 0, as absence, or as failure.
(Component 6's coverage rule in §3 is the worked example: a *performed* sweep
finding nothing attributable is a checked absence and is scored; only a
*blocked* sweep is UNKNOWN.)

**INCOMPLETE handling.** If any component is UNKNOWN, the report shows: the
**known subtotal** (the sum of the scored components' contributions), the
**coverage** (the scored components' combined weight, of 100), and the result
**INCOMPLETE** — and it **withholds the total and the pass verdict**. Missing
components are never renormalized into a full score, and no partial-score
denominator is defined for the headline. Evidence and conditional actions
proceed normally; only the headline waits for coverage.

**Component 7 denominator.** Component 7's score is defined over the layers
actually covered, per the method's rule that a partial denominator applies only
where the pinned rubric explicitly defines it; **this section and §3's Component
7 anchor sets are that definition.** The layers covered and the anchor set used
are required receipt fields (§2.8). Component 7 is UNKNOWN only when the
destination itself could not be inspected *and* no authorized records were
supplied.

**GCT frame.** The exam is defined relative to a buyer, an offer, and a
destination, so the frozen-input brief must state the GCT frame and label each
field supplied, INFERRED, or unknown. Where any of buyer, offer, or destination
is INFERRED rather than supplied or confirmed, the result is labeled
**PROVISIONAL — GCT inferred**: components are scored against the inferred
frame, the findings stand, and the sales destination and affected
recommendations stay provisional pending confirm-or-edit, per the method. A
PROVISIONAL result shows the total (when coverage is complete) and a
**provisional line comparison** — "above/below the pass line against the
inferred frame" — and carries **no pass or fail verdict**. On the attendee's
confirm or edit reply, the verdict issues from the same scores without re-audit;
only components the edit materially changes are re-scored. (This is the draft's
stated position, adopted from the independent critique's recommendation; §7
flags it for Dennis to confirm or override.)

**Pass conditions — all five, enumerated once.** A result **passes** only when:

1. Coverage is complete (no UNKNOWN component);
2. The unrounded total is **≥ 80** (the pass line — house parity with Brand
   Authority's 80 and SEO & Growth's person-site 80; the UAQG 85 threshold
   grades the report deliverable, not the subject, and is not a candidate value
   here);
3. **The identity gate is not engaged**: no primary-source contradiction of the
   subject's publicly claimed identity or role stands unreconciled and
   undisclosed (gate preconditions below);
4. **No component is scored 0** — no active harmful condition stands anywhere on
   the buyer's path; and
5. **The GCT frame is supplied or confirmed** — no field material to the verdict
   is INFERRED.

Conditions 3–5 withhold or fail the verdict; they never alter the total, which
is always reported as computed. A result that meets conditions 1–2 but fails any
of 3–5 is reported as the total plus the named condition — e.g., "TOTAL 84.50 —
verdict withheld: identity gate engaged" — never as a pass.

**Identity gate — preconditions.** The gate engages only when **all** of the
following hold:
- The contradiction is tied to *this* subject by **two distinct identity
  sources** (e.g., the subject's own claimed-role surfaces and the contradicting
  primary source), resolving namesakes before any evidence is assigned;
- The captures relied on are dated **within the audit window** (a stale page
  contradicted by current sources does not engage the gate without a currency
  check);
- The subject's own surfaces neither correct nor disclose the contradiction.
Where the contradicting source is a third party's page and the subject has
**departed** that firm, the finding is scored in Component 1 as inconsistency,
and the gate engages only if the subject's *current* claimed role is the
contradicted one — a former employer's outdated roster cannot, by itself,
block a verdict on a business the subject no longer claims. The gate lifts when
the underlying public record is reconciled or disclosed against — a property of
the subject's public record, not of the report that exposes it. **Any gate
engagement requires independent second-reviewer confirmation, recorded in the
receipt, before the result is final (§2.8).**

**Display rule.** Totals display to one decimal, **except** within 2 points of
the pass line, where the total displays to two decimals and the report states
"decision made on the unrounded total" beside the verdict or line comparison —
so a 79.96 never presents as "80.0" next to a non-pass result.

**Calibration protocol.** Until at least three anchor artifacts (a clear fail,
a borderline case, and a strong pass) have been scored and agreed under this
version, every total issued under it is labeled **CALIBRATION-PROVISIONAL** —
a label on the rubric's maturity, distinct from the GCT frame label. For the
production batch: a second reviewer independently scores a random sample of at
least 10% of results (minimum three) **and** every pass-line-adjacent result
(unrounded total within 10 of 80). Divergence of more than **5 weighted points**
between reviewers on any result triggers adjudication against the evidence
before that result is final (mirroring the UAQG calibration tolerance).
Additionally, per §2.4 and the gate rule above, any 0 score and any gate
engagement requires second-reviewer confirmation regardless of sampling.

---

## 6. Worked calibration — the two pilot inventories scored under this draft

Both calibrations score **only** the evidence in the round-3 proof inventories,
classed and discounted where the independent round-3 QA review checked a claim
live and found it untraceable. Both subjects' GCT frames were authored by the
producer rather than confirmed by the attendee, so both results are
**PROVISIONAL — GCT inferred**, and both are **CALIBRATION-PROVISIONAL** (no
anchor artifacts have yet been agreed under this rubric). Sub-test counts are
shown as satisfied/total per band; contributions are computed from the scores,
not estimated. Each calibration closes with what changed from draft.1 and why —
the rubric's own versions are compared here because a calibration's job is to
show the revision's effect; no other exam's score is used as validation
(Appendix C holds the removed cross-exam drafting record).

### 6.1 Bernard Lee Mun Kam — Singapore Paincare

*Inferred frame:* buyer — prospective specialist-clinic patients (and referrers);
offer — interventional pain consultations and treatment at Singapore Paincare
clinics; destination — clinic booking via sgpaincare.com, the clinic GBP
listings, and WhatsApp. *Public tie:* SGX filings name him Executive Director &
CEO of Singapore Paincare Holdings (EV-06), and the firm's own pages present him
— firm-keyed evidence is attributable to him under §2.3.

| # | Component (weight) | Tests 25 / 50 / 75 | Score | Contribution | Basis (evidence IDs) |
|---:|---|---|---:|---:|---|
| 1 | Identity Resolution (15) | 5/5 · 4/5 · — | 45 | 6.75 | Resolution succeeds: SGX filings confirm name, firm, CEO role (EV-06); drpain.sg is an owned entity home (EV-01); LinkedIn exists (EV-07). The 50-band failure is test 2: the recorded SERP "defaults to mixed generic local maps and news hits" (EV-05) — subject-relevant results are not shown to be half the first page. No personal panel (EV-05) and three competing owned domains (EV-01/02/03) are recorded as diagnosis; under §2.7 the competing-domain fact is charged here, in the failed consistency tests, not again downstream. The chococoral collision (EV-08) is a third-party ingestion error, not a contradiction on his surfaces; no gate question arises. |
| 2 | Buyer-Matched Proof (20) | 5/5 · 5/5 · 3/5 | 65 | 13.00 | Corroborated proof across two types: institutional credentials (founded the TTSH pain unit 2002; Women's Pain Centre KKH 2009 — verified live by QA) and executive record (SGX-listed CEO, EV-06). The 75-band failures are tests 2 and 3: no corroborated *outcome* item matched to the patient offer exists in evidence, and no credential was verified against the issuer/register itself. One press item is misnamed in the inventory (Wanbao, not Zaobao — QA R3-B9); it carries no score. EV-15 (no book found) is UNKNOWN and satisfies no test (§2.2). |
| 3 | Findability & Distribution (15) | 5/5 · 3/5 · — | 40 | 6.00 | TikTok @AskPainDoc is an active second channel with evidenced engagement (EV-10; QA verified the account live, one video at 78.1K likes); the YouTube channel exists (EV-09). The 50-band failures: test 2 (no recorded non-name query result exists in the pilot evidence — the frame the pilot never pinned is exactly what §3 now requires) and test 4 (channels are not cross-linked to one home — the pilot's Gap 4). LinkedIn is dormant (EV-07). |
| 4 | Offer Clarity (15) | 5/5 · 4/5 · — | 45 | 6.75 | Scored on the named destination (sgpaincare.com) alone: conditions, treatments, locations, and an appointment route are stated (EV-02/11/12), and he is presented on it (EV-02). The 50-band failure is test 5: no supporting proof is shown to be present on the destination. The three-competing-destinations fact is **not** charged here in v2 (§2.7) — it is Component 1 diagnosis. |
| 5 | Buying Path (15) | 5/5 · 4/5 · — | 45 | 6.75 | The mechanics work today: verified GBP listings with booking hooks (EV-11/12), an appointment form (EV-01), phone/WhatsApp anchors, no recorded breakage. The 50-band failure is test 3: no low-commitment first step exists — generic forms only, no condition-matched assessment (the pilot's Gap 5). Path split across domains is not re-charged here; the routes as they exist were scored. |
| 6 | Corroboration (10) | 5/5 · 3/5 · — | 40 | 4.00 | The sweep was performed; attributable reviews exist on both verified clinic GBP listings (EV-11/12) and are attributable to him under the public-tie rule. The 50-band failures are tests 2 and 3: the rating level and volume the pilot asserts (">4.5 stars") are untraceable in any live index (QA R3-B8) — presence is captured, magnitude is not, and under counted tests that is a precise, bounded deduction rather than a judgment call. |
| 7 | Follow-Up & Measurement (10) | 5/5 · 0/5 · — | 25 | 2.50 | Public anchor set (the only layer covered; the internal layer was not supplied — EV-13 — and the receipt records that). Static endpoints live and consistent; treatment-guide content gives the not-ready buyer a route (EV-03). The 50 band fails outright: no capture asset, no visible follow-up route, no dated public review artifact; paid presence is occasional with no retargeting observed (EV-14). |
| | **Total (uncapped)** | | | **45.75** | Coverage complete (100 of 100 weight). **No verdict** — PROVISIONAL (frame inferred): the provisional line comparison is **below the pass line** (45.75 < 80). Identity gate not engaged; no component at 0. CALIBRATION-PROVISIONAL. |

**What changed from draft.1 (50.00).** The total falls 4.25 points, and every
point of the movement is a counted test rather than a judgment: C1 50→45 (the
SERP-plurality test the v1 anchor asserted but its own evidence contradicted);
C3 45→40 (the non-name-query and cross-linking tests fail on the record as it
stands); C4 50→45 and C5 55→45 (v1 charged the domain split inside both; v2
charges it once, in C1, and scores the destination and the path as they exist —
the counted tests are stricter about proof-at-destination and the missing first
step than v1's interpolation was); C7 30→25 (the public anchor set's 50 band
fails outright — v1's 30 was an interpolation between bands the evidence does
not reach). C2 (65) and C6 (40) hold their v1 numbers by entirely different
derivations: v1 reached C2 by weighing pedigree volume and C6 by interpolating
below its own anchor; v2 reaches both by test counts, with the specific failing
tests named.

### 6.2 Brandon Lock — GET Consulting

*Inferred frame:* buyer — Singapore SME owners considering exit/succession
advisory; offer — GET Consulting exit advisory (EDG/PMC-supported); destination —
getconsulting.sg contact flow. The subject's role is contested evidence: claimed
founder; the firm's own roster contradicts it (EVD-07/08). *Public tie:* **none**
— he is absent from the firm's roster and no primary source ties him to the firm
in the claimed role, so firm evidence is FIRM-UNATTRIBUTED throughout (§2.3).

| # | Component (weight) | Tests 25 / 50 / 75 | Score | Contribution | Basis (evidence IDs) |
|---:|---|---|---:|---:|---|
| 1 | Identity Resolution (15) | 5/5 · 0/5 · — | 25 | 3.75 | Fragmentary resolution — which is what the 25 band *is*: a real LinkedIn resolves to the man himself (EVD-02), name + firm co-occur (corporate email, EVD-01), and he is distinguishable from his namesakes (the Baruch professor) by the firm tie on his own profile. The 50 band fails outright: the firm page and his profile do not agree on role — the roster omits him entirely (EVD-07/08); no register confirms the claimed role; namesakes dominate the name SERP (EVD-13 context). The contradiction is charged here, once, as failed tests — and again nowhere else in the score. |
| 2 | Buyer-Matched Proof (20) | 4/5 · — · — | 20 | 4.00 | His attributable pool is a single SELF-CLAIM item set: LinkedIn professional history and the claimed role (EVD-02). The 25-band failure is test 2 (fewer than two attributable proof items). The firm's proof is real (case studies, published metrics — EVD-11/12, verified live by QA) but he appears in none of it and no public tie exists, so under §2.2 those items satisfy no sub-test in this component — they are diagnosis, and they are strong material for the gap map. |
| 3 | Findability & Distribution (15) | 1/5 · — · — | 5 | 0.75 | One channel, and it carries no proof content: the LinkedIn (EVD-02) is a profile with claims, not proof items; a performed video index check found zero indexed video (EVD-15 — a checked absence); no non-name discovery surface exists. The single satisfied test is #4 (no misrouting). Draft.1's 20 credited the channel's existence; under counted tests, existence without content or discovery is the floor of this component — correctly, since this component's buyer question is about encountering *proof*, and name-search findability is Component 1's question, already credited there. |
| 4 | Offer Clarity (15) | 4/5 · — · — | 20 | 3.00 | Scored on the de-facto destination (getconsulting.sg): it exists, states a clear offer (EVD-06 — "Exit Strategy Consultants"), and carries a contact route (EVD-18). The 25-band failure is test 4: **the subject is not named or presented anywhere on the destination.** The clarity is the firm's; under the §2.2 class rules, FIRM-UNATTRIBUTED destination evidence supports no higher than the 25 band for the subject. |
| 5 | Buying Path (15) | 5/5 · 4/5 · — | 45 | 6.75 | Scored as mechanics only, per §2.7: the firm's route works — homepage "Book a Strategy Session" CTA into a consultation form, plus WhatsApp/Email/Call (EVD-18; the flow was verified live by QA). The 50-band failure is test 4: his one proof surface (LinkedIn) does not present or hand off to these routes. Draft.1's 30 charged him in this component for the missing entity home and missing attribution; v2 charges those facts in C1/C4 and scores the path as it mechanically exists — the rise to 45 is the evidence-ownership rule working, not leniency. |
| 6 | Corroboration (10) | 5/5 · 0/5 · — | 25 | 2.50 | **Outcome reversed from draft.1 — see the change note below.** The platform sweep was performed and recorded (GBP, Clutch, Trustpilot, and LinkedIn recommendation surfaces crawled — the pilot's own exam section; EVD-16/17 record the sweep's outcome). It found no attributable third-party corroboration. Under §3's coverage rule that is a checked absence, scored: the 25 band's tests are met (sweep recorded; items carry locators; no contradicting source; self-published firm metrics exist as corroboration-adjacent items, EVD-11; subject match recorded for every item). The 50 band fails outright: no attributable reviews or ratings exist on any set platform. |
| 7 | Follow-Up & Measurement (10) | 5/5 · 0/5 · — | 25 | 2.50 | Public anchor set (public layer only was covered). Static endpoints live on the destination (EVD-18); case-study content gives the not-ready buyer a route (EVD-12); endpoints consistent. The 50 band fails outright: no capture asset (the scorecard is a plan, not a live asset), no follow-up route, no dated review artifact (the pilot's MAA memo is an undated template, not a review of results). The §2.2 ceiling is consistent with the outcome: the endpoints are the firm's, unattributed, and support no higher than the 25 band. |
| | **Total (uncapped)** | | | **23.25** | Coverage **complete** (100 of 100 weight). **No verdict** — withheld on two independent grounds: (1) PROVISIONAL (frame inferred) — the provisional line comparison is below the pass line regardless; (2) **identity gate ENGAGED** — preconditions met and recorded in §6.2 note below. No component at 0. CALIBRATION-PROVISIONAL. |

**Identity gate record (Brandon).** Trigger: the firm's own roster page credits
John Lin as Founder (2018) and Ming Sheng as Co-Founder and omits the subject
entirely (EVD-07/08), contradicting the founder role the subject publicly claims
(submission and profile surfaces, EVD-01/02). Two-source tie: the subject's own
claimed-role surfaces and the contradicting primary source, both captured within
the audit window (October 2026) and independently verified live by the round-3
QA review — which serves as the second-reviewer confirmation §5 requires for
this calibration. The subject's own surfaces neither correct nor disclose the
contradiction in the evidence. His *current* claimed role is the contradicted
one, so the departed-subject exception does not apply. **Effect:** the total is
reported uncapped (23.25); no pass verdict may issue while the gate stands,
whatever the total becomes on re-audit.

**What changed from draft.1 — owned openly.** Draft.1 returned INCOMPLETE (known
subtotal 16.25 at 90% coverage) and argued at length that Brandon's Component 6
had to be UNKNOWN because coverage "cannot distinguish 'no attributable
corroboration exists' from 'corroboration exists but is not publicly
attributable.'" The critique (F-2) showed that argument is a category error:
attribution is constitutive of corroboration, a performed sweep is a checked
absence, and the method scores checked absences. **Draft.2 reverses draft.1.**
Component 6 scores 25; coverage completes at 100; the result becomes a completed
total of **23.25** instead of an incomplete 16.25. The number rises and the
deliverable gains the headline draft.1 withheld — and nothing about the
subject's position improves: the identity gate and the provisional frame each
independently withhold a verdict, the total sits 56.75 points below the pass
line, and the same evidence that completes his coverage is the evidence that
engages his gate. The remaining component movements are the revision's other
rules working: C1 5→25 (draft.1 scored the contradiction at near-zero *and*
capped the total for it — a double charge its own 25-band anchor text
contradicted, since fragmentary resolution with material title inconsistency is
the 25 band's own description; v2 charges the fact once, as failed 50-band tests
plus the gate); C3 20→5 and C2 15→20 and C5 30→45 (counted tests and evidence
ownership, per-component notes above); C4 20 and C7 20→25 hold or settle at the
bands their tests produce.

---

## 7. Design notes — choices, rejected alternatives, open questions

**Choices carried from draft.1 (unchallenged by the critique).**

1. **Seven weighted components at 0–100, not ten 0–10 rows.** The method's own
   exam set contains both shapes (Brand Authority rows; SEO & Growth's weighted
   components). The buyer path has fewer, heavier links than an authority
   inventory, and the stages are not naturally equal — hence weights.
2. **Components derived from the method's gap taxonomy, not from either pilot.**
   Method step 3 names the gap kinds: missing proof, buried proof, inconsistent
   identity, weak positioning, broken buying path, missing measurement. The
   seven components are those six, with corroboration broken out of "proof"
   because buyers check it separately — cross-checked against the buyer-path
   stages both pilots independently produced (discovery → verification → trust →
   pricing → capture).
3. **Component 7's public-layer coverage floor.** Chosen over the strict rule
   (component UNKNOWN whenever internal records are unsupplied): the strict rule
   makes the exam return INCOMPLETE for every public-evidence audit, including
   all 86 make-whole audits, none of which can supply CRM records. Draft.2 keeps
   the floor and repairs its actual defect (F-9): the public anchor set's upper
   bands are now reachable on public evidence.

**Choices made in this revision.**

4. **Counted sub-tests over interpolation (F-1).** Five binary tests per band,
   +5 per satisfied test in the next band. Scores are therefore multiples of 5 —
   a deliberate trade: granularity a reviewer cannot reproduce is not
   information. The one-sentence-reason discipline survives as the per-test
   evidence citation.
5. **Gate, not cap, for identity (F-5).** The rationale draft.1 stated — "no
   total in the passing range may stand on an unreconciled identity" — is a
   verdict property, so v2 implements it as one: totals are reported as
   computed, and the verdict is what the contradiction blocks. Recorded
   alternative for Dennis: if he prefers a numeric cap for signaling, the
   critique's fallback is a cap at **79** (just below the pass line), with the
   §5 test applying to the capped total and the residual double charge with
   Component 1 acknowledged as an accepted disposition. The draft's position
   remains gate-only.
6. **PROVISIONAL verdicts (Q2).** The draft adopts the critique's recommendation
   as its stated position (§5, pass condition 5): no pass — and, symmetrically,
   no formal fail — on an inferred GCT frame. The total and a provisional line
   comparison are shown; the verdict issues from the same scores on
   confirm/edit. Dennis may override this in the approval commit; if he does,
   the condition is removed and PROVISIONAL results carry verdicts, and the
   change is a versioned decision, not an editorial one.

**Alternatives rejected (carried from draft.1, still rejected).**

- **Reusing the Oct 17 screening components or caps**: barred by the run
  contract; those rows measure findability fragments, not proof relative to a
  buyer, offer, and destination.
- **Copying the legacy Audit Factory five-part exam**: a different product;
  only its disclosure pattern (cap shown separately from the raw total)
  informed draft.1, and v2 needs even that only as the recorded fallback in
  note 5 above.
- **Adopting the pilots' seven components wholesale**: their set double-counts
  distribution (Social and Video as separate scored components) and imports
  channel bias. Video and social are evidence inside Components 3 and 7 here,
  not components.
- **A Knowledge-Panel cap**: double-counting — panel absence already weighs
  inside Component 1's sub-tests (75-band test 3, 100-band test 1).
- **A renormalized "partial composite" for incomplete coverage** (the pilots'
  approach): the method permits partial-score denominators only when the pinned
  rubric defines them. This rubric defines one only for Component 7's layers
  (§5); for the headline it deliberately does not — known subtotal + coverage
  states the facts without minting a score.

**Open questions only Dennis can settle.**

1. **Pass line.** 80 is proposed for house parity. Confirm, or set the Gap line
   elsewhere. *(Blocking in form only: the draft is approvable with 80 as
   written; a different line is a one-word change in the approval commit.)*
2. **PROVISIONAL pass verdicts — DRAFT POSITION ADOPTED, confirmation
   requested.** The draft's position (§5, condition 5): no verdict on an
   inferred frame; total + provisional line comparison shown; verdict issues
   from the same scores on confirm/edit. Confirm, or override to let
   inferred-frame results carry verdicts. This decides the first-run form of
   most of the 86, whose frames will be inferred.
3. **Identity mechanism — DRAFT POSITION ADOPTED, confirmation requested.**
   Gate, not cap (§5; design note 5). Confirm the gate, or direct the 79-cap
   fallback instead.
4. **Subject scope.** v1.0 is drafted for a person/principal. Should the
   approved version also cover a business entity as subject (e.g., a clinic or
   firm audited in its own name), or is that a separate rubric version by
   design?
5. **Corroboration's place.** Is corroboration (Component 6) a scored component
   of this exam, or a hard evidentiary gate on Component 2 (proof counts only
   when corroborated)? The draft scores it (and F-4 removed review evidence from
   Component 2's score-bearing definition, which narrows the overlap the
   question is about). The gate alternative remains defensible and changes
   Brandon-type cases materially.
6. **Approval mechanics.** On approval: the version that enters the skills
   repo — 1.0.0 as drafted, or renumbered — and the standing rule that Gap
   scores **replace** the Oct 17 screening scores in correction reports with no
   side-by-side (cross-contract comparison is a trend the method forbids; the
   draft's position is replace). Confirm both in the approval commit.

---

## Appendix A — Component 6 platform sets, by offer category

Fixed sets. A producer sweeps every platform in the subject's category set (or
records the platform as blocked, per §3's coverage rule), may add platforms, and
may never narrow the set. The set used is a receipt field.

| Offer category | Platform set |
|---|---|
| Local consumer services (clinics, home services, local retail) | (1) Google Business Profile / Maps listing(s) for the subject or the publicly-tied firm; (2) the dominant vertical directory for the category in the market (healthcare: the market's leading practitioner directory; home services: the market's leading trade directory) — named in the receipt; (3) one general review platform (Trustpilot, Yelp, or the market equivalent). |
| Professional services (advisory, agency, B2B services) | (1) Google Business Profile / Maps listing for the subject or the publicly-tied firm; (2) Clutch or G2, whichever fits the category; (3) Trustpilot; (4) the primary professional profile's recommendation/testimonial section, where the platform supports one. |
| Creators, authors, speakers | (1) Google Business Profile / Maps where a listing exists; (2) the dominant platform for the primary medium (book: Goodreads/Amazon author ratings; speaking: the category's speaker bureau/directory); (3) one general review platform (Trustpilot or market equivalent). |

## Appendix B — Component 3 default channel sets, by offer category

Fixed at brief time from the buyer + category; recorded in the receipt; extend,
never narrow.

| Offer category | Default channel set |
|---|---|
| Local consumer services | Google/Maps (GBP content and listings), short-form video (TikTok/Reels/Shorts — the platforms present in the market), long-form video (YouTube), the primary social profile for the market. |
| Professional services | LinkedIn, search-indexed owned content (articles/pages), YouTube/video, the category's professional directory profiles. |
| Creators, authors, speakers | The primary publishing platform for the medium, YouTube/video, one social channel, search-indexed owned content. |

## Appendix C — Drafting record (NOT part of the rubric; not to be reproduced in any report)

*Preserved per F-6 so the drafting history is not lost. Nothing in this appendix
is rubric text, and no report produced under this rubric may cite or reproduce
it.*

Draft.1's §6 closed each calibration with a comparison against a Brand Authority
mapping of the same inventory (Bernard ≈45–55, no UNKNOWN rows; Brandon
INCOMPLETE, known subtotal ≈11–14), presented as mutual validation of the two
exams' impressions. The independent critique (F-6) held that the method — and
this rubric's own §1 — forbid showing one exam's score as a trend or validation
against another's, and that worked examples teach producers house style. The
paragraphs were therefore removed from §6 in draft.2. They are recorded here
solely as drafting history: the observation that two independently built exams
produced convergent impressions of the same two evidence bases was part of why
the drafting lane trusted the inventories; it plays no role in any score,
verdict, or client-facing document.
