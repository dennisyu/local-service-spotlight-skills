# Job board — work nobody owns yet

Copy to `status/JOBS.md`. Claimed work moves to `status/NOW.md`. The coordinator agent
sweeps this board daily; a row past its recheck date is a failure, not a status.

Row contract:

    - JOB-NNN | OPEN    | function: <what kind of desk can do it> | recheck: YYYY-MM-DD | what, and what done looks like
    - JOB-NNN | CLAIMED | function: <...> | owner: <agent> | recheck: YYYY-MM-DD | what
    - JOB-NNN | DONE    | what — Verified: <what you opened> — <what you saw> — <when>

## OPEN

- JOB-001 | OPEN | function: site publishing | recheck: 2026-01-15 | Publish the staged article; done = live URL shows the new headline.

## CLAIMED

## DONE
