# Locked-Config — per-client GBP spec

Save at `{client_vault}/{client}/locked-config-gbp.md`. First-Run seeds it; Recurring runs append to `run_history`, `open_questions`, and replace the profile snapshot; locked fields change only through a team-reviewed First-Run.

```yaml
client: Target Painting & Contracting
vertical: service-area            # home-services | professional | destination | service-area | online
primary_metric: CALL_CLICKS       # the headline action
secondary_metric: WEBSITE_CLICKS
mode_ready: first-run-only        # recurring | first-run-only | escalated
locked_on: 2026-09-22
locked_by: Daniel Goodrich

account_id: accounts/105463627678224581857
locations:
  - location_id: locations/14620019306909596262
    title: Target Painting & Contracting, Inc.
    label: Andover
  - location_id: locations/5306670257346298793
    title: Target Painting & Contracting, Inc.
    label: Sudbury
rollup: per-location              # per-location | rollup-with-table
excluded_locations: []            # closed or duplicate rows, with reason

baselines:                        # set on First-Run from the 26-week pull
  primary_weekly_band: [0, 3]     # min..max weekly primary in the baseline window
  primary_prior_period: 3
  impressions_maps_prior_period: 109
  action_rate_prior_period: 0.116
  clarity_baseline: Clear
  review_count_last_seen: 0
  average_rating_last_seen: 0.0

profile_snapshot:                 # P6 fields worth diffing; replaced each run
  primary_category: Painter
  phone: ""
  website: https://targetpainting.com/
  address_line: ""
  open_status: OPEN
  hours_set: true
  description_chars: 0
  service_items: 0
  photo_count: 0
  latest_photo: ""
  latest_post: ""
profile_snapshot_prev: {}

services_not_offered: []           # e.g. [medical malpractice, lemon law]; H-check flags any of these in description/services/keywords
known_issues: []                  # e.g. {issue: non-English category on Issaquah, status: NOT_APPLIED, first_seen: 2026-09-22}
open_questions: []
run_history: []                   # {date, mode, headline, clarity, escalated, notes}
```
