# Contributing safely

This repository is the canonical source for the Local Service Spotlight Claude marketplace.
A green-looking agent report is not proof that a change reached a user or ran on
schedule. Changes therefore move through a branch, automated checks, review, and
an acceptance receipt.

## Never upload directly to `main`

Do not send contributors to GitHub's `/upload/main` page and do not choose
**Commit directly to the `main` branch**. That route can replace the canonical
files without validation or review.

Instead:

1. Create a branch such as `skill/<short-name>` or `fix/<short-name>`.
2. Add or edit files on that branch.
3. Open a pull request using the repository template.
4. Wait for all validation checks to pass.
5. Review the diff, then merge.
6. If behavior or distribution changed, complete the relevant checks in
   [ACCEPTANCE.md](ACCEPTANCE.md).

For recurring distribution, follow
`skills/skill-registry/references/update-contract.md`. The GitHub commit is the
release identity; a ZIP filename or modification date is not.

## Adding a skill

1. Add `skills/<skill-name>/SKILL.md`. The directory and frontmatter `name` must
   be the same stable kebab-case value.
2. Add `./skills/<skill-name>` to `lss-everything` in
   `.claude-plugin/marketplace.json` and any appropriate topical bundle.
3. Do not rename an existing skill or bundle. Treat a rename as a migration:
   audit scheduled prompts and installed copies first.
4. Run the checks below.

## Capturing a house rule

**A rule that lives only in an article is a rule the next agent will break.** The
black-button rule was published on 17 May 2026 and broken by an agent holding the
whole pack in context on 15 August 2026, because it was never in `standards/`.

When anyone states a rule — the account owner, a client, an audit, or your own
failure — capture it in the same session:

```bash
python3 scripts/new_standard.py "No autoplay with sound" \
  --from "Dennis Yu, Cowork session, 2026-08-16" \
  --applies-to published-html
```

Then write the rule, add machine checks if an honest one exists, and sync:

```bash
python3 scripts/fleet_check.py --self-test    # proves the checks actually fire
python3 scripts/sync_shared_rules.py          # stamps generated rules into scoped skills
```

`--from` is required. Provenance is how we see which channels leak: if a source
never appears in `captured_from`, that source is not being captured.

Adding a rule is a file drop — no code change, no bundle edit. Plain language
walkthrough: [HOW-KNOWLEDGE-PROPAGATES.md](HOW-KNOWLEDGE-PROPAGATES.md).

## Local checks

```bash
python3 scripts/sync_shared_rules.py --check
python3 scripts/fleet_check.py --self-test
python3 scripts/validate_marketplace.py
python3 -m unittest discover -s tests -v
npx -y @anthropic-ai/claude-code@latest plugin validate .
```

Shared house rules live under `standards/`, one file per rule. After changing
one, run `python3 scripts/sync_shared_rules.py` to update the self-contained copy
inside every applicable distributed skill. Never hand-edit a generated block;
validation rejects missing or stale copies of every applicable rule according
to each skill's declared scope.

`--self-test` runs each rule's machine checks against the passing and failing
samples in its own header. A check with no bite is the failure mode that matters:
it reports every site clean forever and looks exactly like a working check.

## What status words mean

- **Available:** present in the merged marketplace.
- **Installed:** visible in the named Claude account or workspace.
- **Enabled:** Claude is allowed to use it there.
- **Tested:** a fresh chat activated it and produced expected evidence.
- **Scheduled:** a job definition exists.
- **Observed:** a scheduled firing produced a timestamped output or failure.

Never substitute one state for another. In particular, `Scheduled` does not mean
`Observed`, and `Available` does not mean `Installed`.

## Release notes for members

Every member-facing notice must name the source commit/version, changed skills,
required sync action, a fresh-chat verification phrase, and the failure route. If a
legacy ZIP is supplied, label it as a snapshot and include the source commit. Never
call a reconstructed or article-derived pack canonical.


## Rendered first-screen acceptance

For a builder or publisher, first select the actual meaningful image, SVG,
video poster or photographic CSS background from source-backed editorial review.
Run the shared checker against the complete preview including site chrome, then
against the anonymous ordinary URL after the authorized release:

```bash
node scripts/rendered_visual_check.mjs --url https://example.com/ \
  --selector 'main .opening-proof img' --output work/first-screen-receipt
```

Use an installed Playwright runtime, or set `PLAYWRIGHT_MODULE` to its absolute
module entrypoint and `CHROMIUM_EXECUTABLE` to a compatible installed browser.
The checker measures 390x844 and 1280x800 with JavaScript on and off, writes four
viewport screenshots and a hashed JSON receipt, blocks media bytes, and never
clicks or scrolls. It returns 0 for geometry pass, 1 for a measured failure and 2
for command/setup failure. **Exit 0 still says REVIEW_REQUIRED.** It does not
prove authenticity, rights, useful crop, diagram correctness or video playback.
Read the actual screenshots and source evidence before accepting the page.

A generator can import `loadPolicy`, `measureVisual` and `auditPage` from the
same module. Keep its source and live receipts separately; invalid source, a
provider save, static refresh, cache state and public acceptance are different
states. Do not make source-order regex output the production success flag.
`standards/visuals-above-the-fold.md` holds the numeric gate so every adapter
uses the same thresholds. A stylesheet may not replace this with a logo count.
No deployment adapter is activated merely by merging this module; record its
exact version and first observed preview/live run in the existing inventory.

The independent reviewer records screenshot hashes, selected visual, authentic
source and permission receipt, relevance/crop/label verdict, money-page proof
and public Money Tree verdict. Opaque iframe boxes and consent-blocked players
require a verified visible poster or explicit screenshot/player review; a CSS
background must be a real relevant photo. All media testing remains muted with
volume zero, including any separate playback test.

The same first-screen pass requires one readable H1/level-one heading line
(18px minimum, 90% visible). CSS background measurements account for opaque
descendant and before/after layers, including overlays that ignore pointer
events. Transparent text and light tints may coexist with the photo; retain
the actual screenshot review for crop, legibility and complicated compositing.
