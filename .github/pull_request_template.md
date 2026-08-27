## What changed

<!-- Name the skills, bundles, docs, or automation changed. -->

## Why

<!-- Link the failure, request, or evidence this fixes. -->

## Propagation impact

- [ ] No skill or bundle names were changed
- [ ] `lss-everything` contains every directory under `skills/`
- [ ] Shared rules were synchronized into every distributed skill
- [ ] Any rule this work taught us is captured in `standards/` **in this PR**,
      with `captured_from` naming where it was said
- [ ] Scheduled jobs using the affected skill names were checked

## Proof

- [ ] `python3 scripts/sync_shared_rules.py --check`
- [ ] `python3 scripts/fleet_check.py --self-test`
- [ ] `python3 scripts/validate_marketplace.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `npx -y @anthropic-ai/claude-code@latest plugin validate .`
- [ ] Fresh-chat activation test (if behavior changed)
- [ ] First scheduled run observed (if a schedule changed)

Evidence or receipts:

<!-- Paste timestamps, output links, screenshots, and the tested commit SHA. -->
