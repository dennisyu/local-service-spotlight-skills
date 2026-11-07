#!/usr/bin/env python3
"""Check an installed copy of this skill pack against this repository's skills/.

Answers "do I actually have every skill, and the current text?" for any runtime
that keeps the pack on disk — Claude, Codex, Cursor, a member's laptop — by
content, not by folder name.

    python3 scripts/check_installed_parity.py --installed <installed skills dir>
    python3 scripts/check_installed_parity.py --installed <dir> --json report.json

Run it from a checkout, or copy the whole scripts/ folder: it imports
validate_marketplace.py, which imports standards_lib.py. --repository may point
at any checkout or export of this repository (for example a `git archive` of
main), so a runtime that may not clone can still compare against main.

Per skill it reports one state:

    identical          every file matches byte for byte, or differs only in
                       Windows (CRLF) line endings, which the record notes
    frontmatter-only   SKILL.md differs only in how its YAML frontmatter is
                       written (quotes, list indent, folded lines); the values
                       match and the body matches exactly
    drift              the SKILL.md body (even only its leading or trailing
                       whitespace, which the reason says) or another file
                       differs, or a file is missing from the install
    missing            in this repository, not installed
    extra              installed, not in this repository (reported, never
                       failed: a local skill may be deliberate)

It also lists repository SKILL.md files whose frontmatter a strict YAML parser
would reject, because a strict loader may skip them while a lenient one loads
them, which reads as "missing" on one runtime and "fine" on another.

Ignored on both sides: dot-files and dot-folders, ``__pycache__`` folders and
``*.pyc``/``*.pyo``/``*.pyd`` files. The repository's .gitignore already keeps
those out of the library, and running a skill's script in place creates them,
so they would otherwise report a clean install as drifted.

Exit 0: nothing missing and nothing drifted. Exit 1: missing or drift.
Exit 2: bad arguments. Standard library only; PyYAML is used when present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_marketplace import frontmatter_yaml_problems  # noqa: E402

try:  # optional: a real parser makes the frontmatter comparison exact
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised when PyYAML is absent
    yaml = None

REPOSITORY = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lf_bytes(path: Path) -> bytes:
    """File bytes with Windows (CRLF) line endings read as plain LF."""
    return path.read_bytes().replace(b"\r\n", b"\n")


_IGNORED_DIR_NAMES = frozenset({"__pycache__"})
_IGNORED_SUFFIXES = (".pyc", ".pyo", ".pyd")


def _ignored(relative: Path) -> bool:
    """Leftovers the library never ships: dot-files, bytecode caches."""
    return (
        any(part.startswith(".") or part in _IGNORED_DIR_NAMES for part in relative.parts)
        or relative.suffix in _IGNORED_SUFFIXES
    )


def _files(skill_dir: Path) -> dict[str, Path]:
    return {
        path.relative_to(skill_dir).as_posix(): path
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file() and not _ignored(path.relative_to(skill_dir))
    }


def _skill_names(skills_dir: Path) -> list[str]:
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and not _ignored(Path(p.name)))


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter text or None, body). CRLF line endings are read as LF."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 4 :]


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner.replace('\\"', '"')
    return value


def _block_scalar(indicator: str, lines: list[str]) -> str:
    """Fold or keep a YAML block scalar (``|``, ``>``, with ``-``/``+`` chomping)."""
    indents = [len(line) - len(line.lstrip(" ")) for line in lines if line.strip()]
    cut = min(indents) if indents else 0
    stripped = [line[cut:] if line.strip() else "" for line in lines]
    if indicator.startswith("|"):
        text = "\n".join(stripped)
    else:
        paragraphs, current = [], []
        for line in stripped:
            if line:
                current.append(line)
            else:
                paragraphs.append(" ".join(current))
                current = []
        paragraphs.append(" ".join(current))
        text = "\n".join(paragraphs)
    text = text.rstrip("\n")
    if "-" in indicator:
        return text
    return text + "\n"


def _lenient_mapping(frontmatter: str) -> dict[str, object]:
    """Small reader for the frontmatter shape this pack uses.

    Handles ``key: value`` (quoted or not), block scalars (``key: >-`` and
    ``key: |`` with indented lines) and ``key:`` followed by ``- item`` lines at
    any indent. Good enough to tell re-quoting, re-indenting and flattening a
    folded description apart from a real change when PyYAML is not installed.
    """
    mapping: dict[str, object] = {}
    lines = frontmatter.splitlines()
    current: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and current is not None:
            existing = mapping.get(current)
            items = existing if isinstance(existing, list) else []
            items.append(_unquote(item.group(1)))
            mapping[current] = items
            index += 1
            continue
        pair = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not pair:
            index += 1
            continue
        current, raw = pair.group(1), pair.group(2).strip()
        if re.fullmatch(r"[|>][+-]?[1-9]?|[|>][1-9]?[+-]?", raw):
            block: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index].startswith((" ", "\t"))):
                block.append(lines[index])
                index += 1
            # a folded/literal description compares by its text, not its trailing newline
            mapping[current] = _block_scalar(raw, block).rstrip("\n")
            continue
        mapping[current] = _unquote(raw) if raw else []
        index += 1
    return mapping


def frontmatter_values(frontmatter: str) -> dict[str, object]:
    if yaml is not None:
        try:
            loaded = yaml.safe_load(frontmatter)
            if isinstance(loaded, dict):
                return loaded
        except yaml.YAMLError:
            pass
    return _lenient_mapping(frontmatter)


def compare_skill(repo_dir: Path, installed_dir: Path) -> dict[str, object]:
    repo_files = _files(repo_dir)
    installed_files = _files(installed_dir)
    differing: list[str] = []
    line_endings_only: list[str] = []
    for name in sorted(set(repo_files) | set(installed_files)):
        if name not in repo_files or name not in installed_files:
            differing.append(name)
        elif _sha256(repo_files[name]) == _sha256(installed_files[name]):
            continue
        elif _lf_bytes(repo_files[name]) == _lf_bytes(installed_files[name]):
            line_endings_only.append(name)
        else:
            differing.append(name)
    notes = (
        [f"line endings differ (CRLF vs LF), text identical: {', '.join(line_endings_only)}"]
        if line_endings_only
        else []
    )

    def record(state: str, **extra: object) -> dict[str, object]:
        result: dict[str, object] = {"state": state, "files": len(repo_files), **extra}
        if notes:
            result["notes"] = notes
        return result

    if not differing:
        return record("identical")

    reasons: list[str] = []
    for name in differing:
        if name not in installed_files:
            reasons.append(f"{name}: missing from install")
            continue
        if name not in repo_files:
            reasons.append(f"{name}: only in install")
            continue
        if name != "SKILL.md":
            reasons.append(f"{name}: content differs")
            continue
        repo_fm, repo_body = split_frontmatter(_lf_bytes(repo_files[name]).decode("utf-8"))
        inst_fm, inst_body = split_frontmatter(_lf_bytes(installed_files[name]).decode("utf-8"))
        if repo_body != inst_body:
            if repo_body.strip() == inst_body.strip():
                reasons.append("SKILL.md: body differs only in leading or trailing whitespace")
            else:
                reasons.append("SKILL.md: body differs")
        elif repo_fm is None or inst_fm is None:
            reasons.append("SKILL.md: frontmatter missing on one side")
        elif frontmatter_values(repo_fm) != frontmatter_values(inst_fm):
            reasons.append("SKILL.md: frontmatter values differ")

    if differing == ["SKILL.md"] and not reasons:
        return record("frontmatter-only")
    return record("drift", reasons=reasons)


def check(installed: Path, repository: Path = REPOSITORY) -> dict[str, object]:
    repo_skills = repository / "skills"
    repo_names = _skill_names(repo_skills)
    installed_names = _skill_names(installed)

    skills: dict[str, dict[str, object]] = {}
    for name in repo_names:
        if name not in installed_names:
            skills[name] = {"state": "missing"}
        else:
            skills[name] = compare_skill(repo_skills / name, installed / name)
    for name in installed_names:
        if name not in repo_names:
            skills[name] = {"state": "extra"}

    strict_yaml: dict[str, list[str]] = {}
    for name in repo_names:
        skill_file = repo_skills / name / "SKILL.md"
        if skill_file.is_file():
            problems = frontmatter_yaml_problems(skill_file.read_text(encoding="utf-8"))
            if problems:
                strict_yaml[name] = problems

    counts: dict[str, int] = {}
    for record in skills.values():
        counts[str(record["state"])] = counts.get(str(record["state"]), 0) + 1
    return {
        "repository_skills": len(repo_names),
        "installed_skills": len(installed_names),
        "counts": dict(sorted(counts.items())),
        "skills": skills,
        "repository_frontmatter_strict_yaml_problems": strict_yaml,
        "frontmatter_compare": "pyyaml" if yaml is not None else "lenient reader",
        "ok": counts.get("missing", 0) == 0 and counts.get("drift", 0) == 0,
    }


def _print_report(report: dict[str, object]) -> None:
    counts = report["counts"]
    print(
        f"Installed {report['installed_skills']} of {report['repository_skills']} repository skills. "
        + ", ".join(f"{state} {count}" for state, count in counts.items())
    )
    for name, record in report["skills"].items():
        if record["state"] in {"missing", "drift", "extra"}:
            detail = "; ".join(record.get("reasons", []))
            print(f"- {record['state']}: {name}" + (f" ({detail})" if detail else ""))
    for name, problems in report["repository_frontmatter_strict_yaml_problems"].items():
        print(f"- strict YAML would reject skills/{name}/SKILL.md: {'; '.join(problems)}")
    print("PASS: nothing missing, nothing drifted." if report["ok"] else "FAIL: missing or drifted skills above.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--installed", required=True, help="directory that holds the installed skill folders")
    parser.add_argument("--repository", default=str(REPOSITORY), help="repository root (default: this checkout)")
    parser.add_argument("--json", help="also write the full report to this file")
    args = parser.parse_args(argv)

    installed = Path(args.installed)
    repository = Path(args.repository)
    if not installed.is_dir():
        print(f"--installed is not a directory: {installed}", file=sys.stderr)
        return 2
    if not (repository / "skills").is_dir():
        print(f"--repository has no skills/ directory: {repository}", file=sys.stderr)
        return 2

    report = check(installed, repository)
    _print_report(report)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
