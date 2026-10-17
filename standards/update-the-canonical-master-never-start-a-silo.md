---
{
  "title": "Update the canonical master, never start a silo",
  "severity": "error",
  "captured": "2026-10-17",
  "captured_from": "Dennis Yu, Cowork session, 2026-10-17: 'are we updating the existing inventory sheet and the corresponding definitive article that lists all my podcast episodes? or are we perhaps working in a silo and violating the \"SEO tree\" concept we teach? Our hope is that all agents who inventory assets or publish an article check what's already there, so we don't reinvent the wheel.' Follow-up, same session: 'fix the process. consider the 9 triangles (9 principles we operate on), which include LDT and CCS, so we operate effectively as a system.' Incident: on 2026-10-09 an agent was asked to find Dennis's podcast appearances, checked only a 44-item list pasted into the prompt, and delivered a standalone file of '56 new finds'. The canonical hub at https://blitzmetrics.com/dennis-yu-podcast-appearances/ already carried 619 credits across 353 shows; a show-name match on 2026-10-17 found at least 22 of the 56 already on it, and the YouTube pass that was actually requested was never run.",
  "source": "https://blitzmetrics.com/seo-tree/",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Update the canonical master, never start a silo

- **Before you inventory assets or publish a definitive article, hub or list page, find
  the master that already owns that topic, read it, and make your work an update to
  it.** Your output is a delta against the master — added, changed, confirmed,
  dropped — never a fresh standalone list or a second canonical page or tracker for the
  same subject. Supporting pages link up to the master.
- This extends `named-entities-link-to-the-most-helpful-canonical-destination` (one
  topic, one owner in the SEO Tree) from links to whole runs, and generalises the
  in-place rule `positive-mentions-harvester` already applies to mentions inventories.
- **Why:** on 2026-10-09 an agent asked to find Dennis's podcast appearances checked only
  a 44-item list pasted into its prompt and shipped "56 new finds" as a new file. The
  canonical hub already held 619 credits across 353 shows; at least 22 of the "new" ones
  were already on it, and the YouTube pass that was actually requested was skipped.
  Every silo like that is a second count that drifts — the hub itself records that the
  network once carried more than twenty different podcast numbers. A silo also splits
  the SEO Tree: two pages competing for one topic are weaker than one page that owns it.

### Pre-flight, every run, before the first search or the first draft

1. **Resolve the master.** Look up the topic in `docs/canonical-masters.json` in the
   skills repository. If it is not there, or you do not have the repository, search
   whichever of these you can reach before concluding no master exists, and record
   which you could not reach: shared memory, the Canonical Directory and Task Library,
   site search across our domains by title *and* by likely slug (two slugs can serve
   one article), and the Drive or repository the team uses.
2. **Learn it (L of LDT).** Open the live master and read its method, its stated update
   cadence and its source of truth. If the master says the count comes from one place,
   that place is your baseline — not memory, not a number in the prompt.
3. **Treat anything pasted into your prompt as a skin, not the master.** A list,
   count or excerpt in a prompt is a copy that may be stale. Re-derive it from the
   master; if they disagree, the master wins and you report the gap.
4. **Claim the work** in your team's shared work-claims ledger, where one exists, with a
   claim id that names the work and the pass, for example
   `master:<topic-slug>:<pass>:<YYYY-MM-DD>`. If someone else holds it, stop and name
   the holder. If the ledger is unreachable, proceed and say a duplicate is possible.

### Doing the work (D of LDT)

- Deduplicate against the master's **source of truth** (`source_of_truth` in the
  registry), not against its visible table — which may be partial — and never against
  a list you were handed.
- Write your result as a delta that names, for each item, which of these it is:
  already in the master, net-new and verified, candidate needing a check, or dropped
  with a reason.
- Apply the delta **in place**: the master sheet first, then the hub, then every derived
  page (skin) that repeats its numbers, so they all show one number from one source. If
  the master sheet's location is unknown, do not create a new one; record the gap and
  apply the delta to the hub. Where those skills are installed, use `one-master-merge`
  when a second competing copy already exists and `congruency-audit` to confirm the
  master and its skins agree afterwards.
- **If no master exists, you are creating it.** Create exactly one, register it in
  `docs/canonical-masters.json` in the same change, and link it into its SEO Tree
  parent. If you do not have the repository, record the new master's location in your
  run's meta article instead.

### Closing the loop (T of LDT)

- Write the run's meta article and link it to the master.
- If the master's method was missing a step you needed, propose the smallest supported
  fix to the master's method (or its skill) in the same session, under existing
  authority — do not leave the fix only in your run notes.
- Update the master's `last_verified` in the registry with what you opened and when, or
  record it in the meta article if you do not have the repository. Do not copy the
  master's counts into the registry; that is a second source.

### How this maps to Content · Checklist · Software (CCS)

- **Content** is the master hub and its published method — the thing a reader and an
  agent both learn from.
- **Checklist** is this pre-flight. It is what turns "check what's already there" from a
  hope into a step every agent runs.
- **Software** is the registry file, the skill that owns each topic, and the claims
  ledger. The registry is hand-maintained, not generated, and a congruency audit is its
  only check. A registry entry whose owning skill is not in this repository is a known
  gap and is recorded as one, not papered over.
- CCS reads in build order when the Content already exists, as it did here: the master
  hub is the Content, this pre-flight compresses it into a Checklist, and the registry
  and skill are the Software. `capture-what-you-learn`'s Checklist-first order is for a
  brand-new rule that has no Content yet. Both hold.

### Exemption

None for inventories, definitive articles, hubs or list pages. A one-off answer in chat
that publishes nothing and creates no file needs no pre-flight. A supporting post or
meta article does not need its own master; it links up to the one it supports.

No regex can honestly prove an agent looked for the master before it started, so this
rule carries no `checks` block. It is enforced by being read pre-flight, by the
registry, and by a congruency audit catching two surfaces that publish different
numbers for the same thing.
