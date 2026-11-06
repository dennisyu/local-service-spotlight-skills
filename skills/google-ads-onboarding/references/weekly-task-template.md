# Weekly scheduled-task prompt template

Filled by `google-ads-onboarding` Phase G and written to
`{OUTPUT_DIR}/{client}/deliverables/{date}-weekly-task-prompt.md`. The
operator pastes it into a new scheduled task (`maa-{slug}`) once the
onboarding brief is reviewed and the intake answers are in the ledger, or when
the quarantine exits, whichever comes first. Schedule it after the account's
data drops (Friday morning local, after any email export lands).

Placeholders: `{CLIENT}`, `{SLUG}`, `{CID}`, `{MCC}`, `{VAULT}` (client folder
absolute path), `{EMAIL_SUBJECT}` (fallback export subject prefix, or "none"),
`{LEAD_UNIT}` (one clause from ledger section 2, e.g. "counted calls of 60
seconds or longer"), `{OPENING}` ("the plain-English business paragraph opens
the MAA before Metrics" if the spec requires it, else blank), `{SCOPE_NOTES}`
(one line: LSA exclusion, timezone quirks, campaigns excluded by design).

---

Weekly Google Ads MAA for {CLIENT}. CID {CID}, MCC {MCC}. Vault: {VAULT}. Draft only. Never post to Basecamp, never email, never render the client view until Daniel approves in chat. {SCOPE_NOTES}

STAGE 0, READ BEFORE ANY DATA. In this order, fully: compiled/ledger.md (every section), client-knowledge-base.md, compiled/maa-metric-spec.md, clients/_shared/maa-skills-binding.md, clients/_shared/maa-generation.md, clients/_shared/google-ads-data-contract.md, the most recent dated MAA in deliverables/. If compiled/ledger.md is missing, stop and report; do not draft. Do not read compiled/paid-status.md or compiled/active-issues.md end to end; consult them only to resolve a specific conflict, and the ledger wins on any disagreement unless a more recent dated entry exists.

STAGE 0b, PULL. Use the google-ads-maa-skills:google-ads-analyzer skill on the MCP path with clients/_shared/google-ads-gaql-pack.md. Pull the full pack for 7D and 30D before writing a word: campaign summary, campaign_budget, keyword report with QS components (all statuses, not just ENABLED), search terms, ad report with strength, conversion detail by action, network segment, device segment, user_location_view, negatives at three levels, call_view where call assets exist. Save the raw pull to raw/google-ads/YYYY-MM-DD_mcp-pull.json. Record row counts; if any query returns exactly its row cap, flag it and make no absence claim on that dataset. Verify every response carries this client's campaign names before using it. If the MCP is unavailable, use the email fallback (Gmail label maa-data-automation, subject starts "{EMAIL_SUBJECT}"; run the QS column corrector). If both are unavailable, stop and report; never splice partial data.

STAGE 1, DRAFT under the ten evidence gates in shared/frameworks/evidence-gates.md. Foundation breaks act immediately; everything else: no Action on fewer than 30 clicks or 5 conversions; no Action without two prior cycles on the ledger watch list; nothing in the quarantine is judged before its exit date; network and device splits before any keyword verdict; daily before averaging any budget-lost or spend figure; no absence claim on a capped or status-filtered query; the lead unit is {LEAD_UNIT} and the target, windows and service-area test come from the ledger; every causal or trend sentence carries a dataset reference in Generation notes or is deleted; context questions are answered from the ledger or added to its Open ASKs, never asked in chat. Follow the metric spec section order verbatim. {OPENING} Action is one list with inline owners, no scripts or filenames, no em dashes, "we" voice. Write to deliverables/YYYY-MM-DD-google-ads-maa.md.

STAGE 2, HARDEN. Dispatch google-ads-maa-skills:google-ads-reviewer as a subagent in a fresh context with only the frozen draft, the raw pull, the ledger and the metric spec. Apply its KEEP / DEMOTE TO WATCH / DROP / REPULL verdicts once. One round; anything still contested goes to Generation notes for Daniel.

STAGE 3, RECONCILE against the ledger: every number ties to the pull; every Action has watch-list age or is a foundation break; nothing quarantined is judged; no "See Action N" pointer is broken; nothing on the never-surface list appears; render spec norms are met. Any account state the ledger change log does not explain is recorded as "unlogged change" in Generation notes and an Open ASK, not analyzed.

STAGE 4, WRAP. Append the trend.csv row. Append to compiled/ledger.md: weekly log row; change-log rows for anything shipped; watch-list updates; new Open ASKs; new quarantine entries with exit dates; new data faults. Never rewrite past ledger lines. Short dated block in paid-status.md and active-issues.md. Do NOT render the client view.

Finish with a chat summary of at most 8 lines: leads and CPL vs last cycle, Actions proposed, items the hardener demoted or dropped, open ASKs for Daniel, data faults hit.
