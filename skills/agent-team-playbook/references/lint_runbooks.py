#!/usr/bin/env python3
"""lint_runbooks.py — every recurring task documented well enough to hand over.

On 2026-10-17 Dennis asked that "all agents are clearly documenting what they're doing
in GitHub so that other agents can piece together the role and tasks well enough to run
it if I wish." Happy filed the standard the same hour (runbooks/<agent>/INDEX.md plus one
eight-section runbook per recurring task; registries due 2026-10-19, runbooks due
2026-10-24) and promised to count the gaps by hand every evening.

This makes the count a machine's job. A written rule asks agents to document; a red CI
makes them, because the daily run turns red the morning a deadline passes even when
nobody pushed. Same philosophy as lint_job_board.py: check the smallest thing that can
honestly be checked — that a runbook has its eight sections, a dated owner line, and no
credential; that a registry resolves; that every live Claude scheduled task is covered —
and never let NOT CHECKED render as PASS.

    python3 tools/lint_runbooks.py                    full report
    python3 tools/lint_runbooks.py --quiet            counts only
    python3 tools/lint_runbooks.py --write-status     also regenerate runbooks/STATUS.md
    python3 tools/lint_runbooks.py --today=YYYY-MM-DD evaluate deadlines as of a date
    python3 tools/lint_runbooks.py --root=PATH        check another tree (tests)

Standard: runbooks/README.md.   Tests: tools/test_lint_runbooks.py.
Exit codes:  0 clean · 1 errors · 2 unrecognised argument.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent

# One secret guard for the whole house: the same content scan sync_runtime.py runs
# before anything leaves for the cloud runtime. Change the patterns there, not here.
sys.path.insert(0, str(HERE))
try:
    from sync_runtime import scan_secret  # noqa: E402
    _SECRET_IMPORT_ERROR = ""
except Exception as exc:  # outside this repo (the public kit) — same patterns, built in
    _SECRET_IMPORT_ERROR = repr(exc)
    _BUILTIN_SECRETS = [
        (re.compile(r"\b(?:[A-Za-z0-9]{4}[ \t]){5}[A-Za-z0-9]{4}\b"), False),
        (re.compile(r"\b(?:glpat-[A-Za-z0-9_\-]{15,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                    r"|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_\-]{20,}|sk_live_[A-Za-z0-9]{16,})\b"), True),
        (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), True),
        (re.compile(r"(?i)\b(?:app|app_pass|password|passwd|pw|secret|token|api_key)\s*[:=]\s*"
                    r"[\"'][A-Za-z0-9!@#$%^&*_\- ]{12,}[\"']"), True),
    ]
    _BUILTIN_OK = re.compile(r"(?i)<[^>]*>|\$\{|os\.environ|getenv|placeholder|example|redact|xxxx|your[_-]")

    def scan_secret(path):
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        for rx, high in _BUILTIN_SECRETS:
            for m in rx.finditer(text):
                ls = text.rfind("\n", 0, m.start()) + 1
                le = text.find("\n", m.end())
                line = text[ls: le if le >= 0 else len(text)]
                if _BUILTIN_OK.search(line):
                    continue
                if not high and not re.search(r"pass|pwd|credential|auth|token|api[_ ]?key|\bkey\b|login|secret",
                                              text[max(0, m.start() - 120): m.end() + 120].lower()):
                    continue
                return f"line {text.count(chr(10), 0, m.start()) + 1}"
        return None

SECTIONS = [
    ("purpose", "Purpose"),
    ("trigger", "Trigger / cadence"),
    ("inputs", "Inputs"),
    ("steps", "Steps"),
    ("output", "Output"),
    ("receipt", "Receipt"),
    ("failure", "Failure modes"),
    ("owner", "Owner + history"),
]
SNAPSHOT_MAX_AGE_DAYS = 3
ACTIVITY_WINDOW_DAYS = 14

DATE = re.compile(r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?!\d)")
MD_PATH = re.compile(r"([A-Za-z0-9_.\-/]+\.md)\b")
TO_WRITE = re.compile(r"\(\s*to\s+write\s*\)", re.I)
NO_RUNBOOK = re.compile(r"\(\s*(retired|disabled)\s*\)", re.I)
TRIGGER_ID = re.compile(r"\btrig_[A-Za-z0-9]{8,}\b")
NOTE_NAME = re.compile(r"^(20\d{2}-\d{2}-\d{2})-(.+)\.md$")
COMMENT = re.compile(r"<!--.*?-->", re.S)
PLACEHOLDER = re.compile(
    r"^\s*(?:[-*]\s*)?(?:(?:todo|tbd)\b.*|to\s+write|fill\s+(?:this\s+)?in|\.{3}|…|<[^<>]+>)\s*[.:]?\s*$",
    re.I)

COLD_READ = re.compile(r"^Cold read:\s*(20\d{2}-\d{2}-\d{2})\b.*?(\d+)\s+open question", re.M | re.I)
CARD = re.compile(r"(?<![0-9])[0-9](?:[ -]?[0-9]){12,18}(?![0-9])")


def _luhn(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


_KNOWN = ("--quiet", "--write-status", "--today", "--root", "--help", "-h")


class Finding:
    __slots__ = ("severity", "agent", "path", "message")

    def __init__(self, severity, agent, path, message):
        self.severity, self.agent, self.path, self.message = severity, agent, path, message

    def __repr__(self):
        return f"{self.severity.upper():5} {self.path}: {self.message}"


# ---------------------------------------------------------------- parsing helpers

def _parse_date(text):
    m = DATE.search(text or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


SEPARATOR = re.compile(r":?-{3,}:?")


def parse_index(text):
    """Return (rows, problem) across EVERY task table in the file (a registry may split
    enabled, one-time and disabled jobs into separate tables).
    rows = [(line_no, task, runbook_cell, raw_line)]."""
    lines = text.splitlines()
    fenced = [f for _, f in fence_states(lines)]
    rows, tables, i = [], 0, 0
    while i < len(lines):
        cells = None if fenced[i] else _cells(lines[i])
        starts_table = cells and (i == 0 or fenced[i - 1] or _cells(lines[i - 1]) is None)
        nxt = _cells(lines[i + 1]) if i + 1 < len(lines) and not fenced[i + 1] else None
        if not (starts_table and nxt and all(SEPARATOR.fullmatch(x) for x in nxt if x)):
            i += 1
            continue
        low = [c.lower() for c in cells]
        col = lambda word: next((k for k, c in enumerate(low) if word in c), None)  # noqa: E731
        t, c, r = col("task"), col("cadence"), col("runbook")
        j = i + 2
        while j < len(lines) and not fenced[j] and _cells(lines[j]) is not None:
            if t is not None and c is not None and r is not None:
                row = _cells(lines[j])
                row = row + [""] * (max(t, r) + 1 - len(row))
                rows.append((j + 1, row[t], row[r], lines[j]))
            j += 1
        if t is not None and c is not None and r is not None:
            tables += 1
        i = j
    if not tables:
        return [], "no task table (header needs Task, Cadence and Runbook columns)"
    return rows, None


def resolve_cell(agent, cell):
    """Return (kind, relpath). kind: path | to_write | no_runbook | missing."""
    if NO_RUNBOOK.search(cell) and not MD_PATH.search(cell):
        return "no_runbook", None
    m = MD_PATH.search(cell)
    if not m:
        return "missing", None
    raw = m.group(1).lstrip("./")
    if raw.startswith("runbooks/"):
        rel = raw
    else:
        rel = f"runbooks/{agent}/{raw}"
    kind = "to_write" if TO_WRITE.search(cell) else "path"
    if NO_RUNBOOK.search(cell):
        kind = "no_runbook"
    return kind, rel


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")


def fence_states(lines):
    """Yield (line, inside_fence) honouring CommonMark fence length, so a prompt quoted
    inside a ```` fence can itself contain ``` blocks and '## ' lines without being
    mistaken for runbook structure."""
    opener = None
    for line in lines:
        m = FENCE.match(line)
        if opener is None:
            if m:
                opener = m.group(1)
                yield line, True
                continue
            yield line, False
        else:
            if m and m.group(1)[0] == opener[0] and len(m.group(1)) >= len(opener) and not m.group(2).strip():
                opener = None
            yield line, True


def split_sections(text):
    """Map section key -> body text for level-2 headings."""
    found = {}
    current, buf = None, []
    for line, fenced in fence_states(text.splitlines()):
        if not fenced and line.startswith("## "):
            if current is not None:
                found.setdefault(current, "\n".join(buf))
            current, buf = _section_key(line[3:]), []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        found.setdefault(current, "\n".join(buf))
    found.pop(None, None)
    return found


def _section_key(heading):
    h = re.sub(r"^[\s\d.)(]+", "", heading).strip().lower()
    h = re.sub(r"[^a-z/+ ]", "", h)
    if h.startswith("purpose"):
        return "purpose"
    if "trigger" in h or "cadence" in h:
        return "trigger"
    if h.startswith("input"):
        return "inputs"
    if h.startswith("step"):
        return "steps"
    if h.startswith("output"):
        return "output"
    if h.startswith("receipt"):
        return "receipt"
    if h.startswith("failure"):
        return "failure"
    if h.startswith("owner"):
        return "owner"
    return None


def is_substantive(body):
    text = COMMENT.sub("", body or "")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return any(not PLACEHOLDER.match(ln) for ln in lines)


# ---------------------------------------------------------------- the check

def load_agents(root):
    path = root / "runbooks" / "agents.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"cannot read runbooks/agents.json: {exc}"
    return data, None


def check(root, today):
    root = Path(root)
    findings = []
    status = {}

    def add(sev, agent, path, msg):
        findings.append(Finding(sev, agent, str(path), msg))

    if _SECRET_IMPORT_ERROR and (root / "tools" / "sync_runtime.py").is_file():
        add("error", "-", "tools/sync_runtime.py",
            f"the house secret guard is present but did not import ({_SECRET_IMPORT_ERROR}); "
            f"checked with the built-in patterns only — fix the import")

    cfg, err = load_agents(root)
    if err:
        add("error", "-", "runbooks/agents.json", err)
        cfg = {"agents": []}
    registry_due = _parse_date(cfg.get("registry_due", "")) or datetime.date(2026, 10, 19)
    runbooks_due = _parse_date(cfg.get("runbooks_due", "")) or datetime.date(2026, 10, 24)
    expected = {a["dir"]: a for a in cfg.get("agents", []) if a.get("dir")}

    rb_root = root / "runbooks"
    present = sorted(p.name for p in rb_root.iterdir()
                     if p.is_dir() and not p.name.startswith(("_", "."))) if rb_root.is_dir() else []
    agents = sorted(set(present) | set(expected))
    all_runbook_text = {}

    for agent in agents:
        st = status.setdefault(agent, {"name": expected.get(agent, {}).get("name", agent),
                                       "expected": agent in expected, "registry": False,
                                       "rows": 0, "ok": 0, "to_write": 0, "failing": 0,
                                       "retired": 0, "errors": 0, "cold_read": 0, "handover_ready": 0})
        adir = rb_root / agent
        index = adir / "INDEX.md"
        if not index.is_file():
            if agent in expected:
                sev = "error" if today > registry_due else "warning"
                add(sev, agent, f"runbooks/{agent}/INDEX.md",
                    f"no registry — due {registry_due.isoformat()}")
            else:
                add("error", agent, f"runbooks/{agent}/", "folder has no INDEX.md")
            listed = set()
        else:
            st["registry"] = True
            rows, problem = parse_index(index.read_text(encoding="utf-8", errors="replace"))
            if problem:
                add("error", agent, f"runbooks/{agent}/INDEX.md", problem)
            listed = set()
            for line_no, task, cell, _raw in rows:
                st["rows"] += 1
                where = f"runbooks/{agent}/INDEX.md:{line_no}"
                kind, rel = resolve_cell(agent, cell)
                if kind == "no_runbook":
                    st["retired"] += 1
                    continue
                if kind == "missing":
                    add("error", agent, where, f"row '{task}' has no runbook path, (to write), (retired) or (disabled)")
                    st["failing"] += 1
                    continue
                if not rel.startswith(f"runbooks/{agent}/"):
                    add("error", agent, where, f"row '{task}' points outside runbooks/{agent}/: {rel}")
                    st["failing"] += 1
                    continue
                if rel in listed:
                    add("error", agent, where, f"{rel} is listed twice")
                    continue
                listed.add(rel)
                exists = (root / rel).is_file()
                if kind == "to_write" and not exists:
                    st["to_write"] += 1
                    sev = "error" if today > runbooks_due else "warning"
                    add(sev, agent, where, f"'{task}' runbook still to write — due {runbooks_due.isoformat()}")
                    continue
                if not exists:
                    add("error", agent, where, f"{rel} does not exist (mark it '(to write)' or fix the path)")
                    st["failing"] += 1
                    continue
                problems = check_runbook(root / rel)
                all_runbook_text[rel] = (root / rel).read_text(encoding="utf-8", errors="replace")
                if problems:
                    st["failing"] += 1
                    for p in problems:
                        add("error", agent, rel, p)
                else:
                    st["ok"] += 1
                cr = cold_read(all_runbook_text[rel])
                if cr is not None:
                    st["cold_read"] += 1
                    st["handover_ready"] += 1 if cr[1] == 0 else 0
        if adir.is_dir():
            for f in sorted(adir.glob("*.md")):
                rel = f"runbooks/{agent}/{f.name}"
                if f.name == "INDEX.md" or rel in listed:
                    continue
                add("error", agent, rel, "runbook is not listed in INDEX.md")
                all_runbook_text.setdefault(rel, f.read_text(encoding="utf-8", errors="replace"))

    _check_claude_scheduler(root, today, add, status)
    _check_grok_routines(root, all_runbook_text, add)
    activity = _note_activity(root, today, expected)
    for agent, info in activity.items():
        if agent in status:
            status[agent]["notes"] = info
    for f in findings:
        if f.severity == "error" and f.agent in status:
            status[f.agent]["errors"] += 1
    return findings, status, activity


def cold_read(text):
    """(date, open_questions) from the newest 'Cold read:' line, or None. An independent
    agent that has never seen the job reads the runbook alone and counts the questions it
    would have to ask; zero means handover-ready. Tracked, never an error: a machine cannot
    judge whether a runbook is clear — only a cold reader can."""
    hits = [(m.group(1), int(m.group(2))) for m in COLD_READ.finditer(COMMENT.sub("", text or ""))]
    return max(hits) if hits else None


def check_runbook(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    problems = []
    found = split_sections(text)
    for key, label in SECTIONS:
        if key not in found:
            problems.append(f"missing section '{label}'")
        elif not is_substantive(found[key]):
            problems.append(f"section '{label}' is empty or a placeholder")
    owner = found.get("owner")
    if owner and is_substantive(owner) and not DATE.search(COMMENT.sub("", owner)):
        problems.append("'Owner + history' has no date (YYYY-MM-DD) for the last successful run")
    reason = scan_secret(path)
    if reason:
        problems.append(f"looks like a credential at {reason} — name the store and key, never the value")
    for m in CARD.finditer(text):
        digits = re.sub(r"[^0-9]", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits):
            problems.append(f"looks like a payment card number at line {text.count(chr(10), 0, m.start()) + 1} "
                            f"— last four digits only")
            break
    return problems


def _check_claude_scheduler(root, today, add, status):
    snap_path = root / "runbooks" / "claude" / "scheduler-snapshot.json"
    if not (root / "runbooks" / "claude").is_dir() and not snap_path.exists():
        return
    rel = "runbooks/claude/scheduler-snapshot.json"
    if not snap_path.is_file():
        add("error", "claude", rel, "Claude scheduler snapshot missing — Claude's jobs are invisible to every other agent")
        return
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add("error", "claude", rel, f"snapshot is not valid JSON: {exc}")
        return
    generated = _parse_date(snap.get("generated_at", ""))
    if generated is None:
        add("error", "claude", rel, "snapshot has no generated_at date")
    elif (today - generated).days > SNAPSHOT_MAX_AGE_DAYS:
        add("error", "claude", rel,
            f"snapshot is {(today - generated).days} days old — the daily export job stopped "
            f"(runbooks/claude/claude-scheduler-export.md)")
    index = root / "runbooks" / "claude" / "INDEX.md"
    index_text = index.read_text(encoding="utf-8", errors="replace") if index.is_file() else ""
    rows_by_trigger = {}
    for line in index_text.splitlines():
        for tid in TRIGGER_ID.findall(line):
            rows_by_trigger.setdefault(tid, line)
    uncovered = 0
    for trig in snap.get("triggers", []):
        if not trig.get("enabled"):
            continue
        tid = trig.get("id", "")
        line = rows_by_trigger.get(tid)
        if line is None:
            uncovered += 1
            add("error", "claude", "runbooks/claude/INDEX.md",
                f"enabled scheduled task {tid} ('{trig.get('name', '')}') has no row")
            continue
        cells = _cells(line) or []
        kind, relpath = resolve_cell("claude", " ".join(cells))
        if kind != "path" or not relpath or not (root / relpath).is_file():
            uncovered += 1
            add("error", "claude", "runbooks/claude/INDEX.md",
                f"enabled scheduled task {tid} ('{trig.get('name', '')}') has no runbook file")
    if "claude" in status:
        status["claude"]["scheduler"] = {
            "generated_at": snap.get("generated_at"),
            "enabled": sum(1 for t in snap.get("triggers", []) if t.get("enabled")),
            "total": len(snap.get("triggers", [])),
            "uncovered": uncovered,
        }


def _check_grok_routines(root, runbook_text, add):
    inv_path = root / "grok-bot" / "routine-inventory.json"
    if not inv_path.is_file():
        return
    try:
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        add("warning", "tanner", "grok-bot/routine-inventory.json", "not valid JSON — Grok coverage NOT CHECKED")
        return
    haystack = "\n".join(runbook_text.values()).lower()
    verified = inv.get("verified_date", "an unknown date")
    for bot in inv.get("bots", []):
        names = [(r.get("name") or "").strip() for r in bot.get("routines", []) or []]
        missing = [n for n in names if n and n.lower() not in haystack]
        if missing:
            add("warning", "tanner", "grok-bot/routine-inventory.json",
                f"Grok desk '{bot.get('name')}': {len(missing)} of {len(names)} routines (inventory of "
                f"{verified}) appear in no runbook — {'; '.join(missing)}")


def _note_activity(root, today, expected):
    """Agent-notes filed in the last ACTIVITY_WINDOW_DAYS, attributed by filename prefix."""
    notes_dir = root / "agent-notes"
    prefixes = sorted(((p, a) for a, cfg in expected.items() for p in cfg.get("note_prefixes", [])),
                      key=lambda x: -len(x[0]))
    out = {}
    if not notes_dir.is_dir():
        return out
    for f in notes_dir.iterdir():
        m = NOTE_NAME.match(f.name)
        if not m:
            continue
        d = _parse_date(m.group(1))
        if d is None or (today - d).days > ACTIVITY_WINDOW_DAYS or d > today:
            continue
        rest = m.group(2).lower()
        agent = next((a for p, a in prefixes if rest == p or rest.startswith(p + "-")), "(unattributed)")
        info = out.setdefault(agent, {"count": 0, "last": None})
        info["count"] += 1
        info["last"] = max(info["last"] or d, d)
    return out


# ---------------------------------------------------------------- reporting

def render_status(findings, status, activity, today):
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    missing_registries = sum(1 for a, s in status.items() if s["expected"] and not s["registry"])
    to_write = sum(s["to_write"] for s in status.values())
    failing = sum(s["failing"] for s in status.values())
    uncovered = status.get("claude", {}).get("scheduler", {}).get("uncovered", 0)
    undocumented = missing_registries + to_write + failing + uncovered

    out = []
    out.append("# Runbook status — who has documented what")
    out.append("")
    out.append("<!-- GENERATOR-OWNED: tools/lint_runbooks.py --write-status. Do not hand-edit. -->")
    out.append("")
    if undocumented == 0 and not errors:
        out.append(f"**Every expected agent has a registry and every listed task has a passing runbook** (as of {today.isoformat()}).")
    else:
        out.append(f"**{undocumented} gaps left** (as of {today.isoformat()}): "
                   f"{missing_registries} agents with no task list, {to_write} runbooks still to write, "
                   f"{failing} runbooks failing the standard, {uncovered} Claude scheduled tasks not covered.")
    out.append("")
    out.append("Standard: `runbooks/README.md`. Registries due 2026-10-19; runbooks due 2026-10-24.")
    out.append("")
    out.append("| Agent | Task list | Tasks | Runbooks passing | Handover-ready (cold read, 0 questions) | To write | Failing | No runbook needed | Run notes, last 14 days |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for agent in sorted(status, key=lambda a: (not status[a]["expected"], a)):
        s = status[agent]
        notes = s.get("notes") or activity.get(agent)
        note_txt = f"{notes['count']} (last {notes['last'].isoformat()})" if notes else "0"
        reg = "yes" if s["registry"] else "**missing**"
        ready = f"{s['handover_ready']} of {s['cold_read']} cold-read" if s["cold_read"] else "none cold-read"
        out.append(f"| {s['name']} (`runbooks/{agent}/`) | {reg} | {s['rows']} | {s['ok']} | {ready} | "
                   f"{s['to_write']} | {s['failing']} | {s['retired']} | {note_txt} |")
    sched = status.get("claude", {}).get("scheduler")
    if sched:
        out.append("")
        out.append(f"Claude scheduler snapshot: {sched['total']} scheduled tasks, {sched['enabled']} enabled, "
                   f"{sched['uncovered']} not covered by a runbook. Snapshot taken {sched['generated_at']}.")
    unattributed = activity.get("(unattributed)")
    if unattributed:
        out.append("")
        out.append(f"Run notes not matched to any agent in `runbooks/agents.json`: {unattributed['count']} "
                   f"in the last 14 days. If one of them is a recurring job, its agent belongs in that file.")
    out.append("")
    out.append("## Details (skip unless something looks wrong)")
    out.append("")
    if not findings:
        out.append("No findings.")
    for f in errors + warnings:
        out.append(f"- {f.severity.upper()} `{f.path}` — {f.message}")
    out.append("")
    return "\n".join(out)


def main(argv):
    quiet = write_status = False
    today = datetime.date.today()
    root = DEFAULT_ROOT
    for arg in argv[1:]:
        name = arg.split("=", 1)[0]
        if name in ("--help", "-h"):
            print(__doc__.strip())
            return 0
        if name not in _KNOWN:
            print(f"unrecognised argument: {arg}\n\n{__doc__.strip()}")
            return 2
        if name == "--quiet":
            quiet = True
        elif name == "--write-status":
            write_status = True
        elif name == "--today":
            d = _parse_date(arg.split("=", 1)[1] if "=" in arg else "")
            if d is None:
                print("--today needs YYYY-MM-DD")
                return 2
            today = d
        elif name == "--root":
            if "=" not in arg:
                print("--root needs a path")
                return 2
            root = Path(arg.split("=", 1)[1])

    findings, status, activity = check(root, today)
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    if write_status:
        (Path(root) / "runbooks" / "STATUS.md").write_text(
            render_status(findings, status, activity, today), encoding="utf-8")
    if not quiet:
        for f in errors + warnings:
            print(repr(f))
    agents_with_registry = sum(1 for s in status.values() if s["registry"])
    print(f"runbooks: {len(errors)} error(s), {len(warnings)} warning(s); "
          f"{agents_with_registry}/{len(status)} agents have a registry; as of {today.isoformat()}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
