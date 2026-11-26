---
{
  "title": "Our own copy is never a source for a claim about someone",
  "severity": "error",
  "captured": "2026-11-24",
  "captured_from": "Dennis Yu, Claude Code session, 2026-11-24: client personal-brand audit run (client not named); unsupported credentials first written in our agent's site copy were repeated by our own articles as if sourced",
  "applies_to": [
    "agent-behaviour",
    "design-review"
  ]
}
---

## Our own copy is never a source for a claim about someone

- **Before you repeat a credential, award, title, number, price or result about a person or
  client, find where the claim first appeared.** Check the subject's own dated words, public
  records and independent coverage, and also our own drafts, project threads, site copy and
  published pages. If the earliest appearance is something our team or an agent wrote, the
  claim is **self-sourced** until an independent record, or the subject's own dated and
  attributable statement, supports it.
- **Our pages never corroborate each other.** Ten of our pages repeating a line are one source,
  not ten. A client site that we wrote, a schema block we generated, an article that cites our
  own article and a case study that quotes our own copy all count as that same one source.
  "Every figure is public and verifiable" must never sit next to a self-sourced figure.
- **Record the trace in the evidence ledger:** the earliest locator and date, who wrote it, and
  the independent support (or UNKNOWN). A self-sourced claim can be OBSERVED (the page says it)
  but its evidence state is never VERIFIED. Put every surface that repeats it in one
  `contradiction_group`.
- **When a self-sourced claim is live, retire it everywhere it spread, not just on one page.**
  List each surface: our sites, the client's site, schema, articles, case studies, image files
  and their sitemap entries, feeds and final PDFs. Correct the ones we own in the same run, under
  existing authority. Stage the client-property fix for the client's OK. Then run the batch
  retired-claim check (`scripts/audit_report_contract.py --batch`) on every final artifact. A
  report that must quote the retired line to retire it declares a counted
  `retired_quote_allowance` with its reason, and a reviewer confirms each quote is framed as
  retired.
- **Ask the subject once what they meant, and offer the public-record wording meanwhile.** A
  self-sourced claim may come back only as the subject's own attributed statement, after their
  written confirmation.
- **Why:** an audit in November 2026 found an exit size, an award and a "main stage" credential
  stated as plain fact on a client's site, and four of our own articles repeated them, one beside
  the sentence that every figure was public and verifiable. No public record supported them. We
  first traced them to an agent-written site update and believed the subject had never said
  them. A later check of an older public video, on our own channel, found him saying all three
  himself, unverified. That check first reported two, because the award phrase was split across
  two caption lines. Both halves are the lesson: our copy turned an unverified self-description
  into fact, and the trace was not finished until every recording and draft had been searched as
  joined text, not line by line. Retiring the lines took two publication runs across three
  domains, plus an image file and its sitemap entry.

No honest regex can trace where a claim first appeared or decide whether a quote is framed as
retired. Enforce this rule in `evidence-verification`, in the audit acceptance tests and in the
batch retired-claim check. Reviewers judge the framing.
