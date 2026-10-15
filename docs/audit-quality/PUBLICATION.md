# Publication status and integration

The maintained teaching destination is the existing [How We Audit](https://blitzmetrics.com/how-we-audit/) article. This package proposes an additive report-quality section; no new article URL is needed. Specialist exam weights, caps, coverage rules and pass lines remain with their existing owners.

The source-text standard, templates and synthetic decision logic have fresh-context review. Browser/theme design, operational calibration and public article deployment/readback remain unverified. A public branch or pull request makes the proposal readable; it does not establish adoption, installed skill parity or a completed audit.

`how-we-audit-addition.html` contains the proposed full section and static process figure. The current article body must be preserved. `prepare_article_update.py` takes an authenticated current source preimage and a current public REST baseline, fails on drift or duplicate insertion, and prepares content-only and rollback payloads. It performs no network writes. The existing authorized publisher must review the exact source and theme render, recheck current ownership/holds, deploy through the current host route, then verify anonymous body, canonical, desktop/mobile, media, links and downloads before reporting a live revision. Never use rendered HTML as an editable raw-source preimage.

The standard is a proposed operational profile. Calibration anchors and score agreement must be recorded before operational scoring. The decision checker only evaluates asserted receipt fields; it cannot verify source truth, reviewer independence, rendering, privacy or deployment itself.
