"""Action register -> Basecamp to-dos that an agent (or a person) can pick up and finish.

Each to-do carries everything the executor needs: the finding and evidence, the routed
skill, the exact destination, the human gate, and the observable acceptance test. Agent
to-dos also carry a ready-to-run brief, so whichever agent claims the to-do starts work
without re-reading the audit. Human to-dos are kept few and specific: approvals,
recordings, sign-ins and relationship asks only.

Output is plain JSON for `python3 -m basecamp`, the Basecamp MCP server, or the Basecamp
API (POST /buckets/{id}/todolists/{id}/todos.json with content, description, due_on).
"""
from __future__ import annotations

import html
import json
import pathlib
import re

from .ledger import Ledger

HUMAN_WORDS = re.compile(r"\b(record|film|shoot|sign in|log ?in|call|meet|approve|decide|choose|confirm|interview|"
                         r"introduce|ask|send us|provide|supply|share access|grant|pay|sign)\b", re.I)


def executor(a: dict) -> str:
    if a.get("executor"):
        return a["executor"]
    text = f"{a.get('action', '')} {a.get('dependency', '')}"
    if HUMAN_WORDS.search(a.get("action", "")):
        return "HUMAN"
    gate = (a.get("human_gate") or "").strip()
    if gate and not re.fullmatch(r"(none|n/?a|-|no gate)\.?", gate, re.I):  # "None for schema; X approves" is a gate
        return "AGENT_AFTER_APPROVAL"
    return "AGENT" if not HUMAN_WORDS.search(text) else "AGENT_AFTER_APPROVAL"


def brief(a: dict, subject: str, ledger: Ledger | None) -> str:
    facts = []
    for e in a.get("evidence") or []:
        r = ledger.get(e) if ledger else None
        if r:
            facts.append(f"{e}: {r['claim']} — {r['value'][:140]} ({r['source']}{', ' + r['url'] if r['url'] else ''})")
        else:
            facts.append(e)
    return (f"You are the {a.get('skill', 'assigned')} agent for {subject}.\n"
            f"Task {a.get('id')}: {a.get('action')}\n"
            f"Why (evidence):\n  - " + "\n  - ".join(facts) + "\n"
            f"Destination: {a.get('destination')}\n"
            f"Depends on: {a.get('dependency')}\n"
            f"Gate: {a.get('human_gate')} — stage the change; do not publish, send or spend until that gate is cleared.\n"
            f"Done when: {a.get('acceptance_test')}\n"
            f"Close the to-do with one line: Verified: <what you opened> — <what you saw> — <when>.")


AGENTS_FILE = pathlib.Path(__file__).resolve().parents[1] / "config" / "agents.json"


def load_agents(path: str | pathlib.Path | None = None) -> dict:
    p = pathlib.Path(path) if path else AGENTS_FILE
    return json.loads(p.read_text()) if p.exists() else {"default_agent": "", "functions": {}, "chaser": ""}


def assignee(a: dict, ex: str, agents: dict) -> str:
    """The running agent (or person) who picks this to-do up — never just a function name."""
    if a.get("agent"):
        return a["agent"]
    if ex == "HUMAN":
        return agents.get("human_owner", "the client")
    return agents.get("functions", {}).get(a.get("function", ""), agents.get("default_agent", ""))


def todos(audit: dict, ledger: Ledger | None = None, agents: dict | None = None) -> dict:
    subject = audit.get("meta", {}).get("subject", "")
    agents = agents if agents is not None else load_agents()
    items = []
    for a in audit.get("actions", []):
        ex = executor(a)
        who = assignee(a, ex, agents)
        tag = {"AGENT": "🤖 Agent", "AGENT_AFTER_APPROVAL": "🤖 Agent after approval", "HUMAN": "🙋 Human"}[ex]
        desc = [f"<div><strong>{tag}</strong> · {html.escape(a.get('function', ''))} · skill <code>{html.escape(a.get('skill', ''))}</code></div>",
                f"<div><strong>Runs it:</strong> {html.escape(who)} · <strong>Chased by:</strong> {html.escape(agents.get('chaser', ''))}</div>",
                f"<div><strong>Finding:</strong> {html.escape(a.get('finding', '') or a.get('action', ''))} "
                f"(evidence {html.escape(', '.join(a.get('evidence') or []))})</div>",
                f"<div><strong>Destination:</strong> {html.escape(a.get('destination', ''))}</div>",
                f"<div><strong>Gate:</strong> {html.escape(a.get('human_gate', ''))}</div>",
                f"<div><strong>Done when:</strong> {html.escape(a.get('acceptance_test', ''))}</div>"]
        if ex != "HUMAN":
            desc.append("<div><strong>Agent brief</strong></div><pre>" + html.escape(brief(a, subject, ledger)) + "</pre>")
        items.append({"id": a.get("id"), "content": f"[{a.get('id')}] {a.get('action')}", "description": "".join(desc),
                      "due_on": str(a.get("due", ""))[:10], "executor": ex, "function": a.get("function", ""),
                      "agent": who, "chaser": agents.get("chaser", ""),
                      "skill": a.get("skill", ""), "window": a.get("window")})
    counts = {k: sum(1 for i in items if i["executor"] == k) for k in ("AGENT", "AGENT_AFTER_APPROVAL", "HUMAN")}
    unassigned = [i["id"] for i in items if i["executor"] != "HUMAN" and not i["agent"]]
    return {"todolist": f"Audit Execution — {subject}", "counts": counts, "unassigned": unassigned, "todos": items}


def markdown(payload: dict) -> str:
    c = payload["counts"]
    out = [f"# {payload['todolist']}", "",
           f"{c['AGENT']} agent · {c['AGENT_AFTER_APPROVAL']} agent after approval · {c['HUMAN']} human", "",
           "| Due | ID | To-do | Executor | Runs it | Skill |", "|---|---|---|---|---|---|"]
    for t in sorted(payload["todos"], key=lambda x: x["due_on"]):
        out.append(f"| {t['due_on']} | {t['id']} | {t['content'][len(t['id']) + 3:]} | {t['executor']} | {t.get('agent', '')} | {t['skill']} |")
    return "\n".join(out) + "\n"
