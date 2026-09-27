#!/usr/bin/env python3
"""Congruency check for the Local Service Spotlight skill marketplace.

One master, many skins. This asserts the invariants that make that true, so a
count printed anywhere can be regenerated instead of remembered.

  M1  master == the skills/ directory, exactly. No orphans, no phantoms.
  M2  every skin is a subset of the master. A skin never introduces a skill.
  M3  every master skill appears in at least one skin. No skill is unreachable.
  M4  no skill is claimed by more than one skin. The skins tile the master.
  M5  every declared skill directory exists and contains a SKILL.md.
  M6  every description that prints a count prints the true count.
  M7  the marketplace declares a version.

Exit 0 = congruent. Exit 1 = a human has to look.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
SKILLS = os.path.join(ROOT, "skills")
MASTER = "lss-everything"

def main():
    fail = []
    note = []
    m = json.load(open(MANIFEST))

    version = (m.get("metadata") or {}).get("version")
    if not version:
        fail.append("M7  marketplace.json has no metadata.version")

    on_disk = sorted(d for d in os.listdir(SKILLS)
                     if os.path.isdir(os.path.join(SKILLS, d)) and not d.startswith("."))

    master, skins = None, {}
    for p in m["plugins"]:
        names = [s.rsplit("/", 1)[-1] for s in p["skills"]]
        dupes = [k for k, v in collections.Counter(names).items() if v > 1]
        if dupes:
            fail.append(f"M4  {p['name']} lists the same skill twice: {dupes}")
        if p["name"] == MASTER:
            master = names
        else:
            skins[p["name"]] = names

    if master is None:
        fail.append(f"M1  no plugin named {MASTER!r} — there is no master")
        report(fail, note, version); return 1

    # M1 — master is the directory
    extra = sorted(set(on_disk) - set(master))
    phantom = sorted(set(master) - set(on_disk))
    if extra:
        fail.append(f"M1  on disk but not in the master: {extra}  "
                    f"(add to {MASTER} or delete the directory)")
    if phantom:
        fail.append(f"M1  in the master but not on disk: {phantom}")

    # M2/M3/M4 — skins are derived views that tile the master
    claims = collections.Counter()
    for name, names in skins.items():
        outside = sorted(set(names) - set(master))
        if outside:
            fail.append(f"M2  skin {name!r} introduces skills the master does not have: {outside}")
        claims.update(set(names))
    orphans = sorted(set(master) - set(claims))
    if orphans:
        fail.append(f"M3  in the master but in no skin: {orphans}")
    multi = {k: v for k, v in claims.items() if v > 1}
    if multi:
        owners = {k: sorted(n for n, ns in skins.items() if k in ns) for k in multi}
        fail.append(f"M4  claimed by more than one skin: {owners}")

    # M5 — every declared path is real and installable
    for name in sorted(set(master) | set(claims)):
        d = os.path.join(SKILLS, name)
        if not os.path.isdir(d):
            fail.append(f"M5  {name}: directory missing")
        elif not os.path.isfile(os.path.join(d, "SKILL.md")):
            fail.append(f"M5  {name}: no SKILL.md — it will not load")

    # M6 — printed counts are true counts
    for p in m["plugins"]:
        n = len(p["skills"])
        for printed in re.findall(r"\b(\d+)\s+(?:Local Service Spotlight\s+)?skills?\b",
                                  p.get("description", "")):
            if int(printed) != n:
                fail.append(f"M6  {p['name']}: description says {printed}, manifest lists {n}")

    note.append(f"marketplace version {version}")
    note.append(f"master {MASTER}: {len(master)} skills; directory: {len(on_disk)}")
    for name in sorted(skins):
        note.append(f"skin {name}: {len(skins[name])}")
    note.append(f"skins sum to {sum(len(v) for v in skins.values())} (must equal master {len(master)})")

    report(fail, note, version)
    return 1 if fail else 0

def report(fail, note, version):
    for n in note:
        print(f"  · {n}")
    if fail:
        print("\nCONGRUENCY: FAIL")
        for f in fail:
            print(f"  ✗ {f}")
    else:
        print("\nCONGRUENCY: PASS — one master, skins tile it exactly once.")

if __name__ == "__main__":
    sys.exit(main())
