"""python -m factory20 <command> — every command is offline except `run` with a live tier.

  render   <audit.json> --ledger L --out audit.pdf     render + render gates (exit 2 on HOLD)
  gate     <audit.json> --ledger L [--tier standard]   content gates (exit 2 on HOLD); reads brief.json beside it
  measure  <pdf>...                                    density/evidence metrics for any audit PDF
  cost     [--tier T] [--per-month N] [--batch]        per-stage and per-audit cost (planning estimate,
                                                       then the measured-profile estimate)
  pack     <ledger.json> [--blind]                     compact evidence pack for a model prompt
  basecamp <audit.json> --ledger L --out todos.json    to-dos with agent briefs (+ .md preview)
  card     <stage>                                     print a stage card for a manual session
  run      <run-dir> --tier T [--max-usd X] [--fake F] [--no-render] [--no-review]
                                                       stages 30-70 -> gates -> PDF -> up to 3 fix rounds -> fresh-context review
  init     <run-dir> (--from-demo | --ledger L --brief B) [--assets DIR]
                                                       make a run folder (the public demo needs no private data)
  bundle   <run-dir>                                   bundle a finished run for the house audit-quality gate
                                                       (exit 2 if the run is not finished or its records disagree)
  openrouter-check [--models FILE] [--write]           every OpenRouter route still listed, at the price we assume
                                                     (or charged by 3 providers that are up)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import basecamp, cost, gates, model, openrouter, pdfcheck, pipeline, render
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
    print(f"\nFrom an existing ledger, measured profile ({cfg['measured_profile']['label']}):")
    print(f"  {'tier':18s} {'typical':>8s} {'worst case':>11s}   (typical = 1 fix round, 1 review pass; "
          "worst = 3 fix rounds, every review pass, full thinking room, 25% retries)")
    for t in tiers:
        r = cost.measured_range(t, cfg)
        line = f"  {t:18s} ${r['typical']['total_usd']:>7.2f} ${r['worst']['total_usd']:>10.2f}"
        if a.per_month:
            line += f"   x {a.per_month}/month = ${r['typical']['total_usd'] * a.per_month:,.2f} typical"
        print(line)
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
    res = pipeline.run(a.run_dir, a.tier, fake=fake, render_pdf=not a.no_render, review=not a.no_review,
                       max_usd=a.max_usd)
    print(json.dumps(res, indent=1))
    return 0 if res.get("verdict") in ("READY", "REVIEW_READY") else 2


DEMO = ROOT / "fixtures" / "demo"
BRIEF_KEYS = ("subject", "subject_type", "title", "date", "plan_start", "prepared_for", "prepared_by",
              "confidentiality", "palette", "install_url")


def cmd_init(a) -> int:
    """Make a run folder: brief.json + ledger.json (+ assets/). Never copies stage outputs."""
    import shutil
    run = pathlib.Path(a.run_dir)
    if run.exists() and any(run.iterdir()):
        print(f"{run} is not empty; pick a new folder so no earlier stage file is reused by accident")
        return 2
    run.mkdir(parents=True, exist_ok=True)
    if a.from_demo:
        meta = json.loads((DEMO / "audit.json").read_text(encoding="utf-8"))["meta"]
        brief = {k: meta[k] for k in BRIEF_KEYS if k in meta}
        shutil.copy(DEMO / "ledger.json", run / "ledger.json")
        assets = DEMO / "assets"
    else:
        if not (a.ledger and a.brief):
            print("give --from-demo, or both --ledger and --brief")
            return 2
        brief = json.loads(pathlib.Path(a.brief).read_text(encoding="utf-8"))
        shutil.copy(a.ledger, run / "ledger.json")
        assets = pathlib.Path(a.assets) if a.assets else None
    (run / "brief.json").write_text(json.dumps(brief, indent=1, ensure_ascii=False), encoding="utf-8")
    if assets and assets.exists():
        shutil.copytree(assets, run / "assets")
    print(f"run folder ready: {run}  (brief.json, ledger.json{', assets/' if assets and assets.exists() else ''})")
    return 0


def cmd_bundle(a) -> int:
    """Receipt + manifest + evidence envelopes for docs/audit-quality/verify_bundle.py."""
    from . import bundle
    try:
        s = bundle.build(a.run_dir)
    except bundle.BundleError as e:
        print(f"not bundled: {e}")
        return 2
    print(f"bundle written in {s['run']}: {s['receipt']} + {s['manifest']} · {s['artifacts']} artifacts · "
          f"{s['evidence']} evidence rows ({s['ledger_rows']} ledger rows) · {s['claims']} claims · "
          f"{s['actions']} actions")
    if s["skipped_rows"]:
        print(f"  {s['skipped_rows']} ledger rows have no id and could not be bound")
    print("  synthetic: " + ("yes — " + "; ".join(s["synthetic_reasons"]) if s["synthetic"] else "no"))
    passed = [n for n, st in s["checks"].items() if st == "PASS"]
    print(f"  required checks: PASS {', '.join(passed) or 'none'}; {len(s['checks']) - len(passed)} not PASS"
          f" · actual cost {s['actual_cost']}")
    print("  left open (the gate decides; this is the bundle's own list):")
    for item in s["open"]:
        print(f"    - {item}")
    root = ROOT.parent / "docs" / "audit-quality" / "verify_bundle.py"
    mode = " --mode exercise" if s["synthetic"] else ""
    print(f"grade it: python3 {root if root.exists() else 'docs/audit-quality/verify_bundle.py'} --root {s['run']}{mode}")
    return 0


def cmd_openrouter_check(a) -> int:
    cfg = cost.load_routing()
    if a.models:
        models, endpoints, failed = openrouter.load_models(a.models), openrouter.load_endpoints(a.models), []
    else:
        models = openrouter.fetch_models()
        endpoints, failed = openrouter.fetch_all_endpoints(cfg)
    rep = openrouter.check(cfg, models, a.tolerance, endpoints)
    print(f"OpenRouter routes in routing.json: {len(rep['rows'])} · models listed on OpenRouter: {len(models)}"
          + (f" · provider endpoints read for {len(endpoints)} routes" if endpoints is not None else ""))
    for r in rep["rows"]:
        state = "MISSING" if not r["listed"] else ("DRIFT" if r["drift"] else "ok")
        detail = "; ".join(f"{f} {d['ours']} -> {d['live']}" for f, d in r["drift"].items())
        if r.get("headline"):
            moved = "; ".join(f"{f} {d['ours']} -> {d['live']}" for f, d in r["headline"].items())
            detail = (detail + " · " if detail else "") + \
                f"headline {moved} is one provider's; {r['backing']} providers that are up charge ours"
        elif r["drift"] and "backing" in r:
            detail += f" ({r['backing']} providers that are up charge ours; {openrouter.MIN_BACKING} would vouch for it)"
        print(f"  [{state:7s}] {r['key']:34s} {detail}")
    if failed:
        print(f"endpoint lists that did not load (checked on the headline price alone): {', '.join(failed)}")
    if a.write and rep["drifted"]:
        changed = openrouter.write_prices(rep)
        print(f"updated {len(changed)} price lines in config/routing.json: {', '.join(changed)}")
        rep = openrouter.check(cost.load_routing(), models, a.tolerance, endpoints)
    if a.write:
        snap = openrouter.save_snapshot(cost.load_routing(), models, endpoints=endpoints)
        print(f"saved {snap} (the tests check the config against it)")
    if rep["missing"]:
        print(f"routes no longer on OpenRouter: {', '.join(rep['missing'])}"
              + (f" (used by a tier: {', '.join(rep['missing_in_use'])})" if rep["missing_in_use"] else ""))
    print("OpenRouter check:", "PASS" if rep["ok"] else "FAIL")
    return 0 if rep["ok"] else 1


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
    rn.add_argument("--max-usd", type=float, help="spending cap for this run (default: the tier's max_usd)")
    i = sp.add_parser("init"); i.add_argument("run_dir"); i.add_argument("--from-demo", action="store_true")
    i.add_argument("--ledger"); i.add_argument("--brief"); i.add_argument("--assets")
    bd = sp.add_parser("bundle", help="bundle a finished run for docs/audit-quality/verify_bundle.py")
    bd.add_argument("run_dir")
    o = sp.add_parser("openrouter-check"); o.add_argument("--models", help="saved copy of OpenRouter's models list, with its endpoints if saved (default: fetch both)")
    o.add_argument("--write", action="store_true", help="update drifted prices in config/routing.json")
    o.add_argument("--tolerance", type=float, default=0.10, help="allowed price drift before the check fails (default 10%%)")
    a = ap.parse_args(argv)
    return {"gate": cmd_gate, "render": cmd_render, "measure": cmd_measure, "cost": cmd_cost, "pack": cmd_pack,
            "basecamp": cmd_basecamp, "card": cmd_card, "run": cmd_run, "init": cmd_init,
            "bundle": cmd_bundle, "openrouter-check": cmd_openrouter_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
