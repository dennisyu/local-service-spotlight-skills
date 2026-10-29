# How knowledge propagates here

If you want your agents to inherit a useful lesson, capture it once, distribute a
versioned update, and test it in the receiving runtime. This guide explains that
loop. For your first coordinated setup, begin at [START-HERE.md](START-HERE.md).

## The loop we are trying to prove

**A lesson is reusable when another operator can apply it without the author
filling in missing steps.** Publishing instructions is one step toward that result.

| Stage | What to do | Evidence to keep |
|---|---|---|
| Learn | Read the current method, its sources and limits | Method revision and relevant source references |
| Practice | Rehearse with safe public or synthetic inputs | Labeled practice result, failures and corrections |
| Do | Finish an authorized real task against its original criteria | Actual artifact, destination readback and independent check |
| Teach | Explain the successful method, including decisions and failures | Updated canonical guide and a fresh operator's replay |
| Improve | Use a failed check or replay to correct the method | Source change, regression check and tested update receipt |

Learn → Do → Teach (LDT) supplies the learning cycle. Content, Checklists,
Software (CCS) supplies the reusable forms: an explanation, a checkable procedure,
and honest automation. Practice helps learning; a synthetic success does not
establish a production outcome or mastery. The detailed replay method is in
[Learn, Do, Teach in practice](docs/agent-setup/LEARN-DO-TEACH.md).

## Why capture comes first

The original August 16, 2026 account in this repository describes a useful
failure: the black-button rule had been published on May 17, but an agent still
shipped a black button on August 15. The rule had not entered `standards/`, so it
was missing from the generated skill instructions. That historical incident is
the reason for the capture rule; it is not a current audit of anyone's website.

A durable loop has four parts:

| Part | Repository mechanism | What still requires evidence |
|---|---|---|
| Capture | One source file in `standards/`, with provenance and scope | The lesson is correct and the source is permitted for reuse |
| Distribute | Generate applicable copies in `AGENTS.md` and distributed skills | Release, receiver access, account update and fresh activation |
| Check | Run declared software checks and independent review | Actual target coverage, failure cases and unverified judgments |
| Feed back | Correct the master, test and release a new revision | A fresh operator can use the correction in the claimed scope |

## The mechanics, in plain language

**One rule has one maintained source.** Put it in `standards/<slug>.md`. Its
header records origin, date, scope and any supported machine checks. Its body
states what to do, why and how to review it. Amend that master instead of editing
copies inside each skill.

**Skills carry generated copies.** Marketplace packages can contain standalone
skill folders without this repository's `standards/` directory. A rule that only
links to a missing local directory may be unusable there. The sync command embeds
the rule into `AGENTS.md` and the skills whose declared scope applies:

```bash
python3 scripts/sync_shared_rules.py
```

Agent-behavior rules apply to every skill in the manifest. Publishing and design
rules apply only to matching skills. Generated blocks have markers such as:

```html
<!-- shared-rule:no-black-buttons:start -->
<!-- The source rule body appears between these markers. -->
<!-- shared-rule:no-black-buttons:end -->
```

**Validation detects source drift.** The sync check compares the expected blocks
with the copies in the candidate checkout. A stale copy makes that check fail.
Whether a failure blocks a merge depends on the repository's enforced merge
controls. These checks do not inspect every installed package or prove an agent
obeyed an instruction at runtime.

**A merge makes the correction available.** Existing installations still need a
supported update, activation and canary check. A downloaded ZIP remains a dated
snapshot. Do not promise automatic updates to every past installer. Follow the
[update contract](skills/skill-registry/references/update-contract.md) and retain
the previous accepted revision for recovery.

## What one file produces

| CCS form | How the standard is used | Limit |
|---|---|---|
| Content | Its explanation is embedded in applicable skill instructions; an article teaches the method and examples | Generated text is not proof it was loaded |
| Checklists | An operator or reviewer applies its concrete criteria to the work | A checked box is not destination evidence |
| Software | Supported `checks` declarations are consumed by `fleet_check.py` | Only declared checks, reached targets and tested cases are covered |

For this rule-capture workflow, write the **checklist first**, then the teaching
content, then the software check. That order prevents the visible article from
being mistaken for completion. CCS still names the three forms Content,
Checklists, Software; it is not a claim that software can be generated for every
judgment. Timing depends on the rule, tests and rollout, so there is no general
"ten minutes" or "zero minutes" guarantee.

Simple HTML checks can live in the standard's header. More complex checks may
need maintained code, fixtures and review linked from the standard. Shared
provenance helps prevent drift, but the check itself can still be incomplete or
wrong.

## Capture and release a rule

When a client, account owner, audit or failure yields a reusable lesson, first
look for an existing canonical rule. Amend it when appropriate. To create a new
one on a working branch:

```bash
python3 scripts/new_standard.py "No autoplay with sound" \
  --from "Dennis Yu, Cowork session, 2026-08-16" \
  --applies-to published-html
```

This is an example scaffold command, not an instruction to create a duplicate
of the existing [media rule](standards/nothing-plays-uninvited.md). Finish the
body and header before release; validation rejects the scaffold's unfinished
marker. Keep private source records private and publish only the permitted lesson.

Then run:

```bash
python3 scripts/sync_shared_rules.py
python3 scripts/sync_shared_rules.py --check
python3 scripts/fleet_check.py --self-test
python3 scripts/validate_marketplace.py
python3 -m unittest discover -s tests -v
```

Open a pull request, retain required independent review and merge through the
[contribution route](CONTRIBUTING.md). In the release notice name the exact
source revision, changes, required receiver action, fresh-session test and
failure route. Update only accounts and jobs within recorded authority.

`captured_from` is required because provenance makes gaps inspectable. Missing
recording sources warrant a capture audit; they do not by themselves prove how
many calls exist or that no undocumented process ran.

## Prove the check can fail

`scripts/fleet_check.py` fetches supplied targets and applies declared checks.
Its useful property is that it can report a violation, a skipped rule or a page
it could not inspect. Use the supplied target format and keep the output:

```bash
python3 scripts/fleet_check.py --targets fleet.example.txt --json report.json
```

The example target file is an example, not your private production inventory.
An actual fleet sweep requires your approved target list and access.

- **Declared samples:** every supported regex check has clean and violating
  examples. `--self-test` exercises those examples.
- **Independent challenge:** add a reviewer-selected failure beyond the check's
  own samples when practical. Try missing input, a denied fetch or a changed
  markup variant. Never inject a failure into a live customer's page.
- **Scope:** a personal-brand rule need not apply to a product page. Record
  skipped rules and target tags instead of calling the whole site compliant.
- **Unknowns:** failed fetches are not swept. Judgment rules without software
  checks remain for a qualified reviewer. Static markup checks do not prove
  browser behavior, semantic quality, rights or business success.

The original account included a failed `sameAs` target and a clean target from
an August 2026 sweep. Those are historical examples, not current live findings.
Run a new sweep before making a present-tense claim about either site.

## Source, account and job states are different

Use [ACCEPTANCE.md](ACCEPTANCE.md) for the required receipts. Record the claimed
object, source revision, exact runtime/account, timestamp, tester, evidence and
limitations. Do not put credentials or private client data in public receipts.

| State | Evidence |
|---|---|
| Available | Exact merged source or release can be retrieved |
| Delivered | Intended receiver opened the exact artifact revision |
| Installed | Named runtime reports the package/version present, where installation is supported |
| Enabled | That runtime permits use of the installed skill |
| Tested | A fresh task loaded the expected instructions and produced a checked result |
| Scheduled | Saved job definition, owner and next expected firing |
| Observed | Real firing with timestamped output or failure |

These are scoped evidence states, not an automatic progression. A hosted agent
may read a guide without installing a package. A one-off task need not be
scheduled. An observed failure is evidence of a firing, not a successful outcome.
Verify the task's business result separately.

## What remains unproved without new receipts

- Repository sync does not establish adoption by any named outside account.
- A sweep command in a repository does not establish a production schedule or a
  recent unattended firing. Inspect the actual scheduler and run receipts.
- Having a rule in context does not prove obedience. Exercise the relevant
  behavior and inspect the result, as the silent-playback canary does.
- Consistency does not make a rule correct. Preserve dissent, correct the master
  and repeat the affected tests and cold replay.

A useful public report links the released correction, passing and failing
checks, receiver test and limits. It states which claims are still unverified
so the next operator can finish the loop instead of inheriting a success story
without evidence.
