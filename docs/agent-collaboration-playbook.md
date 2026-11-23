# Agent Collaboration Playbook

How fleet agents deliver work to people — clients, partners, and the owner — without wasted motion. Each rule was learned from a real fleet operation and sanitized for public use. When a new operation teaches a delivery lesson, add it here by branch + PR (never commit to `main`), and record the source operation in the private ops log.

## Delivering work to a person

1. **Reply on the channel the person used.** If someone reaches the owner on a given channel, the answer goes back on that channel. Hunting for an email address, then for a go-between, costs extra sends and at least one bounce. Do not route through third parties unless the owner asks.
2. **Links over attachments.** Never attach a large file when a view-only link will do. A big attachment turns one approval into an unreviewable payload; a link stays revocable (drop the share permission) and keeps the approval prompt small.
3. **Keep approval friction low.** Every approval prompt that forces the human to scroll a huge payload trains them to say stop. Batch small approvals, prefer links, and never put a megabyte-scale body in front of the approver when a reference works.
4. **A sent message cannot be recalled — plan the rollback before sending.** View-only shares can be withdrawn; emails cannot. Record which is which in the ops-log rollback section.

## Research fan-out

5. **Test outbound access before planning lanes.** Confirm the environment can reach the target hosts before fanning out research; get network approval first, not mid-run.
6. **Budget the search cap across lanes.** A per-turn search budget covers a limited number of parallel lanes; run registry and reputation lanes first, and record blocked checks as UNKNOWN rather than dropping them silently.
7. **Never ship before every lane reports.** Late evidence can overturn a scored finding. A completeness check must confirm every gap-fill lane has landed before the deliverable is finalized.
8. **Ask "did the subject sell, merge, or leave a company?" in every harvest.** Affiliation changes are the most commonly missed fact and the most embarrassing to get wrong.

## Identity and attribution

9. **A matched name is not identity.** Identity rests on attributes (the person's own domains, confirmed affiliations), never on a name match alone. Same-name records stay PROBABLE until the subject or a primary source confirms them.
10. **Never assert an "exit" in our own voice.** Pin any claim about someone leaving a company to a quote or to the company it names, and say "their site does not state their current role" when the record is silent.
11. **Correct the record, don't adjudicate it.** An unsourced, anonymous public-wiki label is presented as a record to correct — not as true or false — and any edit waits for the subject's consent with conflict of interest disclosed.

## Privacy and packaging

12. **Crop private fields from screenshots before use.** A text scan does not see pixels; OCR every embedded image against the do-not-print list.
13. **Scan what ships, not what you wrote.** Check link URIs, decompressed document streams, metadata, and every client companion file for private strings — not just the visible text.
14. **Withhold private locators from client packages.** Internal row references, sandbox paths, and internal lane codes are stripped or replaced before anything leaves the team.

## Engineering hygiene

15. **Check what serves a site before writing a fix.** A plugin-level patch never reaches production if the live site is a static export; fix the export path and the source together.
16. **Keep correction tables duplicate-free by construction, not by care.** A data structure that silently keeps only the last of two equal keys will drop a correction without warning; reject duplicates loudly at build time.

---
*Source: distilled from November 2026 fleet audit operations (details in the private ops log). Proposed by the weekly fleet-librarian review, 2026-11-23.*
