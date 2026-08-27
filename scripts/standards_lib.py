#!/usr/bin/env python3
"""Read, validate, and compile the house rules in ``standards/``.

One rule lives in exactly one file. That file is the only place the rule is
written down, and three different things are generated from it:

1. **Content**  — the prose body is embedded verbatim in ``AGENTS.md`` and in
   every distributed ``SKILL.md`` (``sync_shared_rules.py``), so the rule
   travels inside each self-contained skill to everyone who installs the pack.
2. **Checklist** — the same prose is what a human reads pre-flight.
3. **Software** — the ``checks`` block is compiled into the live fleet sweep
   (``fleet_check.py``), so a violation on a published page is caught without
   anyone remembering to look.

That is Content · Checklist · Software from a single source. It matters that it
is a *single* source: the moment the sweep is hand-written separately from the
rule, the two drift, and the sweep starts passing sites that break the rule.

File format
-----------

    ---
    { ...JSON header... }
    ---

    ## Human-readable rule

    - body ...

The header is JSON, not YAML, on purpose. A rules engine that silently
mis-parses a rule is worse than no rules engine, and JSON cannot be
mis-parsed into something that merely looks right.

Header fields
-------------

===================  ========  ====================================================
field                required  meaning
===================  ========  ====================================================
``title``            yes       one line, matches the body's ``##`` heading
``severity``         yes       ``error`` (blocks) or ``warn`` (reports)
``captured``         yes       ISO date the rule entered ``standards/``
``captured_from``    yes       where it was said. Provenance is not decoration:
                               it is how we see which channels leak. If Zoom
                               calls never appear here, Zoom calls are not being
                               captured.
``source``           no        canonical article URL
``applies_to``       no        subset of ``published-html``, ``agent-behaviour``,
                               ``design-review`` (default: agent-behaviour)
``target_tags``      no        only sweep pages tagged with one of these. A rule
                               for personal-brand sites should not fire on a
                               product site; a sweep that cries wolf gets
                               ignored, and then the real findings go unread.
``checks``           no        list of machine checks; absent means the rule is a
                               judgement call and is enforced by reading, not
                               grepping. Say so rather than faking a regex.
===================  ========  ====================================================

Check kinds
-----------

``forbid_regex``   ``pattern`` must NOT appear in fetched HTML.
``require_regex``  ``pattern`` MUST appear.
``resolve_urls``   every URL matched by ``extract`` must return an allowed
                   status. An optional ``within`` regex narrows the document
                   first, so "every URL inside the ``sameAs`` array" and "every
                   outbound ``href``" are the same primitive.
``require_paths``  every listed path must resolve on the target's own origin.
                   The only check that tests a URL the page does not link to —
                   which is exactly what a URL printed on a QR code is.

Every regex check must carry ``examples`` with at least one ``violating`` and
one ``clean`` sample, and every ``resolve_urls`` check must carry ``extracts``.
``fleet_check.py --self-test`` runs them. This exists because the most common
way an automated check fails is not a crash — it is a pattern that matches
nothing and reports a clean site forever.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STANDARDS_DIR = ROOT / "standards"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DELIMITER = "---"

SEVERITIES = ("error", "warn")
SCOPES = ("published-html", "agent-behaviour", "design-review")
CHECK_KINDS = ("forbid_regex", "require_regex", "resolve_urls", "require_paths")

REQUIRED_HEADER = ("title", "severity", "captured", "captured_from")
ALLOWED_HEADER = REQUIRED_HEADER + ("source", "applies_to", "target_tags", "checks")

DEFAULT_ALLOW_STATUS = [200, 301, 302, 400, 403, 405, 429, 999]

# new_standard.py writes this into the body. The parser refuses it, so an
# unfinished rule fails CI instead of sitting in standards/ looking enforced.
SCAFFOLD_SENTINEL = "TODO(write-the-rule)"


class StandardError(ValueError):
    """A standard file is malformed. Always names the file and the field."""


@dataclass(frozen=True)
class Check:
    slug: str
    id: str
    kind: str
    message: str
    pattern: re.Pattern | None = None
    within: re.Pattern | None = None
    paths: tuple[str, ...] = ()
    exempt_if_near: str | None = None
    allow_status: tuple[int, ...] = ()
    limit: int = 40
    skip_same_host: bool = False
    examples: dict = field(default_factory=dict)

    @property
    def ref(self) -> str:
        return f"{self.slug}/{self.id}"


@dataclass(frozen=True)
class Standard:
    slug: str
    path: Path
    title: str
    severity: str
    captured: str
    captured_from: str
    source: str | None
    applies_to: tuple[str, ...]
    target_tags: tuple[str, ...]
    body: str
    checks: tuple[Check, ...]

    @property
    def machine_checkable(self) -> bool:
        return bool(self.checks)

    @property
    def universal(self) -> bool:
        """Governs how any agent works, so it ships inside every skill.

        A rule about published HTML has no business inside a subscription-audit
        skill. Embedding every rule everywhere made the rules larger than the
        skills carrying them, which is its own way of not being read.
        """
        return "agent-behaviour" in self.applies_to

    def block(self) -> str:
        start, end = markers(self.slug)
        return f"{start}\n{self.body}\n{end}"


def markers(slug: str) -> tuple[str, str]:
    return (
        f"<!-- shared-rule:{slug}:start -->",
        f"<!-- shared-rule:{slug}:end -->",
    )


def split_front_matter(text: str, where: str) -> tuple[dict, str]:
    """Return (header, body). A file with no header is legal and yields {}."""
    if not text.startswith(DELIMITER + "\n"):
        return {}, text.strip()

    rest = text[len(DELIMITER) + 1 :]
    closing = re.search(r"^---\s*$", rest, re.MULTILINE)
    if closing is None:
        raise StandardError(f"{where}: front matter opened with --- but never closed")

    raw = rest[: closing.start()]
    body = rest[closing.end() :].strip()
    try:
        header = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StandardError(f"{where}: front matter is not valid JSON — {exc}") from exc
    if not isinstance(header, dict):
        raise StandardError(f"{where}: front matter must be a JSON object")
    return header, body


def _compile(pattern: str, where: str) -> re.Pattern:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise StandardError(f"{where}: bad regex {pattern!r} — {exc}") from exc


def _parse_check(slug: str, raw: object, index: int, where: str) -> Check:
    at = f"{where}: checks[{index}]"
    if not isinstance(raw, dict):
        raise StandardError(f"{at} must be an object")

    unknown = set(raw) - {
        "id",
        "kind",
        "message",
        "pattern",
        "exempt_if_near",
        "extract",
        "within",
        "paths",
        "allow_status",
        "limit",
        "skip_same_host",
        "examples",
    }
    if unknown:
        raise StandardError(f"{at}: unknown key(s) {sorted(unknown)}")

    check_id = raw.get("id")
    if not isinstance(check_id, str) or not SLUG_RE.match(check_id):
        raise StandardError(f"{at}: 'id' must be kebab-case, got {check_id!r}")

    kind = raw.get("kind")
    if kind not in CHECK_KINDS:
        raise StandardError(f"{at}: 'kind' must be one of {CHECK_KINDS}, got {kind!r}")

    message = raw.get("message")
    if not isinstance(message, str) or not message.strip():
        raise StandardError(f"{at}: 'message' is required and must say what is wrong")

    examples = raw.get("examples", {})
    if not isinstance(examples, dict):
        raise StandardError(f"{at}: 'examples' must be an object")

    if kind in ("forbid_regex", "require_regex"):
        pattern = raw.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            raise StandardError(f"{at}: '{kind}' requires 'pattern'")
        compiled = _compile(pattern, at)

        for key in ("violating", "clean"):
            samples = examples.get(key)
            if not isinstance(samples, list) or not samples:
                raise StandardError(
                    f"{at}: needs examples.{key} — at least one sample. A check "
                    f"with no examples can match nothing and pass forever."
                )
            if not all(isinstance(s, str) and s for s in samples):
                raise StandardError(f"{at}: examples.{key} must be non-empty strings")

        exempt = raw.get("exempt_if_near")
        if exempt is not None and (not isinstance(exempt, str) or not exempt):
            raise StandardError(f"{at}: 'exempt_if_near' must be a string")

        return Check(
            slug=slug,
            id=check_id,
            kind=kind,
            message=message,
            pattern=compiled,
            exempt_if_near=exempt,
            examples=examples,
        )

    if kind == "require_paths":
        paths = raw.get("paths")
        if not isinstance(paths, list) or not paths:
            raise StandardError(f"{at}: 'require_paths' needs a non-empty 'paths' list")
        for path in paths:
            if not isinstance(path, str) or not path.startswith("/"):
                raise StandardError(
                    f"{at}: every path must be a string starting with '/', got {path!r}"
                )
        allow = raw.get("allow_status", [200, 301, 302])
        if not isinstance(allow, list) or not all(isinstance(i, int) for i in allow):
            raise StandardError(f"{at}: 'allow_status' must be a list of integers")

        builds = examples.get("builds")
        if not isinstance(builds, list) or not builds:
            raise StandardError(
                f"{at}: needs examples.builds — [{{'target': ..., 'urls': [...]}}] — so "
                f"the origin joining is proven offline"
            )
        for sample in builds:
            if (
                not isinstance(sample, dict)
                or not isinstance(sample.get("target"), str)
                or not isinstance(sample.get("urls"), list)
            ):
                raise StandardError(f"{at}: each examples.builds item needs target + urls")

        return Check(
            slug=slug,
            id=check_id,
            kind=kind,
            message=message,
            paths=tuple(paths),
            allow_status=tuple(allow),
            examples=examples,
        )

    extract = raw.get("extract")
    if not isinstance(extract, str) or not extract:
        raise StandardError(f"{at}: 'resolve_urls' requires 'extract'")
    compiled = _compile(extract, at)
    if compiled.groups != 1:
        raise StandardError(
            f"{at}: 'extract' must have exactly one capturing group (the URL), "
            f"found {compiled.groups}"
        )

    within_raw = raw.get("within")
    within = None
    if within_raw is not None:
        if not isinstance(within_raw, str) or not within_raw:
            raise StandardError(f"{at}: 'within' must be a non-empty regex string")
        within = _compile(within_raw, at)

    allow = raw.get("allow_status", DEFAULT_ALLOW_STATUS)
    if not isinstance(allow, list) or not all(isinstance(i, int) for i in allow):
        raise StandardError(f"{at}: 'allow_status' must be a list of integers")

    limit = raw.get("limit", 40)
    if not isinstance(limit, int) or limit < 1:
        raise StandardError(f"{at}: 'limit' must be a positive integer")

    skip_same_host = raw.get("skip_same_host", False)
    if not isinstance(skip_same_host, bool):
        raise StandardError(f"{at}: 'skip_same_host' must be true or false")

    extracts = examples.get("extracts")
    if not isinstance(extracts, list) or not extracts:
        raise StandardError(
            f"{at}: needs examples.extracts — [{{'html': ..., 'urls': [...]}}] — so "
            f"the extractor is proven offline"
        )
    for sample in extracts:
        if (
            not isinstance(sample, dict)
            or not isinstance(sample.get("html"), str)
            or not isinstance(sample.get("urls"), list)
        ):
            raise StandardError(f"{at}: each examples.extracts item needs html + urls")

    return Check(
        slug=slug,
        id=check_id,
        kind=kind,
        message=message,
        pattern=compiled,
        within=within,
        allow_status=tuple(allow),
        limit=limit,
        skip_same_host=skip_same_host,
        examples=examples,
    )


def parse_standard(path: Path) -> Standard:
    slug = path.stem
    where = f"standards/{path.name}"
    if not SLUG_RE.match(slug):
        raise StandardError(
            f"{where}: filename stem must be kebab-case ([a-z0-9-]), got {slug!r}"
        )

    header, body = split_front_matter(path.read_text(encoding="utf-8"), where)
    if not body:
        raise StandardError(f"{where} has no rule body")
    if SCAFFOLD_SENTINEL in body:
        raise StandardError(
            f"{where} is still a scaffold — the rule was never written. Finish it or "
            f"delete it; a half-captured rule in standards/ looks enforced and is not."
        )

    unknown = set(header) - set(ALLOWED_HEADER)
    if unknown:
        raise StandardError(f"{where}: unknown header field(s) {sorted(unknown)}")

    if header:
        missing = [k for k in REQUIRED_HEADER if k not in header]
        if missing:
            raise StandardError(f"{where}: header missing {missing}")

    title = header.get("title") or body.splitlines()[0].lstrip("# ").strip()
    severity = header.get("severity", "error")
    if severity not in SEVERITIES:
        raise StandardError(f"{where}: severity must be one of {SEVERITIES}")

    captured = header.get("captured", "")
    if captured and not DATE_RE.match(captured):
        raise StandardError(f"{where}: 'captured' must be YYYY-MM-DD, got {captured!r}")

    captured_from = header.get("captured_from", "")
    if header and not captured_from.strip():
        raise StandardError(
            f"{where}: 'captured_from' is required — a rule with no traceable origin "
            f"cannot be re-checked against its source"
        )

    applies_to = header.get("applies_to", ["agent-behaviour"])
    if not isinstance(applies_to, list) or not applies_to:
        raise StandardError(f"{where}: 'applies_to' must be a non-empty list")
    bad_scope = [s for s in applies_to if s not in SCOPES]
    if bad_scope:
        raise StandardError(f"{where}: unknown applies_to {bad_scope}, allowed {SCOPES}")

    target_tags = header.get("target_tags", [])
    if not isinstance(target_tags, list) or not all(
        isinstance(tag, str) and SLUG_RE.match(tag) for tag in target_tags
    ):
        raise StandardError(f"{where}: 'target_tags' must be a list of kebab-case tags")

    raw_checks = header.get("checks", [])
    if not isinstance(raw_checks, list):
        raise StandardError(f"{where}: 'checks' must be a list")
    checks = tuple(
        _parse_check(slug, raw, i, where) for i, raw in enumerate(raw_checks)
    )

    seen: set[str] = set()
    for check in checks:
        if check.id in seen:
            raise StandardError(f"{where}: duplicate check id {check.id!r}")
        seen.add(check.id)

    if checks and "published-html" not in applies_to:
        raise StandardError(
            f"{where}: has checks over published HTML but applies_to does not "
            f"include 'published-html'"
        )

    return Standard(
        slug=slug,
        path=path,
        title=title,
        severity=severity,
        captured=captured,
        captured_from=captured_from,
        source=header.get("source"),
        applies_to=tuple(applies_to),
        target_tags=tuple(target_tags),
        body=body,
        checks=checks,
    )


SCOPE_KEY = "rule-scopes"


def skill_scopes(skill_file: Path) -> set[str]:
    """Extra rule scopes a SKILL.md opts into, from its YAML frontmatter.

        rule-scopes: published-html, design-review

    Absent means the skill only carries the universal agent rules.
    """
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return set()
    end = text.find("\n---", 4)
    if end == -1:
        return set()
    for line in text[4:end].splitlines():
        if not line.startswith(SCOPE_KEY + ":"):
            continue
        raw = line.split(":", 1)[1]
        found = {s.strip() for s in raw.replace(",", " ").split() if s.strip()}
        unknown = found - set(SCOPES)
        if unknown:
            raise StandardError(
                f"{skill_file}: unknown {SCOPE_KEY} {sorted(unknown)}, "
                f"allowed {SCOPES}"
            )
        return found
    return set()


def standards_for(standards: list[Standard], scopes: set[str]) -> list[Standard]:
    """Rules a target carrying these scopes must embed in full."""
    return [s for s in standards if s.universal or (set(s.applies_to) & scopes)]


def load_standards(directory: Path | None = None) -> list[Standard]:
    """Every standard, sorted by slug, so all generated output is deterministic."""
    directory = directory or STANDARDS_DIR
    if not directory.is_dir():
        return []
    return [parse_standard(p) for p in sorted(directory.glob("*.md"))]


def all_checks(directory: Path | None = None) -> list[Check]:
    return [c for s in load_standards(directory) for c in s.checks]
