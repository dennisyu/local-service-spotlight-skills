# Tier contract examples and negative controls

These are synthetic exercises. Their PASS fields are invented test inputs, not
actual source inspection, reviewer acceptance, operational calibration or client
results. The [tier annex](tier-contracts.md) supplies the human rules; the
[closed receipt schema](tier-receipt.schema.json) and
[existing decision checker](check_quality.py) supply consistency checks.

| Example | Contract and useful result | Honest state |
|---|---|---|
| Paid personal-brand audit | Agreed 20-page blueprint; proof map, sourced gallery, goal/buyer gap, contradiction register and owned dated actions. Every page has a meaningful visual; every required artifact has exact-hash independent review. | RELEASE_READY only if all original UAQG gates and calibrated threshold also pass; delivery needs its own verified receipt. |
| Free proof-placement diagnostic | Inspect one offer page and a supplied story; explain what it supports and propose a permission-checked placement test. Exclude full brand scoring and revenue attribution. Business-metric baseline UNKNOWN. | Accepted bounded judgments need independent exact-artifact review. A two-page PDF still has two meaningful page visuals. |
| Five-record discovery batch | Validate all five; review flagged records and the recorded seeded sample. Keep every unreviewed record SCREENING. | SCREENING, never five independently accepted audits. Promotion needs a separate product contract and review. |

Run from the repository root:

```text
python3 docs/audit-quality/check_quality.py --self-test
python3 -m unittest discover -s tests -p test_audit_quality.py -v
python3 docs/audit-quality/check_quality.py tests/fixtures/audit-tier-base.json
python3 docs/audit-quality/check_quality.py docs/audit-quality/tier-run-template.json
```

The last command must HOLD. The starter intentionally lacks observations,
authority and review. Supply real evidence in a private receipt; never reuse
synthetic assertions as actual acceptance. The existing checker dispatches the new
schema to additional assertions; legacy1.0.0 inputs retain the original22 controls.
No third-party Python dependency is added. The schema helper supports the closed
subset used here and rejects unsupported assertion keywords; it is not a general
JSON Schema engine. A Draft2020-12 validator can also inspect the JSON schema;
cross-reference and decision checks still require the existing checker.

Negative controls cover missing/empty claims, source locators or author; unknown
claim/status/severity enums; unchecked sources; metadata treated as content; absent
required checks; generic evidence replacing typed receipts; stale review hashes;
missing second-page visual; unresolved identity; wrongly typed closure review;
uncalibrated/wrong totals; changed weights; null/boolean/fractional ratings;
batch-sample mislabeling; unvalidated or unreviewed flagged records; missing access;
exhausted allowance; and unsupported measured-runtime claims. These consistency
tests cannot establish source truth or visual meaning.

Reference-packet names map as `paid_client` → `paid-full`, `free_diagnostic` →
`free-diagnostic`, `high_volume_screening` → `bulk-screening`. Its validator is not
distributed as a second policy/checker. Its assertions are integrated with explicit
population and multiple-artifact review handling. The original six dimension
meanings and weights control numeric acceptance; the annex adds no new score.

Independent-review regression round2 also covers duplicate/conflicting delivery rows in both receipt paths; metadata or ordinary sources substituted for content/access proofs; mismatched recipients/targets; ordinary sources substituted for per-record mechanical validation; stale record hash/scope; one-way finding/action links; unaccepted S2 dispositions in screening; and unresolved or version-mismatched specialist-exam validation. Mobile comparisons stack every row with visible column labels while preserving explicit table/header/cell roles; they need no horizontal scrolling.
