# Offline synthetic fixtures

These are test data, not an approved client/Singapore rubric or a real person's score.

```sh
python3 scripts/audit_report_contract.py --rubric tests/fixtures/audit-contract/rubric.json --report tests/fixtures/audit-contract/correct-48.json
python3 scripts/audit_report_contract.py --rubric tests/fixtures/audit-contract/rubric.json --report tests/fixtures/audit-contract/wrong-58.json
python3 scripts/audit_report_contract.py --batch tests/fixtures/audit-contract/batch.json
```

Expected: CHECKED/48, HOLD/headline mismatch, CHECKED final PDF binary and current
extraction. The PDF fixture was produced/extracted with existing pypdf6.13.2.
Its binary hash and exact extracted UTF8 companion must match. Visual/source-truth
review is separate. Install the pinned optional QA dependency only within an
approved execution environment; missing extraction keeps the batch HOLD.
