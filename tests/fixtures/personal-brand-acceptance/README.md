# Synthetic acceptance regressions

`tests/personal_brand_fixture.py` creates a disposable 20-page PDF, source captures,
render stand-ins, decoder/access receipts and a versioned ZIP. All identities, URLs,
permissions and reviewer statements are synthetic. The stand-ins exercise hash binding
and declared type/role checks; they are not real photography, rendered-page QA, working
QRs, permission proof, tested live delivery, or a complete accepted audit.

The positive control must return mechanical PASS and REVIEW_REQUIRED. Mutations must
produce HOLD for screenshot-only covers, wrong-person/unknown-rights photos, decorative
QRs, missed source targets, duplicate/padded counts, broken traceability, tiny labels,
missing/failed fresh review, stale PDF/kit/render hashes, generic kit destinations,
missing promised files/skills, owner-only downloads and installation claims from a ZIP.
No client data or private reports are included. The fixtures do not award an A+.
