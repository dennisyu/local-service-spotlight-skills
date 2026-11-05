"""Audit Factory 20 — tiered production of the exact 20-page Local Service Spotlight audit.

The model writes structured content (audit.json). Code does everything that can be code:
rendering, arithmetic, evidence linkage, density, privacy and page checks. The frontier
model is spent only where judgment changes the answer: synthesis and the final review.

Modules
    ledger     load and normalize an evidence ledger (Claude JSON format or CSV)
    model      load audit.json, collect evidence refs, structural helpers
    score      Brand Authority v1.0 arithmetic and calibration flags
    gates      deterministic quality gates for audit.json (+ rendered PDF)
    pdfcheck   density/evidence metrics for any audit PDF, from any agent
    components SVG/HTML components (insight cards, graphs, heatmap, swimlane ...)
    render     audit.json + ledger -> 20-page HTML -> PDF (Playwright/Chromium)
    cost       price table, per-stage token budgets, per-audit and monthly cost
    router     stage -> model routing, provider adapters, escalation
    basecamp   action register -> Basecamp to-do payloads (agent vs human)
    cli        python -m factory20 <command>
"""

__version__ = "1.0.0"
SCHEMA_ID = "lss-audit/1.0"
