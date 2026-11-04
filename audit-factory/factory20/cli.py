"""python -m factory20 <command> — every command is offline except `run` with a live tier.

  render   <audit.json> --ledger L --out audit.pdf     render + render gates (exit 2 on HOLD)
  gate     <audit.json> --ledger L [--tier standard]   content gates (exit 2 on HOLD); reads brief.json beside it
  measure  <pdf>...                                    density/evidence metrics for any audit PDF
  cost     [--tier T] [--per-month N] [--batch]        per-stage and per-audit cost
  pack     <ledger.json> [--blind]                     compact evidence pack for a model prompt
  basecamp <audit.json> --ledger L --out todos.json    to-dos with agent briefs (+ .md preview)
  card     <stage>                                     print a stage card for a manual session
  run      <run-dir> --tier T [--fake F] [--no-render] [--no-review]
                                                       stages 30-70 -> gates -> PDF -> up to 3 fix rounds -> fresh-context review
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import basecamp, cost, gates, model, pdfcheck, pipeline, render
from .ledger import Ledger, blind_copy

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _print_report(rep: dict, title: str) -> None:
    print(f"\n{title}: {rep['verdict']}  ({rep['pass']} pass · {rep['warn']} warn · {rep['fail']} fail)")
    for c in rep["checks"]:
        if c["status"] != "PASS":
            print(f"  [{c['status']}] {c['id']} {c['name']}: {c['msg']}")


def cmd_gate(a) -> int:
    audit = render.expand(model.load(a.audit), Ledger.load(a.ledger) if a.ledger else None)
    led = Ledger.load(a.ledger) if a.ledger else None
    brief = pathlib.Path(a.brief) if a.brief else pathlib.Path(a.audit).with_name("brief.json")
    b = json.loads(brief.read_text()) if brief.exists() else {}
    rep = gates.gate_audit(audit, led, a.tier, do_not_print=b.get("do_not_print", []),
                           allowed_phones=b.get("allowed_phones", [])).summary()
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rep, indent=1))
    _print_report(rep, "Content gates")
    return 2 if rep["verdict"] == "HOLD" else 0


def cmd_render(a) -> int:
    rr = render.render(a.audit, a.ledger, a.out, a.html)
    audit = model.load(a.audit)
    install = audit.get("meta", {}).get("install_url", render.INSTALL_URL)
    rep = gates.gate_render(rr, install).summary()
    rr["gates"] = rep
    pathlib.Path(str(a.out) + ".render.json").write_text(json.dumps(rr, indent=1))
    print(f"rendered {rr['pdf']} · {rr['pdf_pages']} pages · links {rr['links']} · overflow {rr['overflow_pages']} "
          f"· missing assets {len(rr['missing_assets'])} · qr {rr['qr_decoded']!r}")
    _print_report(rep, "Render gates")
    return 2 if rep["verdict"] == "HOLD" else 0


def cmd_measure(a) -> int:
    cols = ["pages", "words_per_page", "numbers_per_page", "pages_with_3plus_ids", "thin_pages", "link_annotations", "grade"]
    print("file | " + " | ".join(cols))
    for p in a.pdfs:
        m = pdfcheck.measure(p)
        print(f"{pathlib.Path(p).name} | " + " | ".join(str(m[c]) for c in cols))
    return 0


def cmd_cost(a) -> int:
    cfg = cost.load_routing()
    tiers = [a.tier] if a.tier else list(cfg["tiers"])
    for t in tiers:
        r = cost.audit_cost(t, cfg, a.batch)
        print(f"\n{t}: ${r['total_usd']:.2f} per audit (frontier slice ${r['frontier_usd']:.2f})")
        for s in r["stages"]:
            print(f"  {s['stage']:10s} {s['model']:22s} in {s['in']:>9,} out {s['out']:>7,}  ${s['usd']:.3f}")
        if a.per_month:
            print(f"  x {a.per_month}/month = ${cost.monthly(t, a.per_month, cfg, a.batch):,.2f}")
    ref = cost.reference_cost(cfg)
    print(f"\nreference all-Claude run, Oct 23 (measured tokens at list price, {ref['cache_read_share']:.1%} cache reads): "
          f"${ref['audit_usd']:,.2f} for the audit, ${ref['total_usd']:,.2f} with its website package")
    return 0


def cmd_pack(a) -> int:
    data = json.loads(pathlib.Path(a.ledger).read_text(encoding="utf-8"))
    if a.blind:
        data = blind_copy(data)
    print(Ledger.from_json(data).pack(include_notes=a.notes))
    return 0


def cmd_basecamp(a) -> int:
    led = Ledger.load(a.ledger) if a.ledger else None
    payload = basecamp.todos(model.load(a.audit), led)
    pathlib.Path(a.out).write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    pathlib.Path(a.out).with_suffix(".md").write_text(basecamp.markdown(payload))
    print(f"{len(payload['todos'])} to-dos → {a.out} ({payload['counts']})")
    if payload["unassigned"]:
        print(f"UNASSIGNED (no running agent for their function in config/agents.json): {payload['unassigned']}")
        return 2
    return 0


def cmd_card(a) -> int:
    print((ROOT / "stages" / a.stage).read_text(encoding="utf-8") if a.stage.endswith(".md")
          else next((ROOT / "stages").glob(f"*{a.stage}*.md")).read_text(encoding="utf-8"))
    return 0


def cmd_run(a) -> int:
    fake = None
    if a.fake:
        from .testing import fake_from_fixture
        fake = fake_from_fixture(a.fake)
    res = pipeline.run(a.run_dir, a.tier, fake=fake, render_pdf=not a.no_render, review=not a.no_review)
    print(json.dumps(res, indent=1))
    return 0 if res.get("verdict") in ("READY", "REVIEW_READY") else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="factory20", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gate"); g.add_argument("audit"); g.add_argument("--ledger"); g.add_argument("--tier", default="standard",
                                                                                                     choices=list(gates.TIERS)); g.add_argument("--json")
    g.add_argument("--brief", help="brief.json with do_not_print (default: brief.json beside the audit)")
    r = sp.add_parser("render"); r.add_argument("audit"); r.add_argument("--ledger"); r.add_argument("--out", required=True); r.add_argument("--html")
    m = sp.add_parser("measure"); m.add_argument("pdfs", nargs="+")
    c = sp.add_parser("cost"); c.add_argument("--tier"); c.add_argument("--per-month", type=int); c.add_argument("--batch", action="store_true")
    p = sp.add_parser("pack"); p.add_argument("ledger"); p.add_argument("--blind", action="store_true"); p.add_argument("--notes", action="store_true")
    b = sp.add_parser("basecamp"); b.add_argument("audit"); b.add_argument("--ledger"); b.add_argument("--out", required=True)
    k = sp.add_parser("card"); k.add_argument("stage")
    rn = sp.add_parser("run"); rn.add_argument("run_dir"); rn.add_argument("--tier", default="standard")
    rn.add_argument("--fake", help="fixture audit.json to replay instead of calling models (tests)")
    rn.add_argument("--no-render", action="store_true")
    rn.add_argument("--no-review", action="store_true", help="stop after gates and render (no frontier review)")
    a = ap.parse_args(argv)
    return {"gate": cmd_gate, "render": cmd_render, "measure": cmd_measure, "cost": cmd_cost, "pack": cmd_pack,
            "basecamp": cmd_basecamp, "card": cmd_card, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
