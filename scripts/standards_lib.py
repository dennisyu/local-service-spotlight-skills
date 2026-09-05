#!/usr/bin/env python3
"""Read, validate, and compile the house rules in ``standards/``.

One rule lives in exactly one file. That file is the only place the rule is
written down, and three different things are generated from it:

1. **Content**  — the prose body is embedded verbatim in ``AGENTS.md`` and in
   every applicable distributed ``SKILL.md`` (``sync_shared_rules.py``), so the
   rule travels inside each self-contained skill whose work it governs.
2. **Checklist** — the same prose is what a human reads pre-flight.
3. **Software configuration** — the ``checks`` block configures the live fleet
   sweep (``fleet_check.py``), so a violation on a published page is caught
   without anyone remembering to look. Simple regex checks are fully declared
   there; structural check kinds dispatch to separately reviewed shared code.

That is Content · Checklist · Software with one source for prose, configuration,
and examples. Shared implementations can still drift from those declarations.
Self-tests prove that tracked hostile/clean examples bite and reduce that risk;
independent review and new adversarial fixtures remain necessary.

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
``resolve_urls``   every URL found by a declared structural ``extractor`` or
                   regex ``extract`` must return an allowed status. Structural
                   extractors are used for HTML anchors and JSON-LD ``sameAs``;
                   regex extraction remains available for non-HTML formats.
``require_paths``  every listed path must resolve on the target's own origin.
                   The only check that tests a URL the page does not link to —
                   which is exactly what a URL printed on a QR code is.
``provenance_contract`` parses the document structure and requires exactly one
                   structurally renderable provenance rail. Unlike a regex, it
                   ignores comments/inert containers, validates real ISO
                   datetimes, keeps required fields on one element, and checks a
                   documented static-CSS subset. Browser-computed visibility is
                   still required by the external publication receipt.

Every regex check must carry ``examples`` with at least one ``violating`` and
one ``clean`` sample, and every ``resolve_urls`` check must carry ``extracts``.
``fleet_check.py --self-test`` runs them. This exists because the most common
way an automated check fails is not a crash — it is a pattern that matches
nothing and reports a clean site forever.
"""

from __future__ import annotations

import json
import re
import datetime as dt
import ipaddress
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

try:
    from .public_value_safety import public_value_problem
except ImportError:  # pragma: no cover - direct script imports
    from public_value_safety import public_value_problem  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
STANDARDS_DIR = ROOT / "standards"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DELIMITER = "---"

SEVERITIES = ("error", "warn")
SCOPES = ("published-html", "agent-behaviour", "design-review")
CHECK_KINDS = (
    "forbid_regex",
    "require_regex",
    "resolve_urls",
    "require_paths",
    "provenance_contract",
)

REQUIRED_HEADER = ("title", "severity", "captured", "captured_from")
ALLOWED_HEADER = REQUIRED_HEADER + ("source", "applies_to", "target_tags", "checks")

DEFAULT_ALLOW_STATUS = [200]

# new_standard.py writes this into the body. The parser refuses it, so an
# unfinished rule fails CI instead of sitting in standards/ looking enforced.
SCAFFOLD_SENTINEL = "TODO(write-the-rule)"


class StandardError(ValueError):
    """A standard file is malformed. Always names the file and the field."""


class DuplicateJsonMember(ValueError):
    """A JSON object repeats a member name and is therefore ambiguous."""


def _public_hostname_problem(hostname: str) -> str | None:
    normalized = hostname.rstrip(".").casefold()
    if not normalized or "%" in normalized or "\\" in normalized:
        return "malformed hostname"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        if (
            normalized == "localhost"
            or "." not in normalized
            or normalized.endswith(
                (".localhost", ".local", ".internal", ".intranet", ".lan", ".home", ".corp")
            )
            or re.fullmatch(r"[0-9.]+", normalized)
        ):
            return "private/local hostname"
        try:
            normalized.encode("idna")
        except UnicodeError:
            return "invalid IDNA hostname"
    else:
        if not address.is_global:
            return "private, loopback, link-local, or reserved IP address"
    return None


def _reject_duplicate_json_members(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, child in pairs:
        if key in value:
            raise DuplicateJsonMember(f"duplicate JSON member {key!r}")
        value[key] = child
    return value


def strict_json_loads(text: str) -> object:
    """Parse actual JSON, rejecting duplicate members and JS numeric constants."""

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-JSON numeric constant {value!r}")

    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_json_members,
        parse_constant=reject_constant,
    )


@dataclass(frozen=True)
class Check:
    slug: str
    id: str
    kind: str
    message: str
    pattern: re.Pattern | None = None
    within: re.Pattern | None = None
    extractor: str | None = None
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
    """Return the required JSON header and Markdown body."""
    if text.startswith("\ufeff"):
        raise StandardError(f"{where}: UTF-8 BOM is not allowed")
    if "\r" in text:
        raise StandardError(f"{where}: standards must use canonical LF line endings")
    if not text.startswith(DELIMITER + "\n"):
        raise StandardError(f"{where}: missing required JSON front matter")

    rest = text[len(DELIMITER) + 1 :]
    closing = re.search(r"^---\s*$", rest, re.MULTILINE)
    if closing is None:
        raise StandardError(f"{where}: front matter opened with --- but never closed")

    raw = rest[: closing.start()]
    body = rest[closing.end() :].strip()
    try:
        header = strict_json_loads(raw)
    except (json.JSONDecodeError, DuplicateJsonMember, ValueError) as exc:
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
        "extractor",
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

    if kind == "provenance_contract":
        for key in ("violating", "clean"):
            samples = examples.get(key)
            if not isinstance(samples, list) or not samples:
                raise StandardError(
                    f"{at}: needs examples.{key} — at least one HTML sample. "
                    "A structural check without adversarial examples can pass "
                    "forever while validating the wrong tree."
                )
            if not all(isinstance(sample, str) and sample for sample in samples):
                raise StandardError(f"{at}: examples.{key} must be non-empty strings")

        irrelevant = set(raw) & {
            "pattern",
            "exempt_if_near",
            "extract",
            "extractor",
            "within",
            "paths",
            "allow_status",
            "limit",
            "skip_same_host",
        }
        if irrelevant:
            raise StandardError(
                f"{at}: 'provenance_contract' has no regex or URL options; "
                f"remove {sorted(irrelevant)}"
            )
        return Check(
            slug=slug,
            id=check_id,
            kind=kind,
            message=message,
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
        if (
            not isinstance(allow, list)
            or not allow
            or any(type(item) is not int or not 100 <= item <= 599 for item in allow)
            or len(allow) != len(set(allow))
        ):
            raise StandardError(
                f"{at}: 'allow_status' must be unique exact HTTP-status integers"
            )

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

    extractor = raw.get("extractor")
    if extractor is not None and extractor not in {"html-anchors", "jsonld-sameas"}:
        raise StandardError(
            f"{at}: 'extractor' must be 'html-anchors' or 'jsonld-sameas'"
        )
    extract = raw.get("extract")
    if extractor is not None and extract is not None:
        raise StandardError(f"{at}: use either 'extractor' or 'extract', not both")
    if extractor is None and (not isinstance(extract, str) or not extract):
        raise StandardError(
            f"{at}: 'resolve_urls' requires a structural 'extractor' or regex 'extract'"
        )
    compiled = _compile(extract, at) if isinstance(extract, str) else None
    if compiled is not None and compiled.groups != 1:
        raise StandardError(
            f"{at}: 'extract' must have exactly one capturing group (the URL), "
            f"found {compiled.groups}"
        )

    within_raw = raw.get("within")
    within = None
    if within_raw is not None:
        if extractor is not None:
            raise StandardError(
                f"{at}: structural 'extractor' cannot be combined with 'within'"
            )
        if not isinstance(within_raw, str) or not within_raw:
            raise StandardError(f"{at}: 'within' must be a non-empty regex string")
        within = _compile(within_raw, at)

    allow = raw.get("allow_status", DEFAULT_ALLOW_STATUS)
    if (
        not isinstance(allow, list)
        or not allow
        or any(type(item) is not int or not 100 <= item <= 599 for item in allow)
        or len(allow) != len(set(allow))
    ):
        raise StandardError(
            f"{at}: 'allow_status' must be unique exact HTTP-status integers"
        )

    limit = raw.get("limit", 40)
    if type(limit) is not int or limit < 1:
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
        extractor=extractor,
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

    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise StandardError(f"{where}: cannot read standard — {exc}") from exc
    if len(raw_bytes) > 2_000_000:
        raise StandardError(f"{where}: standard exceeds the 2 MB safety limit")
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StandardError(f"{where}: standard must be valid UTF-8") from exc
    header, body = split_front_matter(text, where)
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

    missing = [k for k in REQUIRED_HEADER if k not in header]
    if missing:
        raise StandardError(f"{where}: header missing {missing}")

    title = header.get("title")
    if (
        not isinstance(title, str)
        or not title.strip()
        or title != title.strip()
        or "\n" in title
        or "\r" in title
    ):
        raise StandardError(f"{where}: 'title' must be one non-blank trimmed line")
    headings = [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]
    if len(headings) != 1 or not body.startswith("## ") or headings[0] != title:
        raise StandardError(
            f"{where}: body must start with exactly one '## {title}' heading"
        )

    severity = header.get("severity")
    if not isinstance(severity, str):
        raise StandardError(f"{where}: 'severity' must be a string")
    if severity not in SEVERITIES:
        raise StandardError(f"{where}: severity must be one of {SEVERITIES}")

    captured = header.get("captured")
    if not isinstance(captured, str) or not DATE_RE.fullmatch(captured):
        raise StandardError(f"{where}: 'captured' must be YYYY-MM-DD, got {captured!r}")
    try:
        captured_date = dt.date.fromisoformat(captured)
    except ValueError as exc:
        raise StandardError(
            f"{where}: 'captured' must be a real calendar date, got {captured!r}"
        ) from exc
    if captured_date > dt.date.today():
        raise StandardError(f"{where}: 'captured' cannot be in the future")

    captured_from = header.get("captured_from")
    if (
        not isinstance(captured_from, str)
        or not captured_from.strip()
        or captured_from != captured_from.strip()
        or "\n" in captured_from
        or "\r" in captured_from
    ):
        raise StandardError(
            f"{where}: 'captured_from' is required — a rule with no traceable origin "
            f"cannot be re-checked against its source"
        )
    captured_from_problem = public_value_problem(captured_from)
    if captured_from_problem:
        raise StandardError(
            f"{where}: 'captured_from' {captured_from_problem}"
        )
    captured_from_comparison = " ".join(
        unicodedata.normalize("NFKC", captured_from).casefold().split()
    )
    tracked_standard = path.parent.resolve() == STANDARDS_DIR.resolve()
    if tracked_standard and captured_from_comparison in {
        "unknown", "someone", "not disclosed", "tbd", "example", "test fixture",
    }:
        raise StandardError(
            f"{where}: 'captured_from' must name a traceable source, not a placeholder"
        )

    source = header.get("source")
    if source is not None:
        if not isinstance(source, str) or not source or source != source.strip():
            raise StandardError(f"{where}: optional 'source' must be a trimmed HTTPS URL")
        try:
            parsed_source = urlparse(source)
            source_port = parsed_source.port
        except ValueError as exc:
            raise StandardError(f"{where}: optional 'source' is malformed") from exc
        if (
            parsed_source.scheme != "https"
            or not parsed_source.hostname
            or parsed_source.username is not None
            or parsed_source.password is not None
            or source_port is not None
            or parsed_source.query
            or parsed_source.fragment
            or "\\" in source
            or any(character.isspace() or ord(character) < 32 for character in source)
            or _public_hostname_problem(parsed_source.hostname) is not None
            or public_value_problem(source) is not None
            or (
                parsed_source.hostname.casefold() == "hooks.slack.com"
                and parsed_source.path.casefold().startswith("/services/")
            )
            or (
                parsed_source.hostname.casefold() in {"discord.com", "discordapp.com"}
                and "/api/webhooks/" in parsed_source.path.casefold()
            )
            or (
                parsed_source.hostname.casefold() == "api.telegram.org"
                and parsed_source.path.casefold().startswith("/bot")
            )
        ):
            raise StandardError(f"{where}: optional 'source' must be a public HTTPS URL")

    applies_to = header.get("applies_to", ["agent-behaviour"])
    if not isinstance(applies_to, list) or not applies_to:
        raise StandardError(f"{where}: 'applies_to' must be a non-empty list")
    if not all(isinstance(scope, str) for scope in applies_to):
        raise StandardError(f"{where}: every applies_to member must be a string")
    if len(applies_to) != len(set(applies_to)):
        raise StandardError(f"{where}: 'applies_to' must not repeat a scope")
    bad_scope = [scope for scope in applies_to if scope not in SCOPES]
    if bad_scope:
        raise StandardError(f"{where}: unknown applies_to {bad_scope}, allowed {SCOPES}")

    target_tags = header.get("target_tags", [])
    if not isinstance(target_tags, list) or not all(
        isinstance(tag, str) and SLUG_RE.match(tag) for tag in target_tags
    ):
        raise StandardError(f"{where}: 'target_tags' must be a list of kebab-case tags")
    if len(target_tags) != len(set(target_tags)):
        raise StandardError(f"{where}: 'target_tags' must not repeat a tag")

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
        source=source,
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
    raw_bytes = skill_file.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raise StandardError(f"{skill_file}: UTF-8 BOM is not allowed in frontmatter")
    if b"\r" in raw_bytes:
        raise StandardError(
            f"{skill_file}: frontmatter must use canonical LF line endings"
        )
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StandardError(f"{skill_file}: frontmatter must be valid UTF-8") from exc
    if not text.startswith("---\n"):
        raise StandardError(
            f"{skill_file}: missing canonical opening frontmatter delimiter"
        )
    end = text.find("\n---\n", 4)
    if end == -1:
        raise StandardError(
            f"{skill_file}: missing canonical closing frontmatter delimiter"
        )
    declarations: list[str] = []
    for line in text[4:end].splitlines():
        if ":" in line:
            raw_key = line.split(":", 1)[0].strip()
            comparable_key = re.sub(
                r"[^a-z]",
                "",
                "".join(
                    character
                    for character in unicodedata.normalize("NFKC", raw_key).casefold()
                    if unicodedata.category(character) not in {"Cf", "Mn", "Me"}
                ),
            )
            if comparable_key in {"rulescope", "rulescopes", "rulesscopes"} and raw_key != SCOPE_KEY:
                raise StandardError(
                    f"{skill_file}: confusable scope key {raw_key!r}; "
                    f"use exact column-0 {SCOPE_KEY!r}"
                )
        if re.match(rf"^\s*{re.escape(SCOPE_KEY)}\s*:", line):
            if not line.startswith(SCOPE_KEY + ":"):
                raise StandardError(
                    f"{skill_file}: {SCOPE_KEY} must be a column-0 key with no "
                    "space before ':'"
                )
            declarations.append(line.split(":", 1)[1])
    if len(declarations) > 1:
        raise StandardError(f"{skill_file}: duplicate {SCOPE_KEY} declarations")
    if not declarations:
        raise StandardError(
            f"{skill_file}: missing explicit {SCOPE_KEY} classification; use "
            "'agent-behaviour' when no additional publication/design scope applies"
        )
    raw = declarations[0]
    found = {s.strip() for s in raw.replace(",", " ").split() if s.strip()}
    if not found:
        raise StandardError(f"{skill_file}: {SCOPE_KEY} must not be blank")
    unknown = found - set(SCOPES)
    if unknown:
        raise StandardError(
            f"{skill_file}: unknown {SCOPE_KEY} {sorted(unknown)}, allowed {SCOPES}"
        )
    return found


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
