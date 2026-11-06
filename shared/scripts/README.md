# shared/scripts

## correct_qs_columns.py

Deterministic corrector for the **email pipeline's** Quality Score column
inversion: affected data-collection script versions emit the `Expected CTR` and
`Ad Relevance` columns swapped in the KEYWORD REPORT 30D/7D blocks (Landing
Page Experience is unaffected). This script un-swaps them positionally and
losslessly.

**Usage:**

```
python3 shared/scripts/correct_qs_columns.py --infile {date}_email-data.txt
```

Writes `{date}_email-data_corrected.txt` next to the input. Analyze the
`_corrected.txt` file and read every column **as labeled**, do not swap again;
double-swapping re-introduces the bug. Keep the raw file verbatim for the
record.

⚠️ **Never run this on MCP data.** The Google Ads MCP returns correctly-labeled
QS components; applying the corrector to MCP output would invert good data.
This script exists for the email fallback path only. Full rules:
`shared/frameworks/data-pipeline-contract.md`.
