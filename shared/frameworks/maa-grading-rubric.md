# MAA Grading Rubric

The standard an MAA is graded against. Used by `google-ads-reviewer`. Written
so a reviewer with no memory of writing the report can apply it consistently.

---

## Precedence: read this before grading anything

The rubric below describes the **default** MAA format. It is the lowest layer
of authority, not the highest. Many accounts deliberately deviate, and a
deviation the client's own spec calls for is **correct output, not a defect**.

Resolve conflicts in this order, highest wins:

1. **The client's metric spec** (`compiled/maa-metric-spec.md`, or whatever the
   deployment's overlay names it). Section order, metric names, which windows
   appear where, top-N rule, voice conventions.
2. **The deployment's shared procedure and overlay files** (for example a
   `maa-generation.md`, a data contract, a `maa-skills-binding.md`). House rules
   on headers, delta sources, output paths, publishing.
3. **This rubric.** Applies only where 1 and 2 are silent.

**If you have not read layers 1 and 2, you cannot grade layer 3.** A reviewer
that flags a house convention as a structural failure is worse than no reviewer:
it trains the team to ignore the review. When the spec and this rubric disagree,
the spec wins and there is no finding.

Two worked examples, both real:

- This rubric says diagnostic metrics (impression share, QS components, CVR)
  belong in Analysis and never in Metrics. A client spec that names
  "Auction Insights" and "Quality Score & Components" as ordered blocks *inside*
  Metrics overrides that completely. Not a finding.
- This rubric says Metrics shows 7D only. A client spec calling for 7D and 30D
  side by side in the leading block overrides it. Not a finding.

Where the spec is silent, this rubric governs.

---

## Grades

| Grade | Meaning |
|---|---|
| **A** | Sendable to a sophisticated client with no edits. Exemplary across the board. Exemplar candidate. |
| **B** | Solid, sendable with minor edits. Most weekly MAAs land here. **B is the ship bar.** |
| **C** | Right structure, one meaningful gap: a missed dispatch, a weak narrative, a mis-prioritized action. |
| **F** | Foundational error: a fabricated or contradicted number, tactics before diagnosis, broken balanced metrics, internal labels or API enums in client copy. |

---

## Severity tiers

Every finding carries a tier. The tier drives what happens next, not the grade.

| Tier | Definition |
|---|---|
| **BLOCK** | Factual or structural error. Objectively checkable against the source data or the spec. Always a real problem. |
| **WARN** | Likely a problem. Fix unless there is a stated reason not to. |
| **STYLE** | Judgment call. Depends on voice, context, intent. Report at most a couple, and never let these dominate a punch list. |

Any BLOCK finding caps the grade at C. A contradicted number, a fabricated
figure, or internal framework language in client copy caps it at F.

---

## Return paths

Every finding is routed, not just described. Routing is part of the finding.

| Path | Use when | Goes to |
|---|---|---|
| **REWRITE** | The defect is in the writing and the data to fix it is already in hand. | The analyzer |
| **REPULL** | The report claims something the available data does not support, or defers a question a mid-cycle pull could answer now. | The analyzer, which pulls and re-answers in the same cycle |
| **ASK** | Only a human can close the gap: lead quality, business context, client intent, whether a target is right. | The human reviewer. **Never** the analyzer. |

An analyzer asked to close an ASK-path gap will produce a confident guess that
is indistinguishable from an answer. Route these to a person or leave them open.

---

## Dimensions

### 1. Framework adherence
- Metrics, then Analysis, then Action.
- Windows used as the spec dictates (default: 7D in Metrics, 30D as supporting
  context in Analysis).
- Campaign level only. No account-level aggregates presented as the analysis
  target.
- Dormant campaigns omitted entirely. Zero or negligible spend in both windows
  means the campaign does not appear anywhere.
- Local Services (LSA) handled per the deployment's rule: omitted by default,
  or included and labeled where a client spec says so. Either is fine; silently
  folding LSA into Search headline math is not.
- Top-N respected. Sorted by spend, the meaningful few, not the long tail.

### 2. Metrics discipline
- The spec's section order and metric names, verbatim.
- Where the spec is silent, the default is the core per-campaign bullets and
  nothing more.
- Conversions broken out by action name when the data supports it.
- Video and Display get the condensed form, not the full breakdown.
- Every number carries its comparison. A bare figure with no delta and no
  baseline is incomplete unless it is genuinely new, in which case that is
  stated.
- Unavailable metrics are marked as unavailable with their expected source.
  Never fabricated, never silently carried forward stale.

### 3. Balanced metrics
- Every claim states its balancing partner. No "CPA improved" without volume.
  No "CTR is strong" without conversion rate. No impression-share gain without
  what it cost.

### 4. Narrative quality
- Analysis opens with the most important diagnostic finding, the why behind the
  numbers, not a recap of last week's activity.
- Paragraphs build toward the actions. A topic list is not a narrative.
- Diagnostic metrics appear with the explanation of what they mean, not dumped
  raw.
- Prior efforts appear as brief supporting context, not as the headline.
- Inferences are labeled as inferences. A plausible read is not a fact.
- Structure is verified from settings and data, never inferred from a campaign
  or account name.
- The weakest area is named plainly, not buried.

### 5. Action specificity
- A small number of real actions, prioritized.
- Each one: what, why (tied to something in Analysis), and expected impact
  where it can be stated.
- **Every action is forward-facing.** Confirmations, observations that a
  previously flagged item stayed quiet, and "we checked X and it is holding"
  belong in Analysis. "Watch X, and if it continues for another week or two,
  do Y" is forward-facing and qualifies.
- One list, owners tagged inline. No per-person sub-sections.
- No padding and no non-actions. "Keep holding budget", "continue monitoring",
  and "no change needed" are Analysis conclusions.
- Structural fixes sequenced before tactics that depend on them. Never
  recommend a tactic that a pending structural change will redo.
- Specific names, specific numbers, specific files.

### 6. Patience discipline
- No action item resting on a single week of noisy data, unless the signal is
  dramatic and obvious or the finding is a foundation break (tracking, bidding,
  geo, structure), which are exempt and acted on immediately.
- Changes made last week are not flagged as problems this week.
- "Worth watching" in Analysis instead of premature escalation to Action.

### 7. Dispatch correctness
- Where the diagnosis tripped a dispatch condition, the action item shows the
  specialist was called, or was staged with enough context to run immediately.
- No action item requires the reader to re-explain the problem to another skill.

### 8. Voice and tone
- Embedded-team voice. "We are seeing", not "your account shows".
- Tactful. "Still gathering data", not "failing".
- **No internal framework vocabulary in client-facing copy.** Tier and check
  labels, "diagnostic ladder", "patience principle", "top-N", "balanced
  metrics", "quarterback dispatch", "quarantine", "gate", "ledger", "watch
  list", "hardener", "claim register", and similar are reasoning tools. The report
  describes the underlying observation in plain English.
- **No API enum names.** `TARGET_SPEND` is Maximize Clicks,
  `MAXIMIZE_CONVERSIONS` is Maximize Conversions. Translate every one.
- No method notes in the body. Data-integrity steps are applied silently.
- Deployment-level style rules (for example a house ban on em dashes) are
  BLOCK-tier, not STYLE, because they are stated rules rather than taste.

### 9. Continuity
- Open threads from the prior report are followed up on.
- Resolved items are marked resolved; new themes are added.
- Context the continuity docs already carry is not re-explained.
- Where a per-client anchor exists (for example a known-good Quality Score
  component read on the highest-spend scored keyword), **this week's report
  matches it.** A contradiction is BLOCK-tier and is one of the highest-value
  checks in this rubric.

### 10. The close
- Names a person and makes a specific ask, or poses the most important open
  question for the coming week, or both.
- Not a restatement of action one.

---

## Auto-fail list

Any of these caps the grade at F.

- A number that contradicts the source data, or a number with no source at all.
- A derived or reclassified figure presented as what the platform reported.
- A recommendation with no metric and no interpretation behind it.
- Account-level totals presented as the analysis target.
- Internal framework or tier labels in client-facing copy.
- API enum names in client-facing copy.
- A Quality Score component named in contradiction of the client's recorded
  anchor, or read off the wrong path (the email-fallback column swap applied to
  MCP data, or omitted on email data).
- Tactics recommended ahead of the structural change they depend on.

---

## Grading procedure

1. Read the client's spec and the deployment's shared procedure files. Note
   every place they override this rubric.
2. Read the source data. Without it, sections 1, 2, 3 and 9 can only be graded
   partially, and the report should say so rather than implying full coverage.
3. Read the report once end to end before writing anything, for narrative and
   voice.
4. Read it a second time against the data, checking every number that can be
   checked.
5. Write findings. Each one carries: dimension, tier, the quoted line at fault,
   what is wrong, the required fix, and a return path.
6. Assign a grade, and state what would have to change to move it up one.

**State your coverage.** If the source data was unavailable, say which
dimensions were graded and which were not. A grade that looks complete but only
covered structure is misleading.
