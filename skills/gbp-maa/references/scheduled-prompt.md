# Weekly scheduled task — GBP MAA

Create one scheduled task per client in claude.ai (weekly, the morning before the client's report day). Connector required: GBP (gbp_mcp). Paste this as the task prompt and fill the PARAMETERS block.

```
Run the gbp-maa skill for the client below. Follow SKILL.md phases 0 through 7 in order.

PARAMETERS
client: Target Painting & Contracting
client_vault: 02-Clients/Target-Painting
locked_config: 02-Clients/Target-Painting/locked-config-gbp.md
locations:
  - locations/14620019306909596262   # Andover
  - locations/5306670257346298793    # Sudbury
account_id: accounts/105463627678224581857
vertical: service-area
primary_metric: CALL_CLICKS
rollup: per-location
mode: recurring                      # first-run | recurring
owner: Daniel Goodrich
deliver_to: draft                    # draft | basecamp:<project> (drafts only; a human sends)

RULES
- Use the window from gbp_get_data_freshness (weeks 13, lag_days 8). Never include today or the lag days.
- Key everything by location_id. Never sum locations unless rollup says so.
- Compute every number from pulled rows before writing a sentence.
- If a tool fails twice, stop, write the escalation memo naming the layer that failed, and do not fabricate.
- Recurring mode: run the tripwire gate. Any fired tripwire holds the week for team review with the banner.
- Output: the client report (report-format.md), then an internal section with the working table, flags, clarity grade, tripwire results, and the exact writeback to the locked config.
- Draft only. Do not send, post, or edit any profile.
```
