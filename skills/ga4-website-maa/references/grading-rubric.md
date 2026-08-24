# GA4 Report Grading Rubric

**Source:** The team's GA4 exemplar grading rubric. Canonical MAA discipline: `skills/weekly-brand-maa/SKILL.md`.
**Tags:** #framework #ga4 #eval #rubric

How to grade a GA4 client report, for the self-improvement / champion-challenger loop. A- is the publish bar. Canonical A example: `references/exemplar-report.md`.

## Scoring (each pass/fail; an A clears all)

1. **Primary conversion first (named per model).** Opens with a plain-English business pulse leading with the model's headline number (count + mix) vs. prior period, in the client's own word — leads, sales, subscribers, members, or donations — never the internal word "conversion." (Dennis's "M" — the most common miss.) The report must also fit the routed model: an e-commerce report shows products and revenue, not cities and calls; a national business shows no cities/GBP lens.
2. **Data shown, not just summarized.** Real numbers + chart/table for leads-by-source and top pages; every number has a comparison + % change. **Scope:** the comparison requirement binds the leads headline, lead mix, channels, and trend; **pages and cities W&O rows are current-window snapshots** compared via the expected-vs-actual line, not a PoP delta (report-format § Comparison scope). Also fail here on the mechanical misses the lint must catch: a client table that doesn't sum to its headline (no "other" line), a stated numeric band that excludes an in-window value, a count adjective ("singles") that contradicts the pulled counts, or a loss/gain attribution that names a bucket other than the largest mover.
3. **Machinery hidden.** No grades (Clear/Hazy/Opaque), no "reconciliation," "attribution coverage," "conformance," or thread names. Translated to plain English.
4. **Honesty / verification applied.** Anomalies are flagged as "we're checking," not asserted (e.g. the referral/booking-tool flag). Nothing unverified is stated as fact. **Swing-driver check:** if the report explains a material lead swing, the named driver must be the **largest mover** in a type×source×touchpoint decomposition (Phase 2.6), verified against the data, with both comparison sides on the same counting basis. A plausible-but-unverified driver — or one that isn't the biggest contributor — fails (Wexford Legal v1: blamed the giveaway/CTV for a drop that was 76% off-site calls).
5. **Tracking issues translated to action.** Any data-trust problem appears as a plain-language heads-up + a fix, never as a raw flag.
6. **Next-step actions (not work-in-progress).** 2–3 items, each a decisive next-move *recommendation* the data drives ("pause the FB campaign," "shift paid search to interior work"), not a status recap of internal effort ("we're working on X"). Our-side ✅ = a forward commitment phrased as a next step; client-side = named ask. No recaps in the action block.
7. **Start-here close.** One clear next move or open question, not a restatement of action #1.
8. **Tight + tactful, and human-sounding.** Reads in a couple of minutes (calibrate to the exemplar, ~530 words); "still gathering data," never "failing." Must not read as AI-written: em-dashes rewritten out (at most one), and no "it's not just X, it's Y," "fast-paced world," or reflexive "leverage/utilize/delve." A machine-sounding report fails here even with correct numbers.
9. **Prescriptions grounded.** Every recommended fix, named product/feature, and causal mechanism traces to integration-behaviors.md, the run's own pulled data, or an explicit "we'll confirm the right approach" hedge. Invented products, real features prescribed for problems they can't solve, and setup status inferred from absent traffic all fail. Watch causal connectives ("which likely means…", "should give us…") bridging gaps the reference doesn't cover. The grader fact-checks recommendations, not just numbers.

## Penalties (auto-drop below A-)

- **Told a legitimate business it is "out of scope," refused the analysis, or forced the wrong model's lens onto it (cities/GBP on a national e-commerce or audience business) → automatic fail.** The router adapts to every small business; rejection or a mismatched frame is never acceptable. (A no-data/dead-tag escalation is a separate, allowed outcome — that is a tracking-gap memo, not a refusal.)
- Any internal grade/score/thread-name leaks into the client text → fail criterion 3, cap at B.
- A confidently-stated number that the data doesn't support — including presenting the analyst's own derived/reclassified count as a GA4-reported figure, or a table that doesn't sum to its headline undisclosed → fail criterion 4, cap at C.
- An ungrounded prescription (invented product / impossible fix / fabricated mechanism) → fail criterion 9, cap at C.
- Reports "your business is dead" without the pre-flight live-property check → automatic F (the dead-property trap).
- No comparison period on the headline metric → cap at B.

## Grading protocol

Self-grades are systematically lenient (observed: self A- vs external B, B+, C- on the same reports). The self-grade is a first filter only; the grade of record comes from a **fresh-context grader** — a separate model instance or session given only the report, the run's data log, this rubric, the exemplar, and integration-behaviors — that fact-checks every number against the log and every prescription against the reference. Self-vs-external disagreement is logged as a finding.

## Champion / challenger use

Run champion and challenger on a settled-Narrative client (Ridgeline is the clean anchor; Brightline Painting and Wexford Legal are the broken anchors). **Run each variant 2–3 times** — single runs are noise under LLM nondeterminism. Diff against this rubric using the external grader. Promote the challenger only if it scores ≥ champion on every criterion in every trial and strictly better on at least one.
