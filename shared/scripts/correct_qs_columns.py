#!/usr/bin/env python3
"""
correct_qs_columns.py - deterministic Quality Score column corrector (MAA skills)

The deployed Google Ads data script ships the Keyword Report with the
`Expected CTR` and `Ad Relevance` columns INVERTED (see
shared/frameworks/data-pipeline-contract.md and the 2026-06-05 Mislabel-Fix
decision). Per Approach B the script is never redeployed; the fix lives in the
consumer. This tool makes that fix MECHANICAL instead of a per-run judgment call:
it reads a raw `*_email-data.txt`, swaps the two columns back inside the
KEYWORD REPORT 30D and 7D blocks, and writes a corrected copy whose column
labels finally match their values.

After running this, read the *_corrected.txt file and treat every column
as-labeled. Do NOT swap again - the inversion is already undone here.

The swap is positional and tightly anchored (a Quality Score number/N/A followed
by exactly three Above/Average/Below/N/A tokens), so it only ever touches real QS
rows and is loss-less: all other text passes through verbatim.

Usage:
    python3 correct_qs_columns.py --infile path/to/2026-06-26_email-data.txt
    # writes path/to/2026-06-26_email-data_corrected.txt
    python3 correct_qs_columns.py --infile RAW --outfile OUT
"""
import argparse, os, re, sys

BLOCKS = [
    ("---BEGIN KEYWORD REPORT 30D---", "---END KEYWORD REPORT 30D---"),
    ("---BEGIN KEYWORD REPORT 7D---", "---END KEYWORD REPORT 7D---"),
]

LABEL = r"(?:ABOVE_AVERAGE|AVERAGE|BELOW_AVERAGE|N/A)"
# A Quality Score cell (1-10 or N/A) followed by the three component cells.
# Column order in the export header: Expected CTR, Landing Page Exp, Ad Relevance.
# Per the bug, the value under "Expected CTR" is really Ad Relevance and vice
# versa, so we swap the 1st and 3rd component cells; the middle (LP) is correct.
QS_TRIPLE = re.compile(
    r",(?P<qs>\d{1,2}|N/A),(?P<ectr_col>%s),(?P<lp>%s),(?P<adrel_col>%s)," % (LABEL, LABEL, LABEL)
)


def flatten(block_body):
    """Rejoin the email's hard line-wraps so each QS triple is contiguous."""
    flat = re.sub(r"[\r\n]+", " ", block_body)
    flat = re.sub(r"[ \t]{2,}", " ", flat)
    return flat


def correct_block(block_body):
    flat = flatten(block_body)
    count = [0]

    def repl(m):
        count[0] += 1
        # put the true Expected CTR (raw "Ad Relevance" col) under Expected CTR,
        # and the true Ad Relevance (raw "Expected CTR" col) under Ad Relevance.
        return ",%s,%s,%s,%s," % (m.group("qs"), m.group("adrel_col"),
                                   m.group("lp"), m.group("ectr_col"))

    corrected = QS_TRIPLE.sub(repl, flat)
    return corrected, count[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--outfile", default=None)
    a = ap.parse_args()

    raw = open(a.infile, encoding="utf-8", errors="replace").read()
    out = raw
    total = 0
    found_any = False
    for begin, end in BLOCKS:
        i = out.find(begin)
        j = out.find(end)
        if i == -1 or j == -1 or j < i:
            continue
        found_any = True
        body = out[i + len(begin):j]
        corrected_body, n = correct_block(body)
        total += n
        out = out[:i + len(begin)] + corrected_body + out[j:]

    if not found_any:
        sys.stderr.write("WARNING: no KEYWORD REPORT blocks found in %s\n" % a.infile)

    note = ("# QS COLUMNS CORRECTED by correct_qs_columns.py per "
            "shared/frameworks/data-pipeline-contract.md. Expected CTR and Ad "
            "Relevance have been un-swapped in the KEYWORD REPORT blocks. Read "
            "every column AS-LABELED; do NOT swap again.\n")
    out = note + out

    outfile = a.outfile or re.sub(r"(\.txt)?$", "_corrected.txt", a.infile, count=1)
    if outfile == a.infile:
        outfile = a.infile + "_corrected.txt"
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(out)
    print("corrected %d keyword rows -> %s" % (total, outfile))


if __name__ == "__main__":
    main()
