#!/usr/bin/env python3
"""Sweep live pages against every machine-checkable rule in ``standards/``.

The sweep is *generated from the rules*, never written beside them. Add a
``checks`` block to a standard and the next sweep enforces it; nothing else has
to be edited, and there is no second copy of the rule to drift out of sync.

    # prove every rule's own patterns actually work — no network
    python3 scripts/fleet_check.py --self-test

    # check the manifest parses and every regex compiles — no network
    python3 scripts/fleet_check.py --lint

    # sweep live pages
    python3 scripts/fleet_check.py https://georgepaladichuk.com/ --tag personal-brand
    python3 scripts/fleet_check.py --targets fleet.txt --json report.json

A targets file is one URL per line, with optional comma-separated tags after
whitespace. Tags decide which rules apply, so a personal-brand rule does not fire
on a product site:

    https://georgepaladichuk.com/     personal-brand,client
    https://blitzmetrics.com/         company

Exit codes
----------
0  no ``error``-severity findings (warnings may be present)
1  at least one ``error``-severity finding
2  the sweep could not run — a page failed to load, or a standard is malformed

The distinction matters. A sweep that cannot fetch a page has not found the page
clean; it has found nothing. Exit 2 says so instead of reporting a pass.
"""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import re
import secrets
import socket
import stat
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:  # package import in tests; direct import when run as scripts/fleet_check.py
    from .agent_fleet_contract import (
        ALL_PUBLIC_MODEL_IDS,
        PUBLIC_ACTOR_IDS,
        PUBLIC_DOCUMENTATION_ACTOR_IDS,
        PUBLIC_HUMAN_REVIEWERS,
        PUBLIC_MODEL_IDS,
    )
except ImportError:  # pragma: no cover - exercised by CLI integration tests
    from agent_fleet_contract import (  # type: ignore
        ALL_PUBLIC_MODEL_IDS,
        PUBLIC_ACTOR_IDS,
        PUBLIC_DOCUMENTATION_ACTOR_IDS,
        PUBLIC_HUMAN_REVIEWERS,
        PUBLIC_MODEL_IDS,
    )
try:
    from .public_value_safety import (
        has_placeholder_slug_token as _has_placeholder_slug_token,
        public_value_problem as _shared_public_value_problem,
    )
except ImportError:  # pragma: no cover - direct CLI import
    from public_value_safety import (  # type: ignore
        has_placeholder_slug_token as _has_placeholder_slug_token,
        public_value_problem as _shared_public_value_problem,
    )
from standards_lib import (  # noqa: E402
    Check,
    Standard,
    StandardError,
    load_standards,
)


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 LSSFleetCheck/1.0"
)
EXEMPT_WINDOW = 160
SNIPPET = 140
PAGE_TIMEOUT = 30
LINK_TIMEOUT = 20
LINK_PAUSE = 0.4
MAX_LINK_REDIRECTS = 5
LINK_STATUS_BODY_BYTES = 1
MAX_PAGE_BODY_BYTES = 5 * 1024 * 1024
MAX_RESOLVE_AUDIT_SECONDS = 120
MAX_PUBLIC_DECODE_ROUNDS = 16
EVIDENCE_CLOCK_FUTURE_TOLERANCE = timedelta(minutes=5)
FLEET_LIVE_MAX_CHECK_AGE = timedelta(hours=36)
GENERIC_PUBLIC_MAX_CHECK_AGE = timedelta(days=30)

PROVENANCE_REQUIRED_ATTRIBUTES = (
    "data-document-provenance",
    "data-verification-scope",
    "data-human-author",
    "data-maintainer",
    "data-maintainer-agent",
    "data-maintainer-model",
    "data-human-reviewer",
    "data-capture-run-id",
    "data-scheduler-capture-result",
    "data-publication-verification-result",
    "data-publication-receipt-id",
    "data-publication-receipt-index",
    "data-publication-receipt-discovery-url",
    "data-last-checked",
    "data-last-changed",
    "data-source-url",
    "data-source-revision",
)
PROVENANCE_OPTIONAL_PUBLIC_DATA_ATTRIBUTES = {
    "data-source-contract-url",
}
PROVENANCE_ALLOWED_DATA_ATTRIBUTES = (
    set(PROVENANCE_REQUIRED_ATTRIBUTES) | PROVENANCE_OPTIONAL_PUBLIC_DATA_ATTRIBUTES
)
OUTSIDE_PROVENANCE_DATA_ATTRIBUTES = set(PROVENANCE_REQUIRED_ATTRIBUTES) | {
    "data-document-verification",
    "data-last-updated",
    "data-review-status",
    "data-verification-result",
    "data-verified",
}
PROVENANCE_SCOPES = {
    "external-exact-live-bytes",
    "external-exact-raw-wp-body-and-inclusive-marker-slice",
}
PROVENANCE_STATES = {"pending-external-verification", "receipt-linked"}
PUBLICATION_VERIFICATION_RESULTS = {"pending", "success", "failure"}
PRIVATE_PROVENANCE_ATTRIBUTE_FRAGMENTS = {
    "automationid",
    "apikey",
    "cadence",
    "client",
    "clientdata",
    "cron",
    "credential",
    "customer",
    "email",
    "fireat",
    "jobid",
    "lastrun",
    "ledgercommit",
    "ledgerpath",
    "machinepath",
    "nextrun",
    "password",
    "private",
    "privateartifact",
    "privatejob",
    "privateprompt",
    "prompt",
    "registry",
    "registrypath",
    "schedulerid",
    "secret",
    "sourcerecord",
    "taskid",
    "timezone",
    "token",
}
FLEET_MARKER_START = "<!-- BM-FLEET-PAGE:START -->"
FLEET_MARKER_END = "<!-- BM-FLEET-PAGE:END -->"
FLEET_RECEIPT_INDEX = (
    "https://github.com/dennisyu/local-service-spotlight-skills/tree/main/"
    "receipts/agent-fleet"
)
FLEET_RECEIPT_DISCOVERY_PREFIX = (
    "https://github.com/dennisyu/local-service-spotlight-skills/blob/main/"
    "receipts/agent-fleet/"
)
FLEET_SOURCE_MANIFEST_PREFIX = (
    "https://github.com/dennisyu/local-service-spotlight-skills/blob/main/"
    "receipts/agent-fleet/sources/"
)
FLEET_RECEIPT_CONTRACT = (
    "https://github.com/dennisyu/local-service-spotlight-skills/blob/main/"
    "receipts/agent-fleet/README.md"
)
ISO_INSTANT = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
PLACEHOLDER_IDENTITY = re.compile(
    r"\b(?:unknown|nobody|none|null|unset|unassigned|someone|anonymous|anonymized|"
    r"redacted|system|invalid|unverified|fabricated|synthetic|placeholder|example|"
    r"sample|pending|awaiting|unavailable|"
    r"undisclosed|withheld|tbd|todo|n/?a|review required|not (?:known|provided|"
    r"recorded|exposed|disclosed|assigned))\b",
    re.IGNORECASE,
)
GENERIC_IDENTITIES = {
    "agent",
    "ai",
    "ai agent",
    "approved",
    "assistant",
    "author",
    "bot",
    "human",
    "human author",
    "human reviewer",
    "model",
    "person",
    "review complete",
    "reviewed",
    "reviewer",
    "staff",
    "team",
    "verifier",
    "writer",
}
GENERIC_ROLE_TOKENS = {
    "a", "admin", "administrator", "an", "and", "approved", "approver",
    "assurance", "audit", "auditor", "author", "automation", "board", "bot",
    "by", "committee", "compliance", "content", "control", "department",
    "designated", "desk", "documentation", "duty", "editorial", "employee",
    "dr", "external", "function", "group", "human", "independent", "lead",
    "manager", "member", "miss", "mr", "mrs", "ms", "mx", "named", "of",
    "officer", "on", "operation",
    "operations", "operator", "owner", "party", "personnel", "qa", "quality",
    "review", "reviewed", "reviewer", "security", "specialist", "staff", "team",
    "prof", "professor", "some", "the", "third", "verification", "verifier",
}
GENERIC_AGENT_TOKENS = {
    "agent", "agentic", "ai", "anthropic", "assistant", "automation", "bot",
    "chatbot", "chatgpt", "claude", "codex", "current", "deepseek", "default",
    "documentation", "gemini", "gpt", "language", "latest", "llama", "llm",
    "model", "openai", "production", "qwen", "runtime", "software", "system",
    "virtual",
}
GENERIC_MODELS = {
    "ai",
    "assistant",
    "bot",
    "default model",
    "language model",
    "llm",
    "model",
    "runtime model",
    "some model",
    "ai model",
    "llm model",
    "production model",
    "current model",
    "latest model",
    "runtime",
    "default",
    "unspecified model",
    "vendor model",
    "chatbot",
}
GENERIC_MODEL_TOKENS = {
    "agent", "ai", "anthropic", "assistant", "bot", "chatbot", "codex",
    "current", "deepseek", "default", "gemini", "gpt", "chatgpt", "language",
    "latest", "llama", "llm", "model", "openai", "production", "qwen",
    "runtime", "some", "unspecified", "vendor", "claude",
}
AMBIGUOUS_HUMAN_NAME_TOKENS = {"claude", "gemini", "qwen"}
KNOWN_AGENT_IDENTITY_TOKENS = {
    "agent",
    "ai",
    "algorithm",
    "anthropic",
    "assistant",
    "automated",
    "automation",
    "bot",
    "chatgpt",
    "claude",
    "codex",
    "copilot",
    "cursor",
    "deepseek",
    "gemini",
    "gpt",
    "grok",
    "llama",
    "llm",
    "machine",
    "mistral",
    "model",
    "openai",
    "perplexity",
    "qwen",
    "robot",
    "software",
    "system",
    "virtual",
}
PUBLIC_AGENT_IDENTITY = re.compile(
    r"^(?:agent|job):[a-z0-9][a-z0-9._-]{2,119}$"
)
PENDING_REVIEW = re.compile(
    r"(?:\bunreviewed\b|\b(?:not|no|without|pending|awaiting|missing|unknown|none)\b"
    r"[^.]{0,60}\breview(?:ed)?\b|\breview(?:ed)?\b[^.]{0,60}"
    r"\b(?:pending|awaiting|missing|unknown|none)\b)",
    re.IGNORECASE,
)
HONEST_PENDING_REVIEW = re.compile(
    r"^(?:not yet reviewed|not reviewed|pending review|review pending|unreviewed|"
    r"no human review recorded|review required)$",
    re.IGNORECASE,
)
STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]+$")
INERT_CONTAINERS = {
    "canvas",
    "datalist",
    "head",
    "iframe",
    "noembed",
    "noscript",
    "plaintext",
    "script",
    "select",
    "style",
    "template",
    "textarea",
    "title",
    "xmp",
}
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
PUBLIC_TEXT_BOUNDARY_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",
    "dt", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p",
    "pre", "section", "table", "tbody", "td", "tfoot", "th", "thead",
    "tr", "ul",
}
NON_RENDERABLE_RAIL_ANCESTORS = {
    "audio", "frameset", "math", "meter", "noframes", "object", "progress",
    "svg", "video",
}


@dataclass
class Finding:
    url: str
    standard: str
    check: str
    severity: str
    message: str
    detail: str

    @property
    def blocking(self) -> bool:
        return self.severity == "error"


@dataclass
class _VisibleText:
    text: str
    visibility_path: tuple[tuple[str, dict[str, str]], ...]
    dom_path: tuple[tuple[int, int], ...]
    sibling_index: int


@dataclass
class _SemanticTime:
    datetime: str | None
    duplicate_attributes: tuple[str, ...]
    text: list[_VisibleText]
    visibility_path: tuple[tuple[str, dict[str, str]], ...]
    leading_text: tuple[_VisibleText, ...]
    node_id: int
    parent_node_id: int
    sibling_index: int


@dataclass
class _VisibleLink:
    href: str | None
    text: list[_VisibleText]
    visibility_path: tuple[tuple[str, dict[str, str]], ...]
    leading_text: tuple[_VisibleText, ...]


@dataclass
class _ProvenanceRail:
    tag: str
    attributes: dict[str, str]
    duplicate_attributes: tuple[str, ...]
    times: list[_SemanticTime]
    links: list[_VisibleLink]
    visible_text: list[_VisibleText]
    visibility_path: tuple[tuple[str, dict[str, str]], ...]
    inside_fleet_markers: bool
    closed: bool = False
    subtree_duplicate_attributes: list[str] = field(default_factory=list)
    subtree_attributes: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    subtree_visibility_paths: list[
        tuple[tuple[str, dict[str, str]], ...]
    ] = field(default_factory=list)
    public_raw_text: list[str] = field(default_factory=list)


@dataclass
class _HtmlFrame:
    tag: str
    ignored: bool
    element_hidden: bool
    children_hidden: bool
    rail: _ProvenanceRail | None
    active_time: _SemanticTime | None
    active_link: _VisibleLink | None
    attributes: dict[str, str]
    closed_details: bool = False
    summary_seen: bool = False
    owns_rail: bool = False
    node_id: int = 0
    sibling_index: int = 0
    next_child_index: int = 0


def _attribute_map(
    attributes: list[tuple[str, str | None]],
) -> tuple[dict[str, str], tuple[str, ...]]:
    values: dict[str, str] = {}
    duplicates: set[str] = set()
    for raw_name, raw_value in attributes:
        name = raw_name.lower()
        if name in values:
            duplicates.add(name)
            continue
        values[name] = "" if raw_value is None else raw_value
    return values, tuple(sorted(duplicates))


def _audit_attribute_name_key(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.category(character).startswith("C")
    )
    return "".join(character for character in normalized if character.isalnum())


def _looks_like_outside_audit_attribute(name: str) -> bool:
    key = _audit_attribute_name_key(name)
    if not key.startswith("data"):
        return False
    if key in {
        _audit_attribute_name_key(attribute)
        for attribute in PROVENANCE_ALLOWED_DATA_ATTRIBUTES
    }:
        return True
    field = key[4:]
    return any(
        fragment in field
        for fragment in (
            "auditstatus", "documentprovenance", "documentverification",
            "humanauthor", "humanreviewer", "lastchanged", "lastchecked",
            "lastupdated", "provenance", "reviewstatus", "verified",
            "verificationresult", "verifiedstate",
        )
    )


def _explicitly_hidden(tag: str, attributes: dict[str, str]) -> bool:
    if "hidden" in attributes:
        return True
    if attributes.get("aria-hidden", "").strip().lower() == "true":
        return True
    if tag == "dialog" and "open" not in attributes:
        return True
    if "popover" in attributes:
        return True
    return False


class _StyleCollector(HTMLParser):
    """Collect real same-document style blocks, excluding inert lookalikes."""

    _INERT = INERT_CONTAINERS - {"head", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, list[str] | None]] = []
        self.style_blocks: list[tuple[dict[str, str], list[str]]] = []
        self.stylesheet_links: list[dict[str, str]] = []
        self.plaintext_started = False

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        self._start(
            tag.lower(), attributes, self_closing=tag.lower() in VOID_ELEMENTS
        )

    def handle_startendtag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        folded = tag.lower()
        self._start(folded, attributes, self_closing=folded in VOID_ELEMENTS)

    def _start(
        self,
        tag: str,
        raw_attributes: list[tuple[str, str | None]],
        self_closing: bool,
    ) -> None:
        if self.plaintext_started:
            return
        parent_ignored = self.stack[-1][1] if self.stack else False
        ignored = parent_ignored or tag in self._INERT
        active_style = self.stack[-1][2] if self.stack else None
        attributes, _ = _attribute_map(raw_attributes)
        if tag == "link" and not parent_ignored:
            relationship = set(attributes.get("rel", "").casefold().split())
            if "stylesheet" in relationship and "disabled" not in attributes:
                self.stylesheet_links.append(attributes)
        if tag == "style" and not parent_ignored:
            active_style = []
            self.style_blocks.append((attributes, active_style))
        if not self_closing:
            self.stack.append((tag, ignored, active_style))
        if tag == "plaintext":
            self.plaintext_started = True

    def handle_endtag(self, tag: str) -> None:
        if self.plaintext_started:
            return
        tag = tag.lower()
        match = next(
            (index for index in range(len(self.stack) - 1, -1, -1)
             if self.stack[index][0] == tag),
            None,
        )
        if match is not None:
            del self.stack[match:]

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1][2] is not None:
            self.stack[-1][2].append(data)


def _balanced_css_blocks(css: str) -> list[tuple[str, str]]:
    """Return top-level ``(header, body)`` blocks from comment-free CSS."""
    blocks: list[tuple[str, str]] = []
    cursor = 0
    length = len(css)
    while cursor < length:
        opening = css.find("{", cursor)
        if opening == -1:
            break
        header = css[cursor:opening].strip()
        depth = 1
        quote = ""
        escaped = False
        index = opening + 1
        while index < length and depth:
            character = css[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif quote:
                if character == quote:
                    quote = ""
            elif character in {"'", '"'}:
                quote = character
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            index += 1
        if depth:
            break
        blocks.append((header, css[opening + 1 : index - 1]))
        cursor = index
    return blocks


def _unconditional_css_rules(css: str) -> list[tuple[str, str]]:
    """Return static rules and skip conditional media/container branches.

    A source-body sweep cannot know viewport size, media mode, feature support,
    or external cascade state. Those cases belong to the browser readback. It
    can honestly enforce unconditional rules, including rules inside ``@layer``.
    """
    rules: list[tuple[str, str]] = []
    for header, block in _balanced_css_blocks(css):
        lowered = header.casefold()
        if not header:
            continue
        if lowered in {"@media screen", "@media all"}:
            rules.extend(_unconditional_css_rules(block))
            continue
        if lowered.startswith(("@media", "@container", "@supports", "@document")):
            continue
        # Layers/scopes change cascade and selector meaning. The browser receipt
        # evaluates them; the static sweep deliberately does not guess.
        if lowered.startswith(("@layer", "@scope")):
            continue
        if header.startswith("@"):
            continue
        rules.append((header, block))
    return rules


@dataclass(frozen=True)
class _CssDeclaration:
    value: str
    important: bool


@dataclass(frozen=True)
class _CssRule:
    selector: str
    declarations: dict[str, _CssDeclaration]
    order: int
    generated_pseudo: str = ""
    specificity: tuple[int, int, int] = (0, 0, 0)


def _strip_css_comments(value: str) -> str:
    """Remove real CSS comments without treating markers in strings as comments."""

    output: list[str] = []
    index = 0
    quote = ""
    escaped = False
    while index < len(value):
        character = value[index]
        if escaped:
            output.append(character)
            escaped = False
            index += 1
            continue
        if character == "\\":
            output.append(character)
            escaped = True
            index += 1
            continue
        if quote:
            output.append(character)
            if character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
            output.append(character)
            index += 1
            continue
        if value.startswith("/*", index):
            closing = value.find("*/", index + 2)
            if closing == -1:
                break
            output.append(" ")
            index = closing + 2
            continue
        output.append(character)
        index += 1
    return "".join(output)


def _split_css_top_level(value: str, delimiter: str) -> list[str]:
    """Split CSS outside quoted strings, brackets, and function parentheses."""

    parts: list[str] = []
    buffer: list[str] = []
    quote = ""
    escaped = False
    round_depth = 0
    square_depth = 0
    for character in value:
        if escaped:
            buffer.append(character)
            escaped = False
            continue
        if character == "\\":
            buffer.append(character)
            escaped = True
            continue
        if quote:
            buffer.append(character)
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"'}:
            quote = character
            buffer.append(character)
            continue
        if character == "(":
            round_depth += 1
        elif character == ")":
            round_depth = max(0, round_depth - 1)
        elif character == "[":
            square_depth += 1
        elif character == "]":
            square_depth = max(0, square_depth - 1)
        if character == delimiter and round_depth == 0 and square_depth == 0:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(character)
    parts.append("".join(buffer))
    return parts


def _cascade_declarations(style: str) -> dict[str, _CssDeclaration]:
    declarations: dict[str, _CssDeclaration] = {}
    style = _strip_css_comments(style)
    for raw_declaration in _split_css_top_level(style, ";"):
        name_and_value = _split_css_top_level(raw_declaration, ":")
        if len(name_and_value) < 2:
            continue
        raw_name = name_and_value[0]
        raw_value = ":".join(name_and_value[1:])
        name = _decode_css_escapes(raw_name).strip().lower()
        value = _decode_css_escapes(raw_value).strip().lower()
        important = bool(re.search(r"!\s*important\s*$", value))
        value = re.sub(r"!\s*important\s*$", "", value).strip()
        if name:
            previous = declarations.get(name)
            if previous is not None and previous.important and not important:
                continue
            declarations[name] = _CssDeclaration(value, important)
    return declarations


def _screen_media_is_unconditional(media: str) -> bool:
    normalized = " ".join(media.casefold().split())
    return normalized in {"", "all", "screen"}


def _css_escape_end(value: str, index: int) -> int:
    """Return the first byte after one CSS escape beginning at ``index``."""

    cursor = index + 1
    if cursor >= len(value):
        return cursor
    if value[cursor] in "\r\n\f":
        if value[cursor : cursor + 2] == "\r\n":
            return cursor + 2
        return cursor + 1
    if value[cursor] in "0123456789abcdefABCDEF":
        start = cursor
        while (
            cursor < len(value)
            and cursor - start < 6
            and value[cursor] in "0123456789abcdefABCDEF"
        ):
            cursor += 1
        if cursor < len(value) and value[cursor].isspace():
            if value[cursor : cursor + 2] == "\r\n":
                cursor += 2
            else:
                cursor += 1
        return cursor
    return cursor + 1


def _consume_css_identifier(value: str, index: int) -> tuple[str, int] | None:
    """Consume a CSS identifier while preserving escaped punctuation boundaries."""

    cursor = index
    raw: list[str] = []
    while cursor < len(value):
        character = value[cursor]
        if character == "\\":
            escape_end = _css_escape_end(value, cursor)
            if escape_end <= cursor + 1:
                return None
            raw.append(value[cursor:escape_end])
            cursor = escape_end
            continue
        if character.isalnum() or character in {"_", "-"} or ord(character) >= 128:
            raw.append(character)
            cursor += 1
            continue
        break
    if not raw:
        return None
    decoded = _decode_css_escapes("".join(raw))
    return decoded, cursor


def _conservative_static_selector(selector: str) -> str:
    """Reduce unsupported pseudo selectors to a fail-closed static superset.

    The source contract cannot evaluate browser state or every Selectors Level 4
    function.  Keeping the non-pseudo portion means a hiding declaration such as
    ``aside:not(.x)`` or ``:where(aside)`` cannot disappear from the audit merely
    because its selector is outside the exact cascade subset.
    """

    output: list[str] = []
    index = 0
    square_depth = 0
    quote = ""
    while index < len(selector):
        character = selector[index]
        if not quote and character == "\\":
            escape_end = _css_escape_end(selector, index)
            output.append(selector[index:escape_end])
            index = escape_end
            continue
        if quote:
            output.append(character)
            if character == "\\" and index + 1 < len(selector):
                index += 1
                output.append(selector[index])
            elif character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"'} and square_depth:
            quote = character
            output.append(character)
            index += 1
            continue
        if character == "[":
            square_depth += 1
            output.append(character)
            index += 1
            continue
        if character == "]":
            square_depth = max(0, square_depth - 1)
            output.append(character)
            index += 1
            continue
        if character != ":" or square_depth:
            output.append(character)
            index += 1
            continue

        while index < len(selector) and selector[index] == ":":
            index += 1
        name_match = re.match(r"[A-Za-z-]+", selector[index:])
        if name_match is None:
            continue
        pseudo_name = name_match.group(0).casefold()
        index += len(name_match.group(0))
        if index >= len(selector) or selector[index] != "(":
            continue
        start = index + 1
        depth = 1
        index += 1
        inner_quote = ""
        while index < len(selector) and depth:
            item = selector[index]
            if inner_quote:
                if item == "\\" and index + 1 < len(selector):
                    index += 2
                    continue
                if item == inner_quote:
                    inner_quote = ""
            elif item in {"'", '"'}:
                inner_quote = item
            elif item == "(":
                depth += 1
            elif item == ")":
                depth -= 1
            index += 1
        argument = selector[start : index - 1] if depth == 0 else ""
        if pseudo_name in {"is", "where"} and argument:
            alternatives = _split_css_top_level(argument, ",")
            if len(alternatives) == 1:
                output.append(alternatives[0].strip())
    return "".join(output).strip()


def _expand_static_selector_alternatives(
    selector: str, _budget: list[int] | None = None
) -> list[str]:
    """Expand top-level ``:is``/``:where`` alternatives before reduction."""

    budget = [128] if _budget is None else _budget
    budget[0] -= 1
    if budget[0] < 0:
        return ["*"]

    square_depth = 0
    quote = ""
    index = 0
    while index < len(selector):
        character = selector[index]
        if not quote and character == "\\":
            index = _css_escape_end(selector, index)
            continue
        if quote:
            if character == "\\" and index + 1 < len(selector):
                index += 2
                continue
            if character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"'} and square_depth:
            quote = character
            index += 1
            continue
        if character == "[":
            square_depth += 1
            index += 1
            continue
        if character == "]":
            square_depth = max(0, square_depth - 1)
            index += 1
            continue
        if character != ":" or square_depth:
            index += 1
            continue
        match = re.match(r":(?:is|where)\(", selector[index:], re.IGNORECASE)
        if match is None:
            index += 1
            continue
        open_index = index + len(match.group(0)) - 1
        cursor = open_index + 1
        depth = 1
        inner_quote = ""
        while cursor < len(selector) and depth:
            item = selector[cursor]
            if inner_quote:
                if item == "\\" and cursor + 1 < len(selector):
                    cursor += 2
                    continue
                if item == inner_quote:
                    inner_quote = ""
            elif item in {"'", '"'}:
                inner_quote = item
            elif item == "(":
                depth += 1
            elif item == ")":
                depth -= 1
            cursor += 1
        if depth:
            return [selector]
        alternatives = _split_css_top_level(
            selector[open_index + 1 : cursor - 1], ","
        )
        if len(alternatives) > 32:
            return ["*"]
        expanded: list[str] = []
        for alternative in alternatives:
            replacement = selector[:index] + alternative.strip() + selector[cursor:]
            expanded.extend(
                _expand_static_selector_alternatives(replacement, budget)
            )
        return expanded or [selector]
    return [selector]


def _static_css_rules(body: str) -> list[_CssRule]:
    collector = _StyleCollector()
    collector.feed(body)
    collector.close()
    rules: list[_CssRule] = []
    order = 0
    for attributes, block in collector.style_blocks:
        if (
            attributes.get("type", "").strip().casefold() not in {"", "text/css"}
            or "disabled" in attributes
            or not _screen_media_is_unconditional(
            attributes.get("media", "")
            )
        ):
            continue
        css = _strip_css_comments("".join(block))
        css = re.sub(
            r"@(?:charset|import|namespace)\b[^;]*;", "", css, flags=re.IGNORECASE
        )
        for selector_list, declarations_text in _unconditional_css_rules(css):
            declarations = _cascade_declarations(declarations_text)
            for selector in _split_css_top_level(selector_list, ","):
                selector = selector.strip()
                pseudo = ""
                pseudo_match = re.search(
                    r"(?<!\\)(?:::?)(before|after)\s*$", selector, re.I
                )
                if pseudo_match:
                    pseudo = pseudo_match.group(1).casefold()
                    selector = selector[: pseudo_match.start()].rstrip()
                selector_specificity = _selector_specificity(selector)
                for expanded_selector in _expand_static_selector_alternatives(
                    selector
                ):
                    static_selector = expanded_selector
                    if len(_split_css_top_level(static_selector, ":")) != 1:
                        static_selector = _conservative_static_selector(
                            static_selector
                        )
                    decoded_selector = _decode_css_escapes(static_selector)
                    if (
                        decoded_selector != static_selector
                        and re.search(
                            r":{1,2}[A-Za-z-]+\s*\(", decoded_selector
                        )
                    ):
                        static_selector = _conservative_static_selector(
                            decoded_selector
                        )
                    if static_selector and not static_selector.startswith("@"):
                        rules.append(
                            _CssRule(
                                static_selector,
                                declarations,
                                order,
                                pseudo,
                                selector_specificity,
                            )
                        )
                        order += 1
    return rules


def _document_css_contract_problems(body: str) -> list[str]:
    """Reject active CSS imports the source sweep cannot safely bind or cascade."""

    collector = _StyleCollector()
    collector.feed(body)
    collector.close()
    problems: list[str] = []
    for attributes, block in collector.style_blocks:
        media_type = attributes.get("type", "").split(";", 1)[0].strip().casefold()
        if media_type not in {"", "text/css"} or "disabled" in attributes:
            continue
        css = _decode_css_escapes(_strip_css_comments("".join(block)))
        if re.search(r"@import\b", css, re.IGNORECASE):
            problems.append(
                "active CSS @import is not allowed on a structurally audited page"
            )
        for target in _css_fetch_targets(css):
            if problem := _css_fetch_url_problem(target):
                problems.append("same-document CSS contains a URL that " + problem)
        privacy_css = re.sub(r"url\([^)]*\)", " ", css, flags=re.IGNORECASE)
        privacy_css = re.sub(
            r"(?:-webkit-)?image-set\([^)]*\)", " ", privacy_css,
            flags=re.IGNORECASE,
        )
        privacy_css = re.sub(r"[\t\r\n]", " ", privacy_css)
        if problem := _public_value_problem(privacy_css):
            problems.append("same-document CSS " + problem)
    for attributes in collector.stylesheet_links:
        href = attributes.get("href", "").strip()
        if not href:
            problems.append("active stylesheet link has no href")
            continue
        if problem := _css_fetch_url_problem(href):
            problems.append("active stylesheet link URL " + problem)
    return problems


def _css_fetch_targets(css: str) -> list[str]:
    targets = [
        next(value for value in match.groups() if value is not None)
        for match in re.finditer(
            r"url\(\s*(?:\"([^\"]*)\"|'([^']*)'|([^)'\"\s]+))\s*\)",
            css,
            re.IGNORECASE,
        )
    ]
    for image_set in re.finditer(
        r"(?:-webkit-)?image-set\((.*?)\)", css, re.IGNORECASE | re.DOTALL
    ):
        for quoted in re.finditer(r"([\"'])(.*?)\1", image_set.group(1), re.DOTALL):
            if quoted.group(2) not in targets:
                targets.append(quoted.group(2))
    return targets


def _css_fetch_url_problem(target: str) -> str | None:
    resolved = urljoin("https://public-css.invalid/", target.strip())
    return _public_link_url_problem(resolved)


def _css_string_literals(value: str) -> tuple[list[str], bool]:
    """Return decoded CSS strings and whether a string was left unclosed."""

    strings: list[str] = []
    index = 0
    while index < len(value):
        if value[index] not in {"'", '"'}:
            index += 1
            continue
        quote = value[index]
        index += 1
        start = index
        escaped = False
        raw: list[str] = []
        while index < len(value):
            character = value[index]
            if escaped:
                raw.append("\\" + character)
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                strings.append(_decode_css_escapes("".join(raw)))
                index += 1
                break
            else:
                raw.append(character)
            index += 1
        else:
            return strings, True
        _ = start
    return strings, False


_JS_JSON_ESCAPE = re.compile(
    r"\\u\{([0-9A-Fa-f]{1,6})\}|\\u([0-9A-Fa-f]{4})|"
    r"\\x([0-9A-Fa-f]{2})|\\([0-3][0-7]{0,2}|[4-7][0-7]?)"
)


def _joined_unicode_scalars(value: str) -> tuple[str, bool]:
    """Join UTF-16 surrogate pairs and report any unpaired surrogate."""

    joined: list[str] = []
    invalid = False
    index = 0
    while index < len(value):
        number = ord(value[index])
        if 0xD800 <= number <= 0xDBFF:
            if index + 1 < len(value):
                low = ord(value[index + 1])
                if 0xDC00 <= low <= 0xDFFF:
                    joined.append(
                        chr(0x10000 + ((number - 0xD800) << 10) + low - 0xDC00)
                    )
                    index += 2
                    continue
            invalid = True
            joined.append("\ufffd")
        elif 0xDC00 <= number <= 0xDFFF:
            invalid = True
            joined.append("\ufffd")
        else:
            joined.append(value[index])
        index += 1
    return "".join(joined), invalid


def _decode_js_json_escapes(value: str) -> tuple[str, str | None]:
    """Decode bounded JS/JSON escapes and fail closed on ambiguous residue.

    Classic-script octal escapes are included because otherwise values such as
    ``\\057Users/...`` and ``name\\100example.com`` evade the public-byte
    privacy boundary. Strict JSON never accepts those spellings, so treating
    them conservatively on every script surface cannot make invalid JSON-LD
    evidence appear valid.
    """

    invalid_codepoint = False

    def codepoint(match: re.Match[str]) -> str:
        nonlocal invalid_codepoint
        if match.group(1) is not None or match.group(2) is not None:
            number = int(match.group(1) or match.group(2), 16)
        elif match.group(3) is not None:
            number = int(match.group(3), 16)
        else:
            number = int(match.group(4), 8)
        if number > 0x10FFFF:
            invalid_codepoint = True
            return "\ufffd"
        return chr(number)

    decoded = value
    for _ in range(MAX_PUBLIC_DECODE_ROUNDS):
        changed = _JS_JSON_ESCAPE.sub(codepoint, decoded)
        if changed == decoded:
            break
        decoded = changed
    else:
        if _JS_JSON_ESCAPE.search(decoded):
            normalized, _ = _joined_unicode_scalars(decoded)
            return normalized, "contains excessively nested JavaScript/JSON escaping"

    decoded, unpaired_surrogate = _joined_unicode_scalars(decoded)
    if invalid_codepoint:
        return decoded, "contains an invalid JavaScript/JSON code point escape"
    if unpaired_surrogate:
        return decoded, "contains an unpaired UTF-16 surrogate escape"
    return decoded, None


ATTRIBUTE_SELECTOR = re.compile(
    r"\[\s*([A-Za-z_:][A-Za-z0-9_:.-]*)\s*"
    r"(?:(~=|\|=|\^=|\$=|\*=|=)\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\]\s]+))\s*([iIsS])?)?\s*\]"
)


def _attribute_selector_matches(
    match: re.Match[str], attributes: dict[str, str]
) -> bool:
    name = match.group(1).lower()
    if name not in attributes:
        return False
    operator = match.group(2)
    if operator is None:
        return True
    expected = next(
        value for value in match.group(3, 4, 5) if value is not None
    )
    actual = attributes[name]
    if (match.group(6) or "").casefold() == "i":
        actual, expected = actual.casefold(), expected.casefold()
    if operator == "=":
        return actual == expected
    if operator == "~=":
        return expected in actual.split()
    if operator == "|=":
        return actual == expected or actual.startswith(expected + "-")
    if operator == "^=":
        return actual.startswith(expected)
    if operator == "$=":
        return actual.endswith(expected)
    return expected in actual


def _compound_selector_matches(
    compound: str, tag: str, attributes: dict[str, str]
) -> bool:
    """Match the static tag/class/id/attribute subset used by generated pages."""
    cursor = 0
    tag_identifier: tuple[str, int] | None = None
    if compound.startswith("*"):
        tag_identifier = ("*", 1)
    elif compound and compound[0] not in {".", "#", "["}:
        tag_identifier = _consume_css_identifier(compound, 0)
    if tag_identifier:
        selected_tag, cursor = tag_identifier
        selected_tag = selected_tag.casefold()
        if selected_tag not in {"*", tag}:
            return False
    matched_any = tag_identifier is not None
    while cursor < len(compound):
        character = compound[cursor]
        if character in {".", "#"}:
            identifier = _consume_css_identifier(compound, cursor + 1)
            if identifier is None:
                return False
            name, cursor = identifier
            if character == "." and name not in attributes.get("class", "").split():
                return False
            if character == "#" and attributes.get("id") != name:
                return False
            matched_any = True
            continue
        if character == "[":
            attribute_end = cursor + 1
            quote = ""
            while attribute_end < len(compound):
                item = compound[attribute_end]
                if item == "\\":
                    attribute_end = _css_escape_end(compound, attribute_end)
                    continue
                if quote:
                    if item == quote:
                        quote = ""
                elif item in {"'", '"'}:
                    quote = item
                elif item == "]":
                    attribute_end += 1
                    break
                attribute_end += 1
            decoded_attribute = _decode_css_escapes(
                compound[cursor:attribute_end]
            )
            attribute_match = ATTRIBUTE_SELECTOR.fullmatch(decoded_attribute)
            if attribute_match is None or not _attribute_selector_matches(
                attribute_match, attributes
            ):
                return False
            cursor = attribute_end
            matched_any = True
            continue
        return False
    return matched_any


def _selector_steps(selector: str) -> tuple[list[str], list[str]] | None:
    """Split a static descendant/child selector without splitting attributes."""
    compounds: list[str] = []
    combinators: list[str] = []
    buffer: list[str] = []
    bracket_depth = 0
    quote = ""
    pending_descendant = False
    value = selector.strip()
    index = 0
    while index < len(value):
        character = value[index]
        if character == "\\":
            escape_end = _css_escape_end(value, index)
            buffer.append(value[index:escape_end])
            index = escape_end
            continue
        if quote:
            buffer.append(character)
            if character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"'} and bracket_depth:
            quote = character
            buffer.append(character)
            index += 1
            continue
        if character == "[":
            bracket_depth += 1
            buffer.append(character)
            index += 1
            continue
        if character == "]":
            bracket_depth = max(0, bracket_depth - 1)
            buffer.append(character)
            index += 1
            continue
        if bracket_depth:
            buffer.append(character)
            index += 1
            continue
        if character in {"+", "~"}:
            return None
        if character == ">":
            if buffer:
                compounds.append("".join(buffer).strip())
                buffer = []
            if not compounds or len(combinators) >= len(compounds):
                return None
            combinators.append(">")
            pending_descendant = False
            index += 1
            continue
        if character.isspace():
            if buffer:
                compounds.append("".join(buffer).strip())
                buffer = []
                pending_descendant = True
            index += 1
            continue
        if pending_descendant:
            if len(combinators) < len(compounds):
                combinators.append(" ")
            pending_descendant = False
        buffer.append(character)
        index += 1
    if buffer:
        compounds.append("".join(buffer).strip())
    if not compounds or len(combinators) != len(compounds) - 1:
        return None
    return compounds, combinators


def _selector_matches_element_path(
    selector: str,
    path: tuple[tuple[str, dict[str, str]], ...],
    end_index: int,
) -> bool:
    parsed = _selector_steps(selector)
    if parsed is None:
        return False
    compounds, combinators = parsed
    if not _compound_selector_matches(compounds[-1], *path[end_index]):
        return False
    path_index = end_index
    for selector_index in range(len(compounds) - 2, -1, -1):
        combinator = combinators[selector_index]
        if combinator == ">":
            path_index -= 1
            if path_index < 0 or not _compound_selector_matches(
                compounds[selector_index], *path[path_index]
            ):
                return False
            continue
        path_index -= 1
        while path_index >= 0 and not _compound_selector_matches(
            compounds[selector_index], *path[path_index]
        ):
            path_index -= 1
        if path_index < 0:
            return False
    return True


def _selector_specificity(selector: str) -> tuple[int, int, int]:
    """Return Selectors-4 specificity for the supported conservative subset."""

    specificity = [0, 0, 0]
    index = 0
    expect_type = True
    while index < len(selector):
        character = selector[index]
        if character.isspace() or character in {">", "+", "~", ","}:
            expect_type = True
            index += 1
            continue
        if character == "[":
            specificity[1] += 1
            depth = 1
            quote = ""
            index += 1
            while index < len(selector) and depth:
                item = selector[index]
                if item == "\\":
                    index = _css_escape_end(selector, index)
                    continue
                if quote:
                    if item == quote:
                        quote = ""
                elif item in {"'", '"'}:
                    quote = item
                elif item == "[":
                    depth += 1
                elif item == "]":
                    depth -= 1
                index += 1
            expect_type = False
            continue
        if character in {".", "#"}:
            identifier = _consume_css_identifier(selector, index + 1)
            if identifier is None:
                index += 1
                continue
            specificity[0 if character == "#" else 1] += 1
            index = identifier[1]
            expect_type = False
            continue
        if character == ":":
            pseudo_element = selector.startswith("::", index)
            index += 2 if pseudo_element else 1
            identifier = _consume_css_identifier(selector, index)
            if identifier is None:
                continue
            pseudo_name, index = identifier
            pseudo_name = pseudo_name.casefold()
            if index < len(selector) and selector[index] == "(":
                start = index + 1
                depth = 1
                quote = ""
                index += 1
                while index < len(selector) and depth:
                    item = selector[index]
                    if item == "\\":
                        index = _css_escape_end(selector, index)
                        continue
                    if quote:
                        if item == quote:
                            quote = ""
                    elif item in {"'", '"'}:
                        quote = item
                    elif item == "(":
                        depth += 1
                    elif item == ")":
                        depth -= 1
                    index += 1
                argument = selector[start : index - 1] if depth == 0 else ""
                if pseudo_name in {"is", "not", "has"} and argument:
                    alternatives = [
                        _selector_specificity(item.strip())
                        for item in _split_css_top_level(argument, ",")
                        if item.strip()
                    ]
                    if alternatives:
                        maximum = max(alternatives)
                        specificity = [
                            specificity[position] + maximum[position]
                            for position in range(3)
                        ]
                elif pseudo_name != "where":
                    specificity[1] += 1
            elif pseudo_element or pseudo_name in {"before", "after"}:
                specificity[2] += 1
            else:
                specificity[1] += 1
            expect_type = False
            continue
        if character == "*":
            index += 1
            expect_type = False
            continue
        identifier = _consume_css_identifier(selector, index)
        if identifier is not None:
            if expect_type:
                specificity[2] += 1
            index = identifier[1]
            expect_type = False
            continue
        index += 1
    return tuple(specificity)


def _css_hides_path(
    path: tuple[tuple[str, dict[str, str]], ...], rules: list[_CssRule]
) -> bool:
    # text/html supplies html/body wrappers for fragments and reparents ordinary
    # body content out of an omitted body. Model those nodes so selectors such as
    # ``body > aside`` and ``html aside`` keep their browser-effective meaning.
    if not path or path[0][0] != "html":
        if path and path[0][0] == "body":
            path = (("html", {}),) + path
        else:
            path = (("html", {}), ("body", {})) + path
    elif len(path) < 2 or path[1][0] != "body":
        path = (path[0], ("body", {}), *path[1:])
    relevant_properties = {
        "clip",
        "clip-path",
        "color",
        "display",
        "filter",
        "font-size",
        "height",
        "left",
        "mask",
        "mask-image",
        "visibility",
        "content-visibility",
        "opacity",
        "position",
        "overflow",
        "overflow-y",
        "text-indent",
        "top",
        "transform",
    }
    inherited_visibility = "visible"
    inherited_color = ""
    inherited_font_size = ""
    inherited_text_indent = ""
    for end_index, (_, attributes) in enumerate(path):
        winners: dict[
            str, tuple[tuple[int, int, int, int, int, int], str]
        ] = {}
        for rule in rules:
            if not _selector_matches_element_path(rule.selector, path, end_index):
                continue
            specificity = rule.specificity
            for name, declaration in rule.declarations.items():
                if name not in relevant_properties:
                    continue
                precedence = (
                    int(declaration.important),
                    0,
                    *specificity,
                    rule.order,
                )
                if name not in winners or precedence >= winners[name][0]:
                    winners[name] = (precedence, declaration.value)

        inline = _cascade_declarations(attributes.get("style", ""))
        for name, declaration in inline.items():
            if name not in relevant_properties:
                continue
            # Inline declarations outrank ordinary author selectors; stylesheet
            # !important still outranks an ordinary inline declaration.
            precedence = (int(declaration.important), 1, 0, 0, 0, 0)
            if name not in winners or precedence >= winners[name][0]:
                winners[name] = (precedence, declaration.value)

        computed_subset = {name: value for name, (_, value) in winners.items()}
        opacity = computed_subset.get("opacity", "")
        normalized_opacity = re.sub(r"\s+", "", opacity)
        zero_opacity = bool(opacity) and bool(
            re.fullmatch(r"(?:0(?:\.0*)?%?|calc\(0(?:\.0*)?%?\))", normalized_opacity)
        )
        position = computed_subset.get("position", "")
        offscreen_position = position in {"absolute", "fixed"} and any(
            re.search(
                r"-\s*(?:[1-9]\d{3,}|\d{4,})(?:px|rem|em|vw|vh|cm|mm|in|pt|pc)\b",
                value,
            )
            for value in (
                computed_subset.get("left", ""),
                computed_subset.get("top", ""),
            )
        )
        transform = computed_subset.get("transform", "")
        transform_hides = bool(
            re.search(
                r"(?:translate(?:x|y)?\([^)]*-\s*(?:[1-9]\d{3,}|\d{4,})px|"
                r"scale(?:x|y)?\(\s*0(?:\.0*)?%?(?:[\s,)]))",
                transform,
            )
        )
        clip_path = computed_subset.get("clip-path", "")
        clip = re.sub(r"\s+", "", computed_subset.get("clip", ""))
        clipped = bool(
            re.search(r"inset\(\s*100%", clip_path)
            or re.search(r"circle\(\s*0(?:px|%)?", clip_path)
            or clip in {"rect(0,0,0,0)", "rect(0px,0px,0px,0px)"}
        )
        filter_hides = bool(
            re.search(r"opacity\(\s*0(?:\.0*)?\s*\)", computed_subset.get("filter", ""))
        )
        mask_hides = any(
            "transparent" in computed_subset.get(name, "")
            for name in ("mask", "mask-image")
        )
        declared_color = computed_subset.get("color", "")
        if declared_color and declared_color not in {"inherit", "unset"}:
            inherited_color = "" if declared_color in {
                "initial", "revert", "revert-layer"
            } else declared_color
        color = re.sub(r"\s+", "", inherited_color)
        transparent_text = color == "transparent" or bool(
            re.fullmatch(
                r"rgba\((?:[^)]*,|[^)]*/\s*)0(?:\.0*)?%?\)", color
            )
        )
        declared_text_indent = computed_subset.get("text-indent", "")
        if declared_text_indent and declared_text_indent not in {"inherit", "unset"}:
            inherited_text_indent = "" if declared_text_indent in {
                "initial", "revert", "revert-layer"
            } else declared_text_indent
        text_indent = inherited_text_indent
        indented_offscreen = bool(
            re.search(
                r"-\s*(?:[1-9]\d{3,}|\d{4,})(?:px|rem|em|vw|vh|cm|mm|in|pt|pc)\b",
                text_indent,
            )
        )
        declared_font_size = computed_subset.get("font-size", "")
        if declared_font_size and declared_font_size not in {"inherit", "unset"}:
            inherited_font_size = "" if declared_font_size in {
                "initial", "revert", "revert-layer"
            } else declared_font_size
        zero_font_size = bool(
            re.fullmatch(
                r"(?:0(?:\.0*)?(?:px|rem|em|%|pt)?|calc\(0(?:\.0*)?(?:px|rem|em|%|pt)?\))",
                re.sub(r"\s+", "", inherited_font_size),
            )
        )
        zero_clipped_height = bool(
            re.fullmatch(
                r"0(?:\.0*)?(?:px|rem|em|%|vh)?",
                re.sub(r"\s+", "", computed_subset.get("height", "")),
            )
        ) and any(
            "hidden" in computed_subset.get(name, "")
            for name in ("overflow", "overflow-y")
        )
        if (
            computed_subset.get("display") == "none"
            or computed_subset.get("content-visibility") == "hidden"
            or zero_opacity
            or offscreen_position
            or transform_hides
            or clipped
            or filter_hides
            or mask_hides
            or zero_clipped_height
        ):
            return True
        if "visibility" in computed_subset:
            declared_visibility = computed_subset["visibility"]
            if declared_visibility not in {"inherit", "unset", "revert", "revert-layer"}:
                inherited_visibility = (
                    "visible" if declared_visibility == "initial" else declared_visibility
                )
    return (
        inherited_visibility in {"hidden", "collapse"}
        or transparent_text
        or indented_offscreen
        or zero_font_size
    )


def _browser_document_path(
    path: tuple[tuple[str, dict[str, str]], ...]
) -> tuple[tuple[str, dict[str, str]], ...]:
    """Add the implicit html/body wrappers supplied by a text/html parser."""

    if path and path[0][0] == "html":
        return path
    if path and path[0][0] == "body":
        return (("html", {}),) + path
    return (("html", {}), ("body", {})) + path


class _ProvenanceParser(HTMLParser):
    """Collect structurally renderable provenance rails from the HTML tree.

    ``HTMLParser`` does not emit tags from comments or script/style data. We also
    suppress inert text containers and native closed/hidden subtrees. Static CSS
    is applied afterward; final browser-computed visibility belongs to the
    external receipt rather than this source parser.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[_HtmlFrame] = []
        self.rails: list[_ProvenanceRail] = []
        self.all_rails: list[_ProvenanceRail] = []
        self.hidden_rail_count = 0
        self.plaintext_started = False
        self.inside_fleet_markers = False
        self.next_node_id = 1
        self.outside_audit_attributes: list[str] = []
        self.outside_visible_text: list[str] = []
        self.outside_root_visible_text: list[str] = []
        self.outside_meta_authors: list[str] = []
        self.outside_modified_times: list[str] = []
        self.outside_updated_times: list[str] = []
        self.outside_updated_time_paths: list[
            tuple[str, tuple[tuple[str, dict[str, str]], ...]]
        ] = []
        self.outside_itemprop_authors: list[str] = []
        self.outside_itemprop_modified: list[str] = []
        self.outside_itemprop_author_paths: list[
            tuple[str, tuple[tuple[str, dict[str, str]], ...]]
        ] = []
        self.outside_itemprop_modified_paths: list[
            tuple[str, tuple[tuple[str, dict[str, str]], ...]]
        ] = []
        self.outside_title_text: list[str] = []
        self.outside_visible_nodes: list[_VisibleText] = []
        self.outside_element_paths: list[
            tuple[tuple[str, dict[str, str]], ...]
        ] = []
        self.itemprop_buffers: dict[
            int,
            tuple[
                str,
                list[str],
                tuple[tuple[str, dict[str, str]], ...],
            ],
        ] = {}

    def handle_comment(self, data: str) -> None:
        if self.stack and self.stack[-1].rail is not None:
            self.stack[-1].rail.public_raw_text.append(data)
        # These are exact byte-boundary comments, not free-form labels. Ignore
        # lookalikes inside an inert container just as we ignore inert rails.
        if self.plaintext_started or any(frame.ignored for frame in self.stack):
            return
        marker = data.strip()
        if marker == "BM-FLEET-PAGE:START":
            self.inside_fleet_markers = True
        elif marker == "BM-FLEET-PAGE:END":
            self.inside_fleet_markers = False

    def handle_pi(self, data: str) -> None:
        if self.stack and self.stack[-1].rail is not None:
            self.stack[-1].rail.public_raw_text.append(data)

    def handle_decl(self, decl: str) -> None:
        if self.stack and self.stack[-1].rail is not None:
            self.stack[-1].rail.public_raw_text.append(decl)

    def unknown_decl(self, data: str) -> None:
        if self.stack and self.stack[-1].rail is not None:
            self.stack[-1].rail.public_raw_text.append(data)

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        self._start(tag.lower(), attributes, self_closing=tag.lower() in VOID_ELEMENTS)

    def handle_startendtag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        folded = tag.lower()
        self._start(folded, attributes, self_closing=folded in VOID_ELEMENTS)

    def _start(
        self,
        tag: str,
        raw_attributes: list[tuple[str, str | None]],
        self_closing: bool,
    ) -> None:
        attributes, duplicates = _attribute_map(raw_attributes)
        parent = self.stack[-1] if self.stack else None
        node_id = self.next_node_id
        self.next_node_id += 1
        sibling_index = parent.next_child_index if parent else 0
        if parent:
            parent.next_child_index += 1
        ignored = (
            self.plaintext_started
            or bool(parent and parent.ignored)
            or tag in INERT_CONTAINERS
            or tag in NON_RENDERABLE_RAIL_ANCESTORS
        )
        if tag == "plaintext":
            self.plaintext_started = True
        inherited_hidden = bool(parent and parent.children_hidden)
        if (
            parent
            and parent.closed_details
            and tag == "summary"
            and not parent.summary_seen
        ):
            inherited_hidden = parent.element_hidden
            parent.summary_seen = True
        element_hidden = inherited_hidden or _explicitly_hidden(tag, attributes)
        closed_details = tag == "details" and "open" not in attributes
        children_hidden = element_hidden or closed_details
        parent_rail = parent.rail if parent else None
        rail = parent_rail
        owns_rail = False

        # Metadata in a real document head is not reader-visible, but it is an
        # independent machine-readable truth surface. Ignore only metadata
        # nested in genuinely inert/raw containers such as template or script.
        metadata_inert = any(
            frame.tag in (INERT_CONTAINERS - {"head"}) for frame in self.stack
        )
        itemprop_tokens = set(
            attributes.get("itemprop", "").strip().casefold().split()
        )
        if parent_rail is None and not metadata_inert and tag == "meta":
            meta_name = attributes.get("name", "").strip().casefold()
            meta_property = attributes.get("property", "").strip().casefold()
            content = attributes.get("content", "").strip()
            if (
                meta_name == "author"
                or "author" in itemprop_tokens
            ) and content:
                self.outside_meta_authors.append(content)
            if meta_property in {
                "article:modified_time", "og:updated_time",
            } or (
                meta_name in {"last-modified", "last_modified"}
                or "datemodified" in itemprop_tokens
            ):
                if content:
                    self.outside_modified_times.append(content)
            if "name" in itemprop_tokens and content:
                for item in self.stack:
                    buffered = self.itemprop_buffers.get(item.node_id)
                    if buffered is not None and buffered[0] == "author":
                        buffered[1].append(content)
        if (
            parent_rail is None
            and not ignored
            and not element_hidden
            and tag == "time"
            and attributes.get("datetime", "").strip()
            and (
                {"updated", "modified"}
                & set(attributes.get("class", "").casefold().split())
                or "datemodified" in itemprop_tokens
            )
        ):
            self.outside_updated_times.append(attributes["datetime"].strip())
            self.outside_updated_time_paths.append(
                (
                    attributes["datetime"].strip(),
                    tuple((frame.tag, frame.attributes) for frame in self.stack)
                    + ((tag, attributes),),
                )
            )

        itemprop = (
            "author" if "author" in itemprop_tokens
            else "datemodified" if "datemodified" in itemprop_tokens
            else ""
        )
        if (
            parent_rail is None
            and not ignored
            and not element_hidden
            and itemprop
            and tag != "meta"
        ):
            # An unscoped itemprop is a page-level claim. Scoped cards are only
            # page truth when their Article scope is explicitly the main entity;
            # otherwise a related-card author/date must not be conflated with
            # the document's own provenance.
            scope = next(
                (
                    frame
                    for frame in reversed(self.stack)
                    if "itemscope" in frame.attributes
                ),
                None,
            )
            scope_is_article = bool(
                scope
                and "article" in scope.attributes.get("itemtype", "").casefold()
            )
            scope_is_main_article = bool(
                scope_is_article
                and (
                    "mainentity"
                    in scope.attributes.get("itemprop", "").casefold().split()
                    or scope.tag == "article"
                    or any(frame.tag == "main" for frame in self.stack)
                )
                and not any(
                    frame.tag in {"aside", "nav", "footer"}
                    for frame in self.stack
                    if frame is not scope
                )
            )
            if scope is None or scope_is_main_article:
                itemprop_path = (
                    tuple((frame.tag, frame.attributes) for frame in self.stack)
                    + ((tag, attributes),)
                )
                direct_value = self._microdata_attribute_value(tag, attributes)
                if direct_value is not None:
                    # URL-valued author properties identify a profile/resource,
                    # not a literal human name. They cannot be compared to the
                    # rail's public-name field without an explicit URL binding.
                    if itemprop != "author" or tag not in {
                        "a", "area", "link", "object", "audio", "embed",
                        "iframe", "img", "source", "track", "video",
                    }:
                        self._record_itemprop(itemprop, direct_value, itemprop_path)
                else:
                    self.itemprop_buffers[node_id] = (itemprop, [], itemprop_path)

        if (
            parent_rail is None
            and not ignored
            and not element_hidden
            and tag in PUBLIC_TEXT_BOUNDARY_TAGS
        ):
            self.outside_visible_text.append("\n")

        if (
            not ignored
            and tag in {"aside", "section"}
            and "data-document-provenance" in attributes
        ):
            path = tuple((frame.tag, frame.attributes) for frame in self.stack) + (
                (tag, attributes),
            )
            candidate = _ProvenanceRail(
                tag,
                attributes,
                duplicates,
                [],
                [],
                [],
                path,
                self.inside_fleet_markers,
            )
            rail = candidate
            owns_rail = True
            self.all_rails.append(candidate)
            if element_hidden:
                self.hidden_rail_count += 1
            else:
                self.rails.append(candidate)

        if parent_rail is None and not owns_rail:
            if not ignored and not element_hidden:
                self.outside_element_paths.append(
                    tuple((frame.tag, frame.attributes) for frame in self.stack)
                    + ((tag, attributes),)
                )
            for name in attributes:
                if (
                    name in OUTSIDE_PROVENANCE_DATA_ATTRIBUTES
                    or _looks_like_outside_audit_attribute(name)
                ):
                    self.outside_audit_attributes.append(f"<{tag}> {name}")

        for active_rail in {id(item): item for item in (parent_rail, rail) if item}.values():
            if tag in PUBLIC_TEXT_BOUNDARY_TAGS and not owns_rail:
                active_rail.public_raw_text.append("\n")
            for name in duplicates:
                duplicate = f"<{tag}> {name}"
                if duplicate not in active_rail.subtree_duplicate_attributes:
                    active_rail.subtree_duplicate_attributes.append(duplicate)
            if not (owns_rail and active_rail is rail):
                active_rail.subtree_attributes.append((tag, attributes))
                active_rail.subtree_visibility_paths.append(
                    tuple((frame.tag, frame.attributes) for frame in self.stack)
                    + ((tag, attributes),)
                )

        active_time = parent.active_time if parent else None
        if not ignored and not element_hidden and tag == "time" and rail is not None:
            path = tuple((frame.tag, frame.attributes) for frame in self.stack) + (
                (tag, attributes),
            )
            leading_text = tuple(rail.visible_text)
            active_time = _SemanticTime(
                attributes.get("datetime"),
                duplicates,
                [],
                path,
                leading_text,
                node_id,
                parent.node_id if parent else 0,
                sibling_index,
            )
            rail.times.append(active_time)

        active_link = parent.active_link if parent else None
        if not ignored and not element_hidden and tag == "a" and rail is not None:
            path = tuple((frame.tag, frame.attributes) for frame in self.stack) + (
                (tag, attributes),
            )
            active_link = _VisibleLink(
                attributes.get("href"), [], path, tuple(rail.visible_text)
            )
            rail.links.append(active_link)

        if (
            not ignored
            and not element_hidden
            and tag in {"br", "hr"}
            and rail is not None
        ):
            path = tuple((frame.tag, frame.attributes) for frame in self.stack) + (
                (tag, attributes),
            )
            rail.visible_text.append(
                _VisibleText("\u2029", path, ((node_id, sibling_index),), sibling_index)
            )

        frame = _HtmlFrame(
            tag,
            ignored,
            element_hidden,
            children_hidden,
            rail,
            active_time,
            active_link,
            attributes,
            closed_details,
            False,
            owns_rail,
            node_id,
            sibling_index,
            0,
        )
        if self_closing:
            if node_id in self.itemprop_buffers:
                self._finish_itemprop(node_id)
            if owns_rail and rail is not None:
                rail.closed = True
            return
        self.stack.append(frame)

    def handle_endtag(self, tag: str) -> None:
        if self.plaintext_started:
            return
        tag = tag.lower()
        match = next(
            (index for index in range(len(self.stack) - 1, -1, -1)
             if self.stack[index].tag == tag),
            None,
        )
        if match is None:
            return
        closing = self.stack[match:]
        del self.stack[match:]
        for frame in closing:
            if frame.node_id in self.itemprop_buffers:
                self._finish_itemprop(frame.node_id)
            if frame.rail is not None and frame.tag in PUBLIC_TEXT_BOUNDARY_TAGS:
                frame.rail.public_raw_text.append("\n")
            if (
                frame.rail is None
                and not frame.ignored
                and not frame.children_hidden
                and frame.tag in PUBLIC_TEXT_BOUNDARY_TAGS
            ):
                self.outside_visible_text.append("\n")
            if frame.owns_rail and frame.rail is not None:
                frame.rail.closed = True

    def handle_data(self, data: str) -> None:
        if not self.stack:
            if not self.plaintext_started:
                self.outside_visible_text.append(data)
                self.outside_root_visible_text.append(data)
            return
        frame = self.stack[-1]
        if frame.rail is None and any(item.tag == "title" for item in self.stack):
            self.outside_title_text.append(data)
        if frame.rail is not None:
            frame.rail.public_raw_text.append(data)
        if frame.ignored or frame.children_hidden:
            return
        for item in self.stack:
            buffered = self.itemprop_buffers.get(item.node_id)
            if buffered is not None:
                buffered[1].append(data)
        visible_text = _VisibleText(
            data,
            tuple((item.tag, item.attributes) for item in self.stack),
            tuple((item.node_id, item.sibling_index) for item in self.stack),
            frame.next_child_index,
        )
        if data.strip():
            frame.next_child_index += 1
        if frame.rail is not None:
            frame.rail.visible_text.append(visible_text)
        else:
            self.outside_visible_text.append(data)
            self.outside_visible_nodes.append(visible_text)
        if frame.active_time is not None:
            frame.active_time.text.append(visible_text)
        if frame.active_link is not None:
            frame.active_link.text.append(visible_text)

    def _finish_itemprop(self, node_id: int) -> None:
        itemprop, chunks, path = self.itemprop_buffers.pop(node_id)
        value = " ".join("".join(chunks).split())
        if not value:
            return
        self._record_itemprop(itemprop, value, path)

    @staticmethod
    def _microdata_attribute_value(
        tag: str, attributes: dict[str, str]
    ) -> str | None:
        attribute = (
            "content" if tag == "meta"
            else "href" if tag in {"a", "area", "link"}
            else "src" if tag in {
                "audio", "embed", "iframe", "img", "source", "track", "video",
            }
            else "data" if tag == "object"
            else "value" if tag in {"data", "meter"}
            else "datetime" if tag == "time"
            else ""
        )
        if not attribute:
            return None
        value = attributes.get(attribute, "").strip()
        return value or None

    def _record_itemprop(
        self,
        itemprop: str,
        value: str,
        path: tuple[tuple[str, dict[str, str]], ...],
    ) -> None:
        if itemprop == "author":
            self.outside_itemprop_authors.append(value)
            self.outside_itemprop_author_paths.append((value, path))
        else:
            self.outside_itemprop_modified.append(value)
            self.outside_itemprop_modified_paths.append((value, path))


class _DocumentPrivacyCollector(HTMLParser):
    """Collect all public response bytes into privacy-auditable value surfaces."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.attributes: list[tuple[str, str]] = []
        self.semantic_chunks: list[str] = []
        self.decoded_literals: list[str] = []
        self.decode_problems: list[str] = []
        self.raw_text_tag = ""

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        folded_tag = tag.casefold()
        self.semantic_chunks.append(folded_tag)
        if folded_tag in PUBLIC_TEXT_BOUNDARY_TAGS:
            self.chunks.append("\n")
            self.semantic_chunks.append("\n")
        if folded_tag in {"script", "style"}:
            self.raw_text_tag = folded_tag
        for name, value in attributes:
            self.attributes.append((name, value or ""))
            normalized_name = re.sub(
                r"^(?:data|aria)[_:-]?", "", name.casefold()
            )
            if normalized_name not in {
                "", "x", "y", "value", "label", "title", "class", "id",
                "name", "role", "property", "content",
            }:
                self.semantic_chunks.append(normalized_name)
            if value:
                self.semantic_chunks.append(value)

    def handle_startendtag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag: str) -> None:
        folded_tag = tag.casefold()
        if folded_tag in PUBLIC_TEXT_BOUNDARY_TAGS:
            self.chunks.append("\n")
            self.semantic_chunks.append("\n")
        if folded_tag == self.raw_text_tag:
            self.raw_text_tag = ""

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)
        if self.raw_text_tag in {"script", "style"}:
            strings, _ = _css_string_literals(data)
            if self.raw_text_tag == "script":
                for item_index, item in enumerate((data, *strings)):
                    decoded, problem = _decode_js_json_escapes(item)
                    self.semantic_chunks.append(decoded)
                    if item_index:
                        self.decoded_literals.append(decoded)
                    if problem is not None:
                        self.decode_problems.append(problem)
            else:
                self.semantic_chunks.extend(strings)
                self.decoded_literals.extend(strings)
        else:
            self.semantic_chunks.append(data)

    def handle_comment(self, data: str) -> None:
        self.chunks.append(data)

    def handle_pi(self, data: str) -> None:
        self.chunks.append(data)

    def handle_decl(self, decl: str) -> None:
        self.chunks.append(decl)

    def unknown_decl(self, data: str) -> None:
        self.chunks.append(data)


def _whole_document_privacy_problems(body: str) -> list[str]:
    collector = _DocumentPrivacyCollector()
    collector.feed(body)
    collector.close()
    surfaces: list[tuple[str, str]] = []
    browser_bytes = re.sub(r"[\t\r\n]+", " ", "".join(collector.chunks))
    surfaces.append(("public document bytes", browser_bytes))
    structural_values = re.sub(
        r"[\t\r\n]+", " ", " ".join(collector.semantic_chunks)
    )
    surfaces.append(("public document structural values", structural_values))
    if collector.decoded_literals:
        surfaces.append(
            ("public document separated decoded literals", " ".join(collector.decoded_literals))
        )
    for name, value in collector.attributes:
        inspected = _decode_css_escapes(value) if name.casefold() == "style" else value
        surfaces.append((f"<{name}> attribute", f"{name}={inspected}"))
    problems: list[str] = []
    seen: set[str] = set()
    for problem in collector.decode_problems:
        detail = f"public script {problem}"
        if detail not in seen:
            seen.add(detail)
            problems.append(detail)
    for label, value in surfaces:
        problem = _public_value_problem(value)
        if problem is None:
            continue
        detail = f"{label} {problem}"
        if detail not in seen:
            seen.add(detail)
            problems.append(detail)
        if len(problems) >= 12:
            break
    return problems


def _is_pending_review_state(value: str) -> bool:
    return PENDING_REVIEW.search(_comparison_text(value)) is not None


def _comparison_text(value: str) -> str:
    """Return a display-preserving value's unobfuscated comparison form."""

    normalized = unicodedata.normalize("NFKC", value)
    visible = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
        and not ("\u180b" <= character <= "\u180d")
        and not ("\ufe00" <= character <= "\ufe0f")
        and not ("\U000e0100" <= character <= "\U000e01ef")
    )
    return " ".join(visible.split())


def _has_ignored_format_character(value: str) -> bool:
    return any(
        unicodedata.category(character) == "Cf"
        or "\u180b" <= character <= "\u180d"
        or "\ufe00" <= character <= "\ufe0f"
        or "\U000e0100" <= character <= "\U000e01ef"
        for character in value
    )


def _unicode_word_tokens(value: str) -> list[str]:
    """Tokenize public names without restricting partner identities to ASCII."""

    tokens: list[str] = []
    current: list[str] = []
    for character in _comparison_text(value).casefold():
        category = unicodedata.category(character)
        if category[0] in {"L", "M", "N"}:
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def _valid_identity(value: str, *, reviewer: bool = False) -> bool:
    stripped = " ".join(value.split())
    comparison = _comparison_text(stripped)
    if re.search(r"%[0-9a-f]{2}", stripped, re.IGNORECASE):
        return False
    if reviewer and HONEST_PENDING_REVIEW.fullmatch(comparison):
        return True
    return (
        len(comparison) >= 2
        and len(value) <= 200
        and not _has_ignored_format_character(stripped)
        and not any(
            unicodedata.category(character).startswith("C") for character in value
        )
        and any(character.isalnum() for character in comparison)
        and not any("://" in item for item in _decoded_values(comparison))
        and comparison.casefold() not in GENERIC_IDENTITIES
        and PLACEHOLDER_IDENTITY.search(comparison) is None
    )


def _looks_like_agent_identity(value: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", _comparison_text(value).casefold())
    if not set(tokens) & KNOWN_AGENT_IDENTITY_TOKENS:
        return False
    non_name_tokens = (
        KNOWN_AGENT_IDENTITY_TOKENS
        | GENERIC_ROLE_TOKENS
        | GENERIC_AGENT_TOKENS
        | {"v", "version"}
    )
    if any(
        token not in non_name_tokens
        and not token.isdigit()
        and re.fullmatch(r"v\d+", token) is None
        for token in tokens
    ):
        # Claude Hopkins and similarly named people remain concrete humans.
        return False
    return True


def _looks_like_generic_role_identity(value: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", _comparison_text(value).casefold())
    return bool(tokens) and all(token in GENERIC_ROLE_TOKENS for token in tokens)


def _valid_human_identity(value: str) -> bool:
    if not _valid_identity(value):
        return False
    if unicodedata.normalize("NFKC", value) != value or " ".join(value.split()) != value:
        return False
    tokens = _unicode_word_tokens(value)
    if not tokens:
        return False
    non_name_tokens = (
        GENERIC_ROLE_TOKENS | KNOWN_AGENT_IDENTITY_TOKENS | GENERIC_AGENT_TOKENS
    )
    versioned_agent = re.compile(
        r"(?:chatgpt|claude|codex|deepseek|gemini|gpt|llama|qwen)\d+"
    )
    name_components = [
        token
        for token in tokens
        if (
            token in AMBIGUOUS_HUMAN_NAME_TOKENS
            or token not in non_name_tokens
        )
        and len(token) >= 1
        and not token.isdigit()
        and re.fullmatch(r"v\d+", token) is None
        and versioned_agent.fullmatch(token) is None
    ]
    unspaced_non_latin_name = (
        len(tokens) == 1
        and len(tokens[0]) >= 2
        and re.search(r"[a-z]", tokens[0]) is None
    )
    return len(name_components) >= 2 or unspaced_non_latin_name


def _valid_agent_identity(value: str) -> bool:
    return (
        _valid_identity(value)
        and PUBLIC_AGENT_IDENTITY.fullmatch(value) is not None
        and value in PUBLIC_DOCUMENTATION_ACTOR_IDS
    )


def _valid_model_identity(value: str) -> bool:
    if value == "UNKNOWN":
        return True
    return _valid_identity(value) and value in PUBLIC_MODEL_IDS


def _valid_stable_id(value: str, minimum: int, maximum: int = 128) -> bool:
    stripped = value.strip()
    comparison = _comparison_text(stripped)
    return (
        value == stripped
        and len(stripped) >= minimum
        and len(stripped) <= maximum
        and not any("://" in item for item in _decoded_values(comparison))
        and PLACEHOLDER_IDENTITY.search(comparison) is None
        and not _has_placeholder_slug_token(comparison)
        and STABLE_ID.fullmatch(stripped) is not None
    )


def _decoded_values(value: str) -> tuple[str, ...]:
    values = [value]
    for _ in range(MAX_PUBLIC_DECODE_ROUNDS):
        decoded = unquote(unescape(values[-1]))
        if decoded == values[-1]:
            break
        values.append(decoded)
    return tuple(values)


def _public_value_problem(value: str) -> str | None:
    return _shared_public_value_problem(value)


def _public_hostname_problem(hostname: str) -> str | None:
    normalized = hostname.rstrip(".").casefold()
    if not normalized or "%" in normalized:
        return "has a malformed or encoded hostname"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        if normalized == "localhost" or normalized.endswith(
            (
                ".localhost",
                ".local",
                ".internal",
                ".intranet",
                ".lan",
                ".home",
                ".corp",
            )
        ):
            return "uses a private/local hostname"
        if "." not in normalized:
            return "uses a dotless non-public hostname"
        if re.fullmatch(r"[0-9.]+", normalized):
            return "uses a malformed or non-public numeric host"
        try:
            ascii_host = normalized.encode("idna").decode("ascii")
        except UnicodeError:
            return "has an invalid IDNA hostname"
        if len(ascii_host) > 253 or any(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) is None
            for label in ascii_host.split(".")
        ):
            return "has a malformed public hostname"
    else:
        if not address.is_global:
            return "uses a private, loopback, link-local, or reserved IP address"
    return None


def _parse_iso_instant(value: str) -> datetime | None:
    if ISO_INSTANT.fullmatch(value) is None:
        return None
    if not value.endswith("Z"):
        offset = re.search(r"([+-])(\d{2}):(\d{2})$", value)
        if offset is None:
            return None
        offset_hour, offset_minute = map(int, offset.group(2, 3))
        if (
            offset_hour > 14
            or offset_minute > 59
            or (offset_hour == 14 and offset_minute != 0)
        ):
            return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _valid_iso_instant(value: str) -> bool:
    return _parse_iso_instant(value) is not None


def _same_contract_instant(candidate: str, expected: str) -> bool:
    candidate_time = _parse_iso_instant(candidate.strip())
    expected_time = _parse_iso_instant(expected.strip())
    return (
        candidate_time is not None
        and expected_time is not None
        and candidate_time == expected_time
    )


def _matches_audit_clock_date(candidate: str, *expected_values: str) -> bool:
    """Bind page-modified metadata to either audited clock's calendar date."""

    candidate_time = _parse_iso_instant(candidate.strip())
    candidate_day = (
        candidate_time.date().isoformat()
        if candidate_time is not None
        else candidate.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate.strip())
        else ""
    )
    return bool(candidate_day) and any(
        (parsed := _parse_iso_instant(expected)) is not None
        and parsed.date().isoformat() == candidate_day
        for expected in expected_values
    )


def _reader_date_labels(parsed: datetime) -> set[str]:
    day = str(parsed.day)
    labels = {
        parsed.strftime("%Y-%m-%d"),
        f"{parsed.strftime('%B')} {day}, {parsed.year}",
        f"{parsed.strftime('%b')} {day}, {parsed.year}",
        f"{parsed.strftime('%B')} {day} {parsed.year}",
        f"{parsed.strftime('%b')} {day} {parsed.year}",
        f"{day} {parsed.strftime('%B')} {parsed.year}",
        f"{day} {parsed.strftime('%b')} {parsed.year}",
        parsed.isoformat(),
    }
    if parsed.utcoffset() == timedelta(0):
        labels.add(parsed.isoformat().removesuffix("+00:00") + "Z")
    return labels


def _visible_truth_conflicts(
    text: str,
    *,
    expected_author: str,
    checked: datetime | None,
    changed: datetime | None,
    rail_scope: bool,
) -> list[str]:
    """Find common reader-facing byline, clock, or state contradictions."""

    conflicts: list[str] = []
    normalized = "\n".join(" ".join(line.split()) for line in text.splitlines())
    author_pattern = re.compile(
        r"(?:^|[.;\n·])\s*(?:human\s+author\s*:|author\s*:?\s+|"
        r"(?:written|posted|authored)\s+by\s+|article\s+by\s+|by\s+|"
        r"meet\s+the\s+author\s*:\s*)"
        r"([^.;\n·]{2,200})",
        re.IGNORECASE,
    )
    expected_folded = _comparison_text(expected_author).casefold()
    for match in author_pattern.finditer(normalized):
        claimed = _comparison_text(match.group(1).strip(" :-–—"))
        if _valid_human_identity(claimed) and claimed.casefold() != expected_folded:
            conflicts.append("a visible author/byline contradicts data-human-author")
            break

    for label_pattern, expected_time, label in (
        (
            r"(?:last\s+)?(?:updated|changed|modified|revised|edited|update)",
            changed,
            "changed",
        ),
        (r"last\s+checked", checked, "checked"),
    ):
        if expected_time is None:
            continue
        expected_labels = {item.casefold() for item in _reader_date_labels(expected_time)}
        prefix = (
            r"\b"
            if rail_scope
            else r"(?:^|[.;\n·])\s*(?:(?:this|the)?\s*"
            r"(?:page|document|article)\s+)?"
        )
        for match in re.finditer(
            rf"{prefix}{label_pattern}\b\s*(?::|[-–—])?\s*([^.;\n]{{1,80}})",
            normalized,
            re.IGNORECASE,
        ):
            claim = match.group(1).casefold()
            if re.search(r"\b(?:19|20)\d{2}\b", claim) is None:
                continue
            if not any(
                re.search(rf"(?<![\w]){re.escape(item)}(?![\w])", claim)
                for item in expected_labels
            ):
                conflicts.append(
                    f"a visible last-{label} claim contradicts the audit clock"
                )
                break

    status_pattern = (
        r"\b(?:verification\s+failed|not\s+verified|never\s+verified|"
        r"review\s+status\s*(?::|[-–—]|is)\s*(?:pending|failed|unreviewed))\b"
        if rail_scope
        else r"(?:^|[.;\n·])\s*(?:verification\s+failed|"
        r"this\s+(?:page|document)\s+(?:is\s+)?(?:not\s+verified|unverified))"
        r"\s*(?=[.;\n·]|$)"
    )
    if re.search(status_pattern, normalized, re.IGNORECASE):
        conflicts.append("visible verification/review prose contradicts the audit state")
    return conflicts


def _https_url_problem(value: str, *, immutable: bool = False) -> str | None:
    if not value:
        return "is blank"
    if "\\" in value:
        return "contains a backslash URL byte"
    if any(re.search(r"[\s\x00-\x1f\x7f]", item) for item in _decoded_values(value)):
        return "contains whitespace or control characters"
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        return f"is malformed ({exc})"
    if parsed.scheme != "https" or not parsed.netloc or not hostname:
        return "must be an absolute HTTPS URL"
    if parsed.username is not None or parsed.password is not None:
        return "must not contain credentials"
    hostname_problem = _public_hostname_problem(hostname)
    if hostname_problem:
        return hostname_problem
    public_value_problem = _public_value_problem(value)
    if public_value_problem:
        return public_value_problem
    normalized_paths = _decoded_values(parsed.path)
    normalized_query = unquote(parsed.query)
    if parsed.hostname and any(
        _credential_route_problem(parsed.hostname, path) for path in normalized_paths
    ):
        return "contains a credential-bearing webhook or bot URL"
    if re.search(
        r"(?:^|[&;])(?:api[_-]?key|authorization|auth|password|passwd|sig|"
        r"session(?:id)?|[A-Za-z0-9_-]*(?:token|secret|credential|signature)|"
        r"private[_-]?key)\s*=",
        normalized_query,
        re.IGNORECASE,
    ):
        return "contains a credential-bearing query parameter"
    if immutable and (parsed.query or parsed.fragment):
        return "must not contain a query or fragment"
    return None


def _rail_public_privacy_problems(
    rail: _ProvenanceRail, *, label: str
) -> list[str]:
    problems: list[str] = []
    safe_tags = {
        "a", "b", "br", "code", "dd", "div", "dl", "dt", "em", "h2",
        "h3", "h4", "h5", "h6", "hr", "i", "li", "ol", "p", "samp",
        "small", "span", "strong", "time", "ul",
    }
    global_attributes = {"class", "id", "role", "style", "title"}
    per_tag_attributes = {
        "a": {"href", "rel", "target"},
        "time": {"datetime"},
    }

    def audit_attribute(
        name: str, value: str, *, tag: str, location: str, is_root: bool
    ) -> None:
        normalized_display_name = _comparison_text(name).casefold()
        normalized_name = re.sub(r"[^a-z0-9]", "", normalized_display_name)
        ordinary_allowed = (
            name in global_attributes
            or name in {"aria-label", "aria-description", "aria-hidden"}
            or name in per_tag_attributes.get(tag, set())
        )
        if (
            normalized_display_name.startswith("on")
            or name == "srcdoc"
            or (
                is_root
                and not ordinary_allowed
                and name not in PROVENANCE_ALLOWED_DATA_ATTRIBUTES
            )
            or (
                not is_root
                and not ordinary_allowed
            )
        ):
            problems.append(f"{label}{location}{name} is not allowed in the audit rail")
        if name in {"aria-labelledby", "aria-describedby"}:
            problems.append(
                f"{label}{location}{name} IDREF naming is not allowed in the audit rail"
            )
        if name == "aria-hidden" and value.strip().casefold() not in {"true", "false"}:
            problems.append(
                f"{label}{location}aria-hidden must be exactly true or false"
            )
        if name == "role" and value.strip().casefold() not in {
            "complementary", "region",
        }:
            problems.append(
                f"{label}{location}role is not compatible with provenance rail semantics"
            )
        if name in {"aria-label", "aria-description", "title"} and re.search(
            r"\b(?:state|verified|verification|human\s+(?:author|reviewer)|"
            r"maintainer|agent|model|capture\s+run|publication\s+receipt|"
            r"discovery\s+url|source\s+revision|checked|changed)\b",
            _comparison_text(value),
            re.IGNORECASE,
        ):
            problems.append(
                f"{label}{location}{name} must not assert a second audit truth"
            )
        if (
            is_root
            and normalized_display_name.startswith("data-")
            and normalized_display_name not in PROVENANCE_ALLOWED_DATA_ATTRIBUTES
        ):
            problems.append(f"{label}{name} is an unapproved root data attribute")
        private_schedule_attribute = (
            "schedule" in normalized_name and "scheduler" not in normalized_name
        )
        if private_schedule_attribute or any(
            fragment in normalized_name
            for fragment in PRIVATE_PROVENANCE_ATTRIBUTE_FRAGMENTS
        ):
            problems.append(
                f"{label}{location}{name} is a forbidden private provenance attribute"
            )
        if not is_root and normalized_display_name.startswith("data-"):
            problems.append(
                f"{label}{location}{name} is an unapproved descendant data attribute"
            )
        if (
            not is_root
            or name not in PROVENANCE_ALLOWED_DATA_ATTRIBUTES
        ):
            public_problem = _public_value_problem(value)
            if public_problem:
                problems.append(f"{label}{location}{name} {public_problem}")
        if not is_root or name not in PROVENANCE_REQUIRED_ATTRIBUTES:
            for url_token in re.findall(
                r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"']+", value
            ):
                if url_problem := _https_url_problem(url_token.rstrip(".,);")):
                    problems.append(
                        f"{label}{location}{name} contains a URL that {url_problem}"
                    )
        if name in {"href", "xlink:href", "src", "action", "formaction"}:
            url_problem = _https_url_problem(value)
            if url_problem:
                problems.append(
                    f"{label}{location}{name} URL {url_problem}"
                )
        if name == "style":
            decoded_style = _decode_css_escapes(_strip_css_comments(value))
            privacy_style = decoded_style
            for target in _css_fetch_targets(decoded_style):
                privacy_style = privacy_style.replace(target, " ")
                if url_problem := _css_fetch_url_problem(target):
                    problems.append(
                        f"{label}{location}style contains a URL that {url_problem}"
                    )
            if decoded_problem := _public_value_problem(privacy_style):
                problems.append(
                    f"{label}{location}style after CSS decoding {decoded_problem}"
                )

    for name, value in rail.attributes.items():
        audit_attribute(name, value, tag=rail.tag, location="", is_root=True)
    for tag, attributes in rail.subtree_attributes:
        if tag not in safe_tags:
            problems.append(f"{label}<{tag}> is not allowed in the audit rail")
        for name, value in attributes.items():
            audit_attribute(
                name,
                value,
                tag=tag,
                location=f"<{tag}> descendant ",
                is_root=False,
            )

    # Inline element boundaries do not insert rendered whitespace. Preserve
    # only block/BR boundaries so split tokens cannot evade the privacy gate.
    public_raw_text = re.sub(r"[\t\r\n]+", " ", "".join(rail.public_raw_text))
    if raw_text_problem := _public_value_problem(public_raw_text):
        problems.append(f"{label}public subtree {raw_text_problem}")
    visible_parts: list[str] = []
    previous_branch: tuple[tuple[str, int], ...] | None = None
    for chunk in rail.visible_text:
        branch = tuple(
            (tag, node_id)
            for (tag, _), (node_id, _) in zip(
                chunk.visibility_path, chunk.dom_path
            )
            if tag in PUBLIC_TEXT_BOUNDARY_TAGS
        )
        if previous_branch is not None and branch != previous_branch:
            visible_parts.append("\n")
        visible_parts.append(chunk.text)
        previous_branch = branch
    browser_text = re.sub(r"[\t\r\n\u2029]+", " ", "".join(visible_parts))
    if visible_problem := _public_value_problem(browser_text):
        problems.append(f"{label}browser-equivalent text {visible_problem}")
    for url_token in re.findall(
        r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"']+", public_raw_text
    ):
        if url_problem := _https_url_problem(url_token.rstrip(".,);")):
            problems.append(
                f"{label}public subtree contains a URL that {url_problem}"
            )
    return problems


def _rail_css_privacy_problems(
    rail: _ProvenanceRail, rules: list[_CssRule], *, label: str
) -> list[str]:
    """Audit generated text and fetch-bearing CSS applied to the rail root."""

    problems: list[str] = []
    paths = [rail.visibility_path, *rail.subtree_visibility_paths]
    generated_values: list[str] = []
    for rule in rules:
        if not any(
            path
            and _selector_matches_element_path(rule.selector, path, len(path) - 1)
            for path in paths
        ):
            continue
        for name, declaration in rule.declarations.items():
            decoded_value = unescape(_decode_css_escapes(declaration.value))
            pseudo = f"::{rule.generated_pseudo}" if rule.generated_pseudo else ""
            if public_problem := _public_value_problem(decoded_value):
                problems.append(
                    f"{label}applicable CSS {rule.selector}{pseudo} {name} "
                    f"{public_problem}"
                )
            if name == "content" and rule.generated_pseudo:
                if decoded_value.strip().casefold() not in {
                    "none", "normal", "initial", "inherit", "unset", "revert",
                    "revert-layer",
                }:
                    problems.append(
                        f"{label}applicable generated CSS content is not allowed on "
                        "the auditable rail"
                    )
                if re.search(
                    r"\b(?:attr|counter|counters|var)\s*\(|"
                    r"\b(?:open-quote|close-quote|no-open-quote|no-close-quote)\b",
                    decoded_value,
                    re.IGNORECASE,
                ):
                    problems.append(
                        f"{label}applicable generated CSS content uses an unsupported "
                        "dynamic value"
                    )
                content_strings, unclosed = _css_string_literals(declaration.value)
                if unclosed:
                    problems.append(
                        f"{label}applicable generated CSS content has an unclosed string"
                    )
                generated_values.append("".join(content_strings))
            for target in _css_fetch_targets(decoded_value):
                if url_problem := _css_fetch_url_problem(target):
                    problems.append(
                        f"{label}applicable CSS {rule.selector}{pseudo} {name} "
                        f"contains a URL that {url_problem}"
                    )
    if generated_values:
        combined_generated = "".join(generated_values)
        if problem := _public_value_problem(combined_generated):
            problems.append(f"{label}combined generated CSS content {problem}")
    return problems


def _document_generated_truth_problems(
    parser: _ProvenanceParser,
    rules: list[_CssRule],
    *,
    expected_author: str,
    checked: datetime | None,
    changed: datetime | None,
) -> list[str]:
    """Reconcile static reader-visible pseudo content outside the audit rail."""

    problems: list[str] = []
    paths = [_browser_document_path(path) for path in parser.outside_element_paths]
    # Fragment inputs still have browser-created html/body nodes even if neither
    # appeared lexically in the supplied source.
    paths.extend([(("html", {}),), (("html", {}), ("body", {}))])
    for rule in rules:
        if not rule.generated_pseudo or "content" not in rule.declarations:
            continue
        if not any(
            _selector_matches_element_path(rule.selector, path, len(path) - 1)
            for path in paths
        ):
            continue
        declaration = rule.declarations["content"]
        decoded = _decode_css_escapes(declaration.value).strip().casefold()
        if decoded in {
            "", "none", "normal", "initial", "inherit", "unset", "revert",
            "revert-layer",
        }:
            continue
        strings, unclosed = _css_string_literals(declaration.value)
        if unclosed:
            problems.append("outside generated CSS truth has an unclosed string")
            continue
        generated_text = "".join(strings)
        problems.extend(
            _visible_truth_conflicts(
                generated_text,
                expected_author=expected_author,
                checked=checked,
                changed=changed,
                rail_scope=False,
            )
        )
    return problems


def _decode_css_escapes(value: str) -> str:
    """Decode CSS escapes before privacy inspection of generated/fetching values."""

    def replace(match: re.Match[str]) -> str:
        hexadecimal = match.group(1)
        if hexadecimal:
            codepoint = int(hexadecimal, 16)
            if codepoint == 0 or codepoint > 0x10FFFF:
                return "\ufffd"
            return chr(codepoint)
        escaped = match.group(2)
        return "" if escaped in {"\n", "\r", "\f"} else escaped

    return re.sub(r"\\(?:([0-9a-fA-F]{1,6})\s?|(.))", replace, value, flags=re.DOTALL)


def provenance_contract_problems(body: str) -> list[str]:
    parser = _ProvenanceParser()
    parser.feed(body)
    parser.close()

    css_rules = _static_css_rules(body)
    css_hidden = [
        rail for rail in parser.rails if _css_hides_path(rail.visibility_path, css_rules)
    ]
    visible_rails = [rail for rail in parser.rails if rail not in css_hidden]
    privacy_problems = (
        _whole_document_privacy_problems(body)
        + _document_css_contract_problems(body)
        + [
        problem
        for index, candidate in enumerate(parser.all_rails, start=1)
        for problem in (
            _rail_public_privacy_problems(
                candidate, label=f"provenance rail {index} "
            )
            + _rail_css_privacy_problems(
                candidate, css_rules, label=f"provenance rail {index} "
            )
        )
        ]
    )

    if len(visible_rails) != 1:
        detail = f"expected exactly one visible rail, found {len(visible_rails)}"
        hidden_count = parser.hidden_rail_count + len(css_hidden)
        if hidden_count:
            detail += f" ({hidden_count} hidden rail(s) do not count)"
        if privacy_problems:
            detail += "; " + "; ".join(privacy_problems)
        return [detail]

    rail = visible_rails[0]
    problems: list[str] = privacy_problems
    if len(parser.all_rails) != 1:
        problems.append(
            f"expected exactly one provenance element in the DOM, found {len(parser.all_rails)}"
        )
    if parser.outside_audit_attributes:
        problems.append(
            "audit-like data attributes appear outside the provenance rail: "
            + ", ".join(parser.outside_audit_attributes)
        )
    if not rail.closed:
        problems.append("the provenance rail is not closed")
    if rail.subtree_duplicate_attributes:
        problems.append(
            "the rail subtree repeats attribute(s), which is browser-ambiguous: "
            + ", ".join(rail.subtree_duplicate_attributes)
        )

    missing = [
        name
        for name in PROVENANCE_REQUIRED_ATTRIBUTES
        if not rail.attributes.get(name, "").strip()
    ]
    if missing:
        problems.append("missing same-element attribute(s): " + ", ".join(missing))

    verification_scope = rail.attributes.get("data-verification-scope", "").strip()
    if verification_scope and verification_scope not in PROVENANCE_SCOPES:
        problems.append(
            "data-verification-scope must be one of "
            + ", ".join(repr(value) for value in sorted(PROVENANCE_SCOPES))
            + f", found {verification_scope!r}"
        )
    if verification_scope == "external-exact-raw-wp-body-and-inclusive-marker-slice":
        start_count = body.count(FLEET_MARKER_START)
        end_count = body.count(FLEET_MARKER_END)
        if start_count != 1 or end_count != 1:
            problems.append(
                "marker-bounded scope requires exactly one "
                f"{FLEET_MARKER_START!r} and one {FLEET_MARKER_END!r}; "
                f"found {start_count} start and {end_count} end"
            )
        elif body.index(FLEET_MARKER_START) >= body.index(FLEET_MARKER_END):
            problems.append("the fleet byte-boundary markers are reversed")
        elif not rail.inside_fleet_markers:
            problems.append(
                "the provenance rail must be between the fleet byte-boundary markers"
            )
        else:
            bounded = body.split(FLEET_MARKER_START, 1)[1].split(
                FLEET_MARKER_END, 1
            )[0]
            bounded_parser = _ProvenanceParser()
            bounded_parser.feed(bounded)
            bounded_parser.close()
            lexical_matches = [
                candidate
                for candidate in bounded_parser.rails
                if candidate.tag == rail.tag
                and candidate.attributes == rail.attributes
                and candidate.duplicate_attributes == rail.duplicate_attributes
                and candidate.closed
            ]
            if len(lexical_matches) != 1:
                problems.append(
                    "the visible provenance rail is not wholly inside the marker-bounded bytes"
                )

    provenance_state = rail.attributes.get("data-document-provenance", "").strip()
    if provenance_state and provenance_state not in PROVENANCE_STATES:
        problems.append(
            "data-document-provenance must be pending-external-verification or "
            f"receipt-linked, found {provenance_state!r}"
        )

    identities = (
        ("data-human-author", False),
        ("data-maintainer", False),
        ("data-maintainer-agent", False),
        ("data-human-reviewer", True),
    )
    for name, reviewer in identities:
        value = rail.attributes.get(name, "")
        public_value_problem = _public_value_problem(value)
        if value and public_value_problem:
            problems.append(f"{name} {public_value_problem}")
        if value and not _valid_identity(value, reviewer=reviewer):
            problems.append(f"{name} is blank or a placeholder identity/state")
        elif (
            value
            and name in {"data-human-author", "data-human-reviewer"}
            and not _is_pending_review_state(value)
            and not _valid_human_identity(value)
        ):
            problems.append(
                f"{name} must name a concrete human with a public name, not a role/team alias"
            )
        if (
            value
            and name in {
                "data-human-author",
                "data-human-reviewer",
                "data-maintainer-agent",
            }
            and not _is_pending_review_state(value)
            and _looks_like_generic_role_identity(value)
        ):
            problems.append(f"{name} must name a concrete identity, not a role or team")

    agent_value = rail.attributes.get("data-maintainer-agent", "")
    if agent_value and not _valid_agent_identity(agent_value):
        problems.append(
            "data-maintainer-agent must name a concrete public agent identity"
        )

    model_value = " ".join(rail.attributes.get("data-maintainer-model", "").split())
    model_comparison = model_value
    model_public_problem = _public_value_problem(model_value)
    if model_value and model_public_problem:
        problems.append(f"data-maintainer-model {model_public_problem}")
    if model_value and not _valid_model_identity(model_value):
        problems.append("data-maintainer-model is blank or a placeholder")
    if verification_scope == "external-exact-raw-wp-body-and-inclusive-marker-slice":
        if agent_value and agent_value not in PUBLIC_ACTOR_IDS:
            problems.append(
                "the fleet maintaining agent is not in fleet-public-actors-v1"
            )
        if (
            model_value
            and model_value != "UNKNOWN"
            and model_comparison not in PUBLIC_MODEL_IDS
        ):
            problems.append("the fleet model is not in fleet-public-models-v1")
        if (
            reviewer_value := " ".join(
                rail.attributes.get("data-human-reviewer", "").split()
            )
        ) and not _is_pending_review_state(reviewer_value) and (
            reviewer_value not in PUBLIC_HUMAN_REVIEWERS
        ):
            problems.append(
                "the fleet human reviewer is not in fleet-public-human-reviewers-v1"
            )

    reviewer_value = " ".join(rail.attributes.get("data-human-reviewer", "").split())
    if provenance_state == "receipt-linked" and (
        _is_pending_review_state(reviewer_value)
        or not _valid_identity(reviewer_value, reviewer=False)
    ):
        problems.append(
            "receipt-linked requires the actual human reviewer; use "
            "pending-external-verification while review is pending"
        )

    if "data-capture-result" in rail.attributes:
        problems.append(
            "data-capture-result is ambiguous; use data-scheduler-capture-result and "
            "data-publication-verification-result"
        )
    scheduler_capture_result = rail.attributes.get(
        "data-scheduler-capture-result", ""
    ).strip()
    if scheduler_capture_result and scheduler_capture_result not in {"success", "failure"}:
        problems.append("data-scheduler-capture-result must be 'success' or 'failure'")
    publication_verification_result = rail.attributes.get(
        "data-publication-verification-result", ""
    ).strip()
    if (
        publication_verification_result
        and publication_verification_result not in PUBLICATION_VERIFICATION_RESULTS
    ):
        problems.append(
            "data-publication-verification-result must be 'pending', 'success', or 'failure'"
        )
    if (
        provenance_state == "pending-external-verification"
        and publication_verification_result
        and publication_verification_result != "pending"
    ):
        problems.append(
            "pending-external-verification requires "
            "data-publication-verification-result='pending'"
        )
    if (
        provenance_state == "receipt-linked"
        and publication_verification_result
        and publication_verification_result not in {"success", "failure"}
    ):
        problems.append(
            "receipt-linked requires a publication verification result of success or failure"
        )

    for name in ("data-capture-run-id", "data-publication-receipt-id"):
        value = rail.attributes.get(name, "")
        public_value_problem = _public_value_problem(value)
        if value and public_value_problem:
            problems.append(f"{name} {public_value_problem}")
        if value and not _valid_stable_id(value, 4):
            problems.append(f"{name} is not a stable, non-placeholder identifier")
    receipt_index = rail.attributes.get("data-publication-receipt-index", "")
    receipt_index_problem = _https_url_problem(receipt_index, immutable=True)
    if receipt_index and receipt_index_problem:
        problems.append(f"data-publication-receipt-index {receipt_index_problem}")
    receipt_url = rail.attributes.get("data-publication-receipt-discovery-url", "")
    receipt_url_problem = _https_url_problem(receipt_url, immutable=True)
    if receipt_url and receipt_url_problem:
        problems.append(
            f"data-publication-receipt-discovery-url {receipt_url_problem}"
        )
    receipt_id = rail.attributes.get("data-publication-receipt-id", "")
    if receipt_url and not receipt_url_problem and receipt_id:
        receipt_filename = unquote(urlparse(receipt_url).path.rsplit("/", 1)[-1])
        if receipt_filename != f"{receipt_id}.json":
            problems.append(
                "data-publication-receipt-discovery-url filename must equal "
                "data-publication-receipt-id + '.json'"
            )

    source_url = rail.attributes.get("data-source-url", "")
    source_url_problem = _https_url_problem(source_url)
    if source_url and source_url_problem:
        problems.append(f"data-source-url {source_url_problem}")
    source_contract_url = rail.attributes.get("data-source-contract-url", "")
    source_contract_url_problem = _https_url_problem(
        source_contract_url, immutable=True
    )
    if source_contract_url and source_contract_url_problem:
        problems.append(
            f"data-source-contract-url {source_contract_url_problem}"
        )
    source_revision = rail.attributes.get("data-source-revision", "")
    source_revision_public_problem = _public_value_problem(source_revision)
    if source_revision and source_revision_public_problem:
        problems.append(f"data-source-revision {source_revision_public_problem}")
    if source_revision and not _valid_stable_id(source_revision, 6):
        problems.append("data-source-revision is not a stable, non-placeholder identifier")

    if verification_scope == "external-exact-raw-wp-body-and-inclusive-marker-slice":
        if not source_contract_url:
            problems.append(
                "the fleet rail requires data-source-contract-url on the rail itself"
            )
        elif source_contract_url != FLEET_RECEIPT_CONTRACT:
            problems.append(
                "the fleet source contract URL must name the public receipt contract"
            )
        if receipt_index and receipt_index != FLEET_RECEIPT_INDEX:
            problems.append(
                "the fleet receipt index must use the public local-service-spotlight-skills ledger"
            )
        expected_discovery = FLEET_RECEIPT_DISCOVERY_PREFIX + receipt_id + ".json"
        if receipt_url and receipt_url != expected_discovery:
            problems.append(
                "the fleet receipt discovery URL must use the deterministic public ledger path"
            )
        if source_revision and re.fullmatch(r"[0-9a-f]{40}", source_revision) is None:
            problems.append(
                "the fleet source revision must be a full lowercase 40-hex commit"
            )
        expected_source = FLEET_SOURCE_MANIFEST_PREFIX + source_revision + ".json"
        if source_url and source_url != expected_source:
            problems.append(
                "the fleet source URL must use its deterministic public sanitized manifest"
            )
        if receipt_id and re.fullmatch(r"fleet-page-[0-9a-f]{20}", receipt_id) is None:
            problems.append(
                "the fleet publication receipt ID must be fleet-page- plus 20 lowercase hex"
            )

    checked = rail.attributes.get("data-last-checked", "").strip()
    changed = rail.attributes.get("data-last-changed", "").strip()
    for name, value in (
        ("data-last-checked", checked),
        ("data-last-changed", changed),
    ):
        if value and not _valid_iso_instant(value):
            problems.append(f"{name} is not a valid timezone-qualified ISO instant")
    parsed_checked = _parse_iso_instant(checked)
    parsed_changed = _parse_iso_instant(changed)
    if parsed_checked and parsed_changed and parsed_changed > parsed_checked:
        problems.append("data-last-changed cannot be later than data-last-checked")
    if (
        parsed_checked
        and parsed_checked
        > datetime.now(timezone.utc) + EVIDENCE_CLOCK_FUTURE_TOLERANCE
    ):
        problems.append("data-last-checked cannot be in the future")

    expected_author = rail.attributes.get("data-human-author", "").strip()
    asserted_authors = [*parser.outside_meta_authors]
    asserted_authors.extend(
        value
        for value, path in parser.outside_itemprop_author_paths
        if not _css_hides_path(path, css_rules)
    )
    for meta_author in asserted_authors:
        if _comparison_text(meta_author).casefold() != _comparison_text(
            expected_author
        ).casefold():
            problems.append("document meta author contradicts data-human-author")
    for modified in parser.outside_modified_times:
        if not _matches_audit_clock_date(modified, checked, changed):
            problems.append(
                "document modified-time metadata contradicts data-last-changed"
            )
    for modified, path in parser.outside_updated_time_paths:
        if _css_hides_path(path, css_rules):
            continue
        if not _matches_audit_clock_date(modified, checked, changed):
            problems.append("an outside updated <time> contradicts data-last-changed")
    for itemprop_modified, path in parser.outside_itemprop_modified_paths:
        if _css_hides_path(path, css_rules):
            continue
        if not _matches_audit_clock_date(itemprop_modified, checked, changed):
            problems.append(
                "document itemprop dateModified contradicts data-last-changed"
            )
    outside_text = "".join(parser.outside_root_visible_text) + "".join(
        chunk.text
        for chunk in parser.outside_visible_nodes
        if not _css_hides_path(chunk.visibility_path, css_rules)
    )
    problems.extend(
        _visible_truth_conflicts(
            outside_text,
            expected_author=expected_author,
            checked=parsed_checked,
            changed=parsed_changed,
            rail_scope=False,
        )
    )
    problems.extend(
        _visible_truth_conflicts(
            "".join(parser.outside_title_text),
            expected_author=expected_author,
            checked=parsed_checked,
            changed=parsed_changed,
            rail_scope=False,
        )
    )
    problems.extend(
        _document_generated_truth_problems(
            parser,
            css_rules,
            expected_author=expected_author,
            checked=parsed_checked,
            changed=parsed_changed,
        )
    )
    problems.extend(
        _jsonld_article_truth_problems(
            body,
            expected_author=expected_author,
            expected_changed=changed,
            expected_checked=checked,
        )
    )

    usable_times: list[tuple[str, str, str]] = []
    for semantic_time in rail.times:
        time_is_visible = not _css_hides_path(
            semantic_time.visibility_path, css_rules
        )
        if "datetime" in semantic_time.duplicate_attributes:
            problems.append("a semantic time repeats its datetime attribute")
            continue
        visible_time_text = " ".join(
            "".join(
                chunk.text
                for chunk in semantic_time.text
                if not _css_hides_path(chunk.visibility_path, css_rules)
            ).split()
        )
        if time_is_visible and not semantic_time.datetime:
            problems.append("every visible semantic <time> must have datetime")
            continue
        if time_is_visible and semantic_time.datetime and not _valid_iso_instant(
            semantic_time.datetime
        ):
            problems.append(
                "every visible semantic <time> datetime must be a real ISO instant"
            )
            continue
        if time_is_visible and not visible_time_text:
            problems.append("every visible semantic <time> must expose readable text")
            continue
        if (
            semantic_time.datetime
            and visible_time_text
            and time_is_visible
        ):
            def child_branch_index(chunk: _VisibleText) -> int | None:
                for index, (node_id, _) in enumerate(chunk.dom_path):
                    if node_id != semantic_time.parent_node_id:
                        continue
                    if index + 1 < len(chunk.dom_path):
                        return chunk.dom_path[index + 1][1]
                    return chunk.sibling_index
                return None

            def adjacent_text(
                chunks: Iterable[_VisibleText], expected_index: int, *, tail: bool
            ) -> str:
                for chunk in chunks:
                    if (
                        not chunk.text.strip()
                        or _css_hides_path(chunk.visibility_path, css_rules)
                        or child_branch_index(chunk) != expected_index
                        or any(tag == "time" for tag, _ in chunk.visibility_path)
                    ):
                        continue
                    return chunk.text[-120:] if tail else chunk.text[:120]
                return ""

            leading_text = adjacent_text(
                reversed(semantic_time.leading_text),
                semantic_time.sibling_index - 1,
                tail=True,
            )
            trailing_text = adjacent_text(
                rail.visible_text,
                semantic_time.sibling_index + 1,
                tail=False,
            )
            inside_label = " ".join(visible_time_text.split())
            leading_label = " ".join(
                (leading_text + " " + visible_time_text).split()
            )
            trailing_label = " ".join(
                (visible_time_text + " " + trailing_text).split()
            )
            # An inside label is unambiguous. For an adjacent label, prefer the
            # side that names the role belonging to this datetime. This keeps a
            # compact ``Changed <time>...</time> Checked <time>...</time>``
            # sequence from assigning the next clock's label to the first time.
            if re.search(r"\b(?:checked|changed)\b", inside_label, re.IGNORECASE):
                semantic_label = inside_label
            else:
                expected_roles: set[str] = set()
                if semantic_time.datetime == checked:
                    expected_roles.add("checked")
                if semantic_time.datetime == changed:
                    expected_roles.add("changed")

                def adjacent_roles(label: str) -> set[str]:
                    return {
                        role
                        for role in ("checked", "changed")
                        if re.search(rf"\b{role}\b", label, re.IGNORECASE)
                    }

                leading_roles = adjacent_roles(leading_label) & expected_roles
                trailing_roles = adjacent_roles(trailing_label) & expected_roles
                if len(leading_roles) == 1:
                    # Ordinary prose binds a role immediately before its
                    # semantic time.  This remains unambiguous when checked
                    # and changed happen at the same instant, even if the
                    # separator after the first time introduces the second
                    # role (``Checked <time>...</time>; changed <time>``).
                    semantic_label = leading_label
                elif trailing_roles and not leading_roles:
                    semantic_label = trailing_label
                elif leading_roles and trailing_roles:
                    # When the clocks are equal, accepting either side would let
                    # one ambiguous time satisfy both roles. Preserve both
                    # contexts so the exact-one-role checks below fail closed.
                    semantic_label = leading_label + " " + trailing_label
                elif re.search(
                    r"\b(?:checked|changed)\b", trailing_label, re.IGNORECASE
                ):
                    semantic_label = trailing_label
                else:
                    semantic_label = leading_label
            usable_times.append(
                (semantic_time.datetime, visible_time_text, semantic_label)
            )
    if parsed_checked and parsed_changed:
        expected_times = Counter((checked, changed))
        observed_times = Counter(value for value, _, _ in usable_times)
        absent = expected_times - observed_times
        extra = observed_times - expected_times
        if absent or extra:
            details = [
                *(f"missing {value} ×{count}" for value, count in absent.items()),
                *(f"unexpected {value} ×{count}" for value, count in extra.items()),
            ]
            problems.append(
                "visible semantic <time> values must be exactly the checked and "
                "changed clocks: " + ", ".join(details)
            )

        def label_exposes_clock(
            value: str, text: str, clock_name: str, parsed: datetime
        ) -> bool:
            date_labels = _reader_date_labels(parsed)
            folded = text.casefold()
            clock_match = re.search(rf"\b{re.escape(clock_name)}\b", folded)
            if clock_match is None:
                return False
            leading = folded[max(0, clock_match.start() - 24) : clock_match.start()]
            if re.search(r"(?:\b(?:not|never|no)\s+|un)$", leading):
                return False
            if re.search(
                rf"\b{re.escape(clock_name)}\b\s*(?:\?\s*(?:no|false)\b|"
                r"(?:is|was)\s+(?:not|false)\b)",
                folded,
            ):
                return False
            for date_label in date_labels:
                date_match = re.search(
                    rf"(?<![\w]){re.escape(date_label.casefold())}(?![\w])",
                    folded,
                )
                if date_match is None:
                    continue
                between_start = min(clock_match.end(), date_match.end())
                between_end = max(clock_match.start(), date_match.start())
                between = folded[between_start:between_end]
                if re.search(r"\b(?:not|never|no)\b", between):
                    continue
                return True
            return False

        assigned_roles: list[tuple[str, bool, bool]] = []
        for value, _, label in usable_times:
            is_checked = value == checked and label_exposes_clock(
                checked, label, "checked", parsed_checked
            )
            is_changed = value == changed and label_exposes_clock(
                changed, label, "changed", parsed_changed
            )
            assigned_roles.append((label, is_checked, is_changed))
        if sum(is_checked for _, is_checked, _ in assigned_roles) != 1:
            problems.append(
                "exactly one checked <time> must visibly name the checked clock and its date"
            )
        if sum(is_changed for _, _, is_changed in assigned_roles) != 1:
            problems.append(
                "exactly one changed <time> must visibly name the changed clock and its date"
            )
        if any(is_checked and is_changed for _, is_checked, is_changed in assigned_roles):
            problems.append(
                "one semantic <time> cannot claim both the checked and changed roles"
            )

    block_tags = {
        "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt",
        "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
        "h5", "h6", "header", "li", "main", "nav", "ol", "p", "pre",
        "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
    }

    def visible_branch_key(chunk: _VisibleText) -> tuple[str, int]:
        for (tag, _), (node_id, _) in reversed(
            list(zip(chunk.visibility_path, chunk.dom_path))
        ):
            if tag in block_tags:
                return tag, node_id
        return "rail", chunk.dom_path[0][0] if chunk.dom_path else -1

    visible_segments: list[str] = []
    segment_key: tuple[str, int] | None = None
    segment_parts: list[str] = []
    for chunk in rail.visible_text:
        if chunk.text == "\u2029":
            if segment_parts:
                visible_segments.append(" ".join("".join(segment_parts).split()))
                segment_parts = []
                segment_key = None
            continue
        if _css_hides_path(chunk.visibility_path, css_rules) or not chunk.text.strip():
            continue
        key = visible_branch_key(chunk)
        if segment_key is not None and key != segment_key:
            visible_segments.append(" ".join("".join(segment_parts).split()))
            segment_parts = []
        segment_key = key
        segment_parts.append(chunk.text)
    if segment_parts:
        visible_segments.append(" ".join("".join(segment_parts).split()))
    visible_segments_folded = [
        unicodedata.normalize("NFKC", segment)
        .replace("∶", ":")
        .replace("꞉", ":")
        .replace("ː", ":")
        .replace("︰", ":")
        .replace("ꓽ", ":")
        .replace("։", ":")
        .casefold()
        for segment in visible_segments
    ]
    problems.extend(
        _visible_truth_conflicts(
            "\n".join(visible_segments),
            expected_author=expected_author,
            checked=parsed_checked,
            changed=parsed_changed,
            rail_scope=True,
        )
    )
    visibility_values = {
        "data-verification-scope": verification_scope,
        "data-human-author": rail.attributes.get("data-human-author", ""),
        "data-maintainer": rail.attributes.get("data-maintainer", ""),
        "data-maintainer-agent": rail.attributes.get("data-maintainer-agent", ""),
        "data-maintainer-model": rail.attributes.get("data-maintainer-model", ""),
        "data-human-reviewer": rail.attributes.get("data-human-reviewer", ""),
        "data-capture-run-id": rail.attributes.get("data-capture-run-id", ""),
        "data-scheduler-capture-result": scheduler_capture_result,
        "data-publication-verification-result": publication_verification_result,
        "data-publication-receipt-id": receipt_id,
        "data-publication-receipt-discovery-url": receipt_url,
        "data-source-revision": source_revision,
    }
    labeled_visibility = {
        "data-verification-scope": r"\bverification\s+scope\b",
        "data-human-author": r"\bhuman(?:\s+owner\s+and)?\s+author\b",
        "data-maintainer": r"\b(?:maintainer|maintained\s+by)\b",
        "data-maintainer-agent": r"\b(?:maintainer\s+)?agent\b",
        "data-maintainer-model": r"\b(?:maintainer\s+)?model\b",
        "data-human-reviewer": r"\bhuman\s+reviewer\b",
        "data-capture-run-id": r"\bcapture\s+run\b",
        "data-scheduler-capture-result": r"\bscheduler\s+capture\s+result\b",
        "data-publication-verification-result": (
            r"\bpublication\s+verification\s+result\b"
        ),
        "data-publication-receipt-id": (
            r"\b(?:publication\s+receipt(?:\s+(?:id|identifier))?"
            r"|receipt\s+(?:id|identifier))\b"
        ),
        "data-publication-receipt-discovery-url": (
            r"\b(?:receipt\s+)?(?:mutable\s+)?discovery(?:\s+url)?\b"
        ),
        "data-source-revision": r"\b(?:source\s+revision|for\s+revision)\b",
    }
    def explicit_assignment_surfaces(label_pattern: str) -> list[str]:
        surfaces = list(visible_segments_folded)
        label_only = re.compile(
            rf"^\s*{label_pattern}\s*(?::|[-–—]|is)?\s*$", re.IGNORECASE
        )
        for index, segment in enumerate(visible_segments_folded[:-1]):
            if label_only.fullmatch(segment):
                surfaces.append(segment.rstrip(":-–— ") + ": " + visible_segments_folded[index + 1])
        return surfaces

    def assignment_status(label_pattern: str, expected: str) -> tuple[bool, bool, int]:
        expected = " ".join(expected.split()).casefold()
        surfaces = explicit_assignment_surfaces(label_pattern)
        clause_start = r"(?:^|[.;])\s*"
        exact = re.compile(
            clause_start
            + label_pattern
            + r"\s*(?:(?::|[-–—])\s+|is\s+)"
            + re.escape(expected)
            + r"(?=\s*(?:[.;]|$))",
            re.IGNORECASE,
        )
        explicit = re.compile(
            clause_start
            + label_pattern
            + r"\s*(?:(?::|[-–—])\s+|is\s+)",
            re.IGNORECASE,
        )
        unlabeled_separator = re.compile(
            clause_start
            + label_pattern
            + r"\s+(?!is\b)(?P<loose_value>[^.;]+)(?=\s*(?:[.;]|$))",
            re.IGNORECASE,
        )
        exact_count = sum(len(list(exact.finditer(surface))) for surface in surfaces)
        # A same-segment `Label value` clause is ambiguous prose, not a
        # machine/auditor-readable assignment.  Keep `<dt>/<dd>` support via
        # the synthesized colon surface above, but fail closed on loose prose
        # so it cannot add a second contradictory truth.
        contradictory = False
        for surface in surfaces:
            explicit_matches = list(explicit.finditer(surface))
            for loose_match in unlabeled_separator.finditer(surface):
                loose_value = loose_match.group("loose_value").strip()
                # Resolve a longer, explicitly delimited compound label before
                # treating its shorter prefix as an unpunctuated assignment.
                # For example, ``Model availability note: ...`` is a label in
                # its own right, not a second ``Model: ...`` field.  Requiring
                # whitespace after the later delimiter keeps value-internal
                # separators such as ``wp:110278:113449`` in scope.
                if re.match(
                    r"^[^:;]+?(?::|[-–—])\s+\S", loose_value
                ):
                    continue
                # Several labels have optional suffixes (for example
                # `Publication receipt ID`).  A prefix-only loose match may
                # begin at the same byte as the complete, delimited label;
                # the latter is canonical and must win.
                label_only_surface = re.fullmatch(
                    rf"\s*{label_pattern}\s*(?::|[-–—]|is)?\s*",
                    surface,
                    re.IGNORECASE,
                )
                if label_only_surface is None and not any(
                    match.start() == loose_match.start()
                    for match in explicit_matches
                ):
                    contradictory = True
            for match in explicit_matches:
                remainder = surface[match.end() :].lstrip()
                if not remainder:
                    continue
                if not re.match(
                    re.escape(expected) + r"(?=\s*(?:[.;]|$))",
                    remainder,
                    re.IGNORECASE,
                ):
                    contradictory = True
        return exact_count > 0, contradictory, exact_count

    for name, label_pattern in labeled_visibility.items():
        value = visibility_values[name]
        if not value:
            continue
        exposed, contradictory, count = assignment_status(label_pattern, value)
        if not exposed:
            problems.append(f"{name} is not exposed with its visible rail label")
        elif contradictory or count != 1:
            problems.append(f"{name} has conflicting or duplicate visible rail labels")

    normalized_segments = [
        re.sub(r"[-_]+", " ", segment) for segment in visible_segments_folded
    ]
    normalized_state = re.sub(r"[-_]+", " ", provenance_state.casefold())
    if provenance_state:
        original_segments = visible_segments_folded
        visible_segments_folded = normalized_segments
        exposed, contradictory, count = assignment_status(r"\bstate\b", normalized_state)
        visible_segments_folded = original_segments
        if not exposed:
            problems.append("the provenance state is not exposed with its visible rail label")
        elif contradictory or count != 1:
            problems.append("the provenance state has conflicting or duplicate visible labels")

    visible_links = {
        link.href
        for link in rail.links
        if link.href
        and not _css_hides_path(link.visibility_path, css_rules)
        and "".join(
            chunk.text
            for chunk in link.text
            if not _css_hides_path(chunk.visibility_path, css_rules)
        ).strip()
    }
    for name, value in (
        ("data-source-url", source_url),
        ("data-publication-receipt-index", receipt_index),
    ):
        if value and value not in visible_links:
            problems.append(f"{name} has no matching visible link in the rail")
    receipt_discovery_links = [
        link
        for link in rail.links
        if link.href == receipt_url
        and not _css_hides_path(link.visibility_path, css_rules)
        and "".join(
            chunk.text
            for chunk in link.text
            if not _css_hides_path(chunk.visibility_path, css_rules)
        ).strip()
    ]
    if provenance_state == "receipt-linked" and len(receipt_discovery_links) != 1:
        problems.append(
            "receipt-linked requires exactly one visible link to the publication receipt"
        )
    if provenance_state == "pending-external-verification" and receipt_discovery_links:
        problems.append(
            "pending-external-verification must expose the expected receipt as text, "
            "not an unresolved link"
        )
    if verification_scope == "external-exact-raw-wp-body-and-inclusive-marker-slice":
        def contract_link_is_named(link: _VisibleLink) -> bool:
            inner = " ".join(
                "".join(
                    chunk.text
                    for chunk in link.text
                    if not _css_hides_path(chunk.visibility_path, css_rules)
                ).split()
            )
            leading = ""
            for chunk in reversed(link.leading_text):
                if not chunk.text.strip() or _css_hides_path(
                    chunk.visibility_path, css_rules
                ):
                    continue
                leading = chunk.text[-120:]
                break
            return inner.casefold() == "public verification rules" or re.search(
                r"\breceipt[-\s]+contract\b",
                " ".join((leading, inner)).casefold(),
            ) is not None

        contract_links = [
            link
            for link in rail.links
            if link.href == source_contract_url == FLEET_RECEIPT_CONTRACT
            and not _css_hides_path(link.visibility_path, css_rules)
            and contract_link_is_named(link)
        ]
        if len(contract_links) != 1:
            problems.append(
                "the fleet rail must expose one separately named public receipt contract link"
            )

    return problems


# ----------------------------------------------------------------------------
# fetching


def fetch(url: str, timeout: int = PAGE_TIMEOUT) -> tuple[int, str]:
    return _fetch_public_page(url, timeout)


@dataclass(frozen=True)
class _ResolvedLinkTarget:
    scheme: str
    hostname: str
    port: int
    request_target: str
    addresses: tuple[str, ...]


def _public_link_url_problem(url: str) -> str | None:
    """Reject unsafe public link bytes before DNS, filtering, or sampling."""

    if re.search(r"[\s\x00-\x1f\x7f]", url) or "\\" in url:
        return "contains whitespace, control, or backslash URL bytes"
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        return f"malformed URL ({exc})"
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        return "only absolute HTTP(S) links may be resolved"
    if parsed.username is not None or parsed.password is not None:
        return "credential-bearing links are not public resolver targets"
    if hostname_problem := _public_hostname_problem(hostname):
        return hostname_problem
    normalized_paths = _decoded_values(parsed.path)
    normalized_query = unquote(parsed.query)
    if any(_credential_route_problem(hostname, path) for path in normalized_paths):
        return "contains a credential-bearing webhook or bot URL"
    if re.search(
        r"(?:^|[&;])(?:api[_-]?key|authorization|auth|password|passwd|sig|"
        r"session(?:id)?|[A-Za-z0-9_-]*(?:token|secret|credential|signature)|"
        r"private[_-]?key)\s*=",
        normalized_query,
        re.IGNORECASE,
    ):
        return "contains a credential-bearing query parameter"
    for component_name, component in (
        ("path", parsed.path),
        ("query", parsed.query),
        ("fragment", parsed.fragment),
    ):
        if not component:
            continue
        problem = _public_value_problem(component)
        if component_name == "path" and problem and "machine path" in problem:
            decoded_path = "\n".join(_decoded_values(component))
            if not re.search(r"(?:file:|(?:^|/)\.\.?/)", decoded_path, re.IGNORECASE):
                # `/home/`, `/library/`, `/media/`, etc. are ordinary public
                # website routes. Filesystem-root rules apply only to free text,
                # not the path component of an already approved public URL.
                problem = None
        if problem:
            return f"URL {component_name} {problem}"
    return None


def _credential_route_problem(hostname: str, path: str) -> bool:
    """Recognize public-service URL paths whose path bytes are credentials."""

    host = hostname.rstrip(".").casefold()
    folded_path = path.casefold()
    return bool(
        (host == "hooks.slack.com" and folded_path.startswith("/services/"))
        or (
            host in {"discord.com", "discordapp.com"}
            and folded_path.startswith("/api/webhooks/")
        )
        or (
            host == "api.telegram.org"
            and re.match(r"/bot[^/]+/", path, re.IGNORECASE)
        )
    )


def _resolve_public_link_target(
    url: str,
) -> tuple[_ResolvedLinkTarget | None, str | None]:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        return None, f"malformed URL ({exc})"
    if public_problem := _public_link_url_problem(url):
        return None, "unsafe public URL: " + public_problem
    resolved_port = port or (443 if parsed.scheme == "https" else 80)
    try:
        answers = socket.getaddrinfo(
            hostname,
            resolved_port,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        return None, f"DNS resolution failed ({exc})"
    addresses = {answer[4][0].split("%", 1)[0] for answer in answers if answer[4]}
    if not addresses:
        return None, "DNS returned no addresses"
    for address_text in sorted(addresses):
        try:
            address = ipaddress.ip_address(address_text)
        except ValueError:
            return None, f"DNS returned malformed address {address_text!r}"
        if not address.is_global:
            return None, f"DNS resolved to non-public address {address_text}"
    request_target = parsed.path or "/"
    if parsed.params:
        request_target += ";" + parsed.params
    if parsed.query:
        request_target += "?" + parsed.query
    return (
        _ResolvedLinkTarget(
            parsed.scheme,
            hostname,
            resolved_port,
            request_target,
            tuple(sorted(addresses)),
        ),
        None,
    )


def _network_target_problem(url: str) -> str | None:
    """Compatibility helper for tests/callers that only need a safety verdict."""
    _, problem = _resolve_public_link_target(url)
    return problem


def _pinned_connection(
    target: _ResolvedLinkTarget, address: str, timeout: float
) -> http.client.HTTPConnection:
    """Connect to the already-approved IP while preserving Host/SNI semantics."""
    if target.scheme == "https":
        connection: http.client.HTTPConnection = http.client.HTTPSConnection(
            target.hostname, target.port, timeout=timeout
        )
    else:
        connection = http.client.HTTPConnection(
            target.hostname, target.port, timeout=timeout
        )

    def create_connection(
        _address: tuple[str, int],
        connect_timeout: float | object = socket._GLOBAL_DEFAULT_TIMEOUT,
        source_address: tuple[str, int] | None = None,
    ):
        return socket.create_connection(
            (address, target.port), connect_timeout, source_address
        )

    # HTTPConnection.connect calls this hook. For HTTPS, the connection still keeps
    # target.hostname as its host, so TLS SNI and certificate validation use the public
    # name while the TCP socket cannot perform a second, attacker-controlled DNS lookup.
    connection._create_connection = create_connection  # type: ignore[attr-defined]
    return connection


def _single_link_response(
    target: _ResolvedLinkTarget, method: str, timeout: float
) -> tuple[int, str | None]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    for address in target.addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        connection = _pinned_connection(target, address, remaining)
        try:
            connection.request(
                method,
                target.request_target,
                headers={"User-Agent": UA, "Accept": "*/*"},
            )
            response = connection.getresponse()
            if method == "GET":
                response.read(LINK_STATUS_BODY_BYTES)
            return response.status, response.getheader("Location")
        except Exception as exc:  # one approved address may be temporarily unreachable
            last_error = exc
        finally:
            connection.close()
    if last_error is not None:
        raise urllib.error.URLError(last_error)
    raise urllib.error.URLError("link-check deadline exceeded")


def _single_page_response(
    target: _ResolvedLinkTarget, timeout: float
) -> tuple[int, str | None, str, bytes]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    for address in target.addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        connection = _pinned_connection(target, address, remaining)
        try:
            connection.request(
                "GET",
                target.request_target,
                headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.1"},
            )
            response = connection.getresponse()
            raw = response.read(MAX_PAGE_BODY_BYTES + 1)
            if len(raw) > MAX_PAGE_BODY_BYTES:
                raise ValueError(
                    f"page response exceeds {MAX_PAGE_BODY_BYTES} byte audit limit"
                )
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.getheader("Location"), charset, raw
        except Exception as exc:  # one approved address may be temporarily unreachable
            last_error = exc
        finally:
            connection.close()
    if last_error is not None:
        if isinstance(last_error, ValueError):
            raise last_error
        raise urllib.error.URLError(last_error)
    raise urllib.error.URLError("page-fetch deadline exceeded")


def _fetch_public_page(url: str, timeout: int) -> tuple[int, str]:
    deadline = time.monotonic() + timeout
    current = url
    for redirect_count in range(MAX_LINK_REDIRECTS + 1):
        target, problem = _resolve_public_link_target(current)
        if problem or target is None:
            raise ValueError(problem or "page target did not resolve safely")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("page-fetch deadline exceeded")
        status, location, charset, raw = _single_page_response(target, remaining)
        if status not in {301, 302, 303, 307, 308}:
            return status, raw.decode(charset, errors="replace")
        if not location:
            raise ValueError("page redirect has no Location header")
        if redirect_count == MAX_LINK_REDIRECTS:
            raise ValueError(f"page has more than {MAX_LINK_REDIRECTS} redirects")
        current = urljoin(current, location)
    raise ValueError("unreachable page-fetch state")


def _status_with_method(url: str, method: str, deadline: float) -> tuple[int, str]:
    current = url
    for redirect_count in range(MAX_LINK_REDIRECTS + 1):
        target, target_problem = _resolve_public_link_target(current)
        if target_problem:
            return 0, target_problem
        if target is None:  # defensive: the resolver always returns target xor problem
            return 0, "link target did not resolve"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 0, "link-check deadline exceeded"
        try:
            status, location = _single_link_response(target, method, remaining)
        except urllib.error.URLError as exc:
            return 0, str(exc.reason)
        except Exception as exc:  # noqa: BLE001 - one link must not abort the sweep
            return 0, exc.__class__.__name__
        if status not in {301, 302, 303, 307, 308}:
            return status, ""
        if not location:
            return 0, "redirect has no Location header"
        if redirect_count == MAX_LINK_REDIRECTS:
            return 0, f"more than {MAX_LINK_REDIRECTS} redirects"
        current = urljoin(current, location)
    return 0, "unreachable"


def status_of(url: str) -> tuple[int, str]:
    """Return (status, note). Status 0 means the request never completed."""
    deadline = time.monotonic() + LINK_TIMEOUT
    # GET is visitor-equivalent and authoritative. HEAD 200 is frequently a CDN
    # shortcut even when the corresponding GET is dead.
    return _status_with_method(url, "GET", deadline)


# ----------------------------------------------------------------------------
# running one check


def _snippet(text: str, start: int, end: int) -> str:
    fragment = text[max(0, start - 20) : min(len(text), end + 20)]
    return re.sub(r"\s+", " ", fragment).strip()[:SNIPPET]


def _exempted(text: str, start: int, end: int, marker: str) -> bool:
    window = text[max(0, start - EXEMPT_WINDOW) : end + EXEMPT_WINDOW]
    return marker in window


def normalise_json_slashes(text: str) -> str:
    """JSON-LD is often emitted with escaped slashes (``https:\\/\\/``)."""
    return text.replace("\\/", "/")


def run_regex_check(check: Check, url: str, body: str, severity: str) -> list[Finding]:
    findings: list[Finding] = []

    if check.kind == "require_regex":
        if check.pattern.search(body) is None:
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, "not found")
            )
        return findings

    hits = 0
    for match in check.pattern.finditer(body):
        if check.exempt_if_near and _exempted(
            body, match.start(), match.end(), check.exempt_if_near
        ):
            continue
        hits += 1
        if hits <= 5:
            findings.append(
                Finding(
                    url,
                    check.slug,
                    check.id,
                    severity,
                    check.message,
                    _snippet(body, match.start(), match.end()),
                )
            )
    if hits > 5:
        findings.append(
            Finding(
                url,
                check.slug,
                check.id,
                severity,
                check.message,
                f"...and {hits - 5} more occurrence(s)",
            )
        )
    return findings


def run_provenance_contract(
    check: Check,
    url: str,
    body: str,
    severity: str,
    *,
    now: datetime | None = None,
    enforce_freshness: bool = True,
    freshness_policy: str | None = None,
) -> list[Finding]:
    problems = provenance_contract_problems(body)
    target = urlparse(url)
    is_fleet_target = (
        target.hostname in {"blitzmetrics.com", "www.blitzmetrics.com"}
        and target.path.rstrip("/") == "/scheduled-jobs-fleet"
    )
    parser = _ProvenanceParser()
    parser.feed(body)
    parser.close()
    maximum_age: timedelta | None = None
    if is_fleet_target:
        maximum_age = FLEET_LIVE_MAX_CHECK_AGE
    elif freshness_policy == "current-live-30d":
        maximum_age = GENERIC_PUBLIC_MAX_CHECK_AGE
    if enforce_freshness and maximum_age is not None and len(parser.all_rails) == 1:
        checked = _parse_iso_instant(
            parser.all_rails[0].attributes.get("data-last-checked", "")
        )
        current_time = now or datetime.now(timezone.utc)
        if checked is not None and current_time - checked > maximum_age:
            if is_fleet_target:
                problems.append(
                    "the live scheduled-jobs fleet last-checked clock is older than "
                    "its 36-hour daily-refresh SLA"
                )
            else:
                problems.append(
                    "the current-live target's last-checked clock is older than "
                    "its explicit 30-day verification SLA"
                )
    if not problems:
        return []
    return [
        Finding(
            url,
            check.slug,
            check.id,
            severity,
            check.message,
            "; ".join(problems),
        )
    ]


class _OutboundAnchorCollector(HTMLParser):
    """Collect actual navigable outbound anchors, never HTML-looking text."""

    INERT = (INERT_CONTAINERS - {"head", "plaintext"}) | {"noembed", "noframes"}

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.effective_base_url = base_url
        self.base_seen = False
        self.base_invalid = False
        self.inert_stack: list[str] = []
        self.head_depth = 0
        self.plaintext_started = False
        self.urls: list[str] = []
        self.seen: set[str] = set()
        self.problems: list[str] = []
        self.document_ids: set[str] = set()
        self.same_document_fragments: list[str] = []
        self.raw_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        folded = tag.casefold()
        if self.plaintext_started:
            return
        active = not self.inert_stack
        if active:
            element_id = next(
                (value for name, value in attrs if name.casefold() == "id"), None
            )
            if element_id:
                self.document_ids.add(unescape(element_id))
            if folded == "a":
                legacy_name = next(
                    (value for name, value in attrs if name.casefold() == "name"),
                    None,
                )
                if legacy_name:
                    self.document_ids.add(unescape(legacy_name))
        if folded == "base" and not self.base_seen and not self.inert_stack:
            href = next(
                (value for name, value in attrs if name.casefold() == "href"), None
            )
            if href is not None:
                self.base_seen = True
                raw_base = unescape(href).strip()
                if "\\" in raw_base:
                    self.problems.append("base href contains browser-ambiguous backslashes")
                    self.base_invalid = True
                else:
                    candidate = urljoin(self.base_url, raw_base)
                    if problem := _public_link_url_problem(candidate):
                        self.problems.append("unsafe document base URL: " + problem)
                        self.base_invalid = True
                    else:
                        self.effective_base_url = candidate
        if not self.inert_stack and folded in {"a", "area"} and self.head_depth:
            self.problems.append("anchor markup appears in the HTML head")
        elif not self.inert_stack and folded in {"a", "area"}:
            # HTML uses the first repeated attribute. Preserve browser semantics;
            # provenance rails separately reject duplicate attributes outright.
            href = next(
                (value for name, value in attrs if name.casefold() == "href"), None
            )
            if href is None and folded == "a":
                href = next(
                    (
                        value
                        for name, value in attrs
                        if name.casefold() == "xlink:href"
                    ),
                    None,
                )
            if href is not None:
                raw = unescape(href).strip()
                if "\\" in raw:
                    self.problems.append(
                        "anchor href contains browser-ambiguous backslashes"
                    )
                    raw = ""
                if raw:
                    self.raw_links.append(raw)
        if folded == "head" and not self.inert_stack:
            self.head_depth += 1
        elif folded == "plaintext":
            self.plaintext_started = True
        elif folded in self.INERT:
            self.inert_stack.append(folded)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # In text/html the slash is ignored for non-void elements. Treat it as
        # a normal start so <template/>, <head/>, and <a/> match browser state.
        self.handle_starttag(tag, attrs)
        if tag.casefold() in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.plaintext_started:
            return
        folded = tag.casefold()
        if folded == "head" and self.head_depth:
            self.head_depth -= 1
        elif self.inert_stack and self.inert_stack[-1] == folded:
            self.inert_stack.pop()

    def close(self) -> None:
        super().close()
        if not self.base_invalid:
            for raw in self.raw_links:
                parsed = urlparse(raw)
                if parsed.scheme.casefold() in {"http", "https"}:
                    target = raw
                elif not parsed.scheme:
                    target = urljoin(self.effective_base_url, raw)
                elif parsed.scheme.casefold() in {"mailto", "tel"}:
                    continue
                else:
                    self.problems.append(
                        "anchor href uses an unsafe or unsupported URL scheme"
                    )
                    continue
                target_parts = urlparse(target)
                base_parts = urlparse(self.base_url)
                same_document = (
                    target_parts.fragment
                    and target_parts._replace(fragment="")
                    == base_parts._replace(fragment="")
                )
                if same_document:
                    self.same_document_fragments.append(
                        unquote(target_parts.fragment)
                    )
                elif target not in self.seen:
                    self.seen.add(target)
                    self.urls.append(target)
        for fragment in self.same_document_fragments:
            if fragment not in self.document_ids:
                self.problems.append(
                    "same-document fragment does not match any id or legacy anchor name"
                )


class _JsonLdSameAsCollector(HTMLParser):
    """Parse only real JSON-LD script elements and collect sameAs values."""

    INERT = (INERT_CONTAINERS - {"head", "plaintext", "script"}) | {
        "noembed",
        "noframes",
    }

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.script_data: list[str] | None = None
        self.urls: list[str] = []
        self.seen: set[str] = set()
        self.problems: list[str] = []
        self.inert_stack: list[str] = []
        self.plaintext_started = False
        self.document_ids: set[str] = set()
        self.jsonld_node_ids: set[str] = set()
        self.same_document_fragments: list[str] = []
        self.documents: list[object] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        folded = tag.casefold()
        if self.plaintext_started:
            return
        if folded == "plaintext":
            self.plaintext_started = True
            return
        if folded in self.INERT:
            self.inert_stack.append(folded)
            return
        if self.inert_stack:
            return
        attributes: dict[str, str] = {}
        for name, value in attrs:
            attributes.setdefault(name.casefold(), value or "")
        if attributes.get("id"):
            self.document_ids.add(unescape(attributes["id"]))
        if folded == "a" and attributes.get("name"):
            self.document_ids.add(unescape(attributes["name"]))
        if folded != "script" or self.script_data is not None:
            return
        media_type = attributes.get("type", "").split(";", 1)[0].strip().casefold()
        if media_type == "application/ld+json":
            if "src" in attributes:
                self.problems.append(
                    "JSON-LD script must not combine an external src with inline data"
                )
                return
            self.script_data = []

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # A slash does not self-close script in text/html.
        self.handle_starttag(tag, attrs)
        if tag.casefold() in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.script_data is not None:
            self.script_data.append(data)

    def handle_endtag(self, tag: str) -> None:
        folded = tag.casefold()
        if self.plaintext_started:
            return
        if self.inert_stack:
            if self.inert_stack[-1] == folded:
                self.inert_stack.pop()
            return
        if folded != "script" or self.script_data is None:
            return
        raw = "".join(self.script_data).strip()
        self.script_data = None
        if raw.startswith("<!--") and raw.endswith("-->"):
            raw = raw[4:-3].strip()
        def reject_duplicates(
            pairs: list[tuple[str, object]],
        ) -> dict[str, object]:
            value: dict[str, object] = {}
            for key, child in pairs:
                if key in value:
                    raise ValueError("duplicate JSON member")
                value[key] = child
            return value

        try:
            document = json.loads(
                raw,
                object_pairs_hook=reject_duplicates,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-JSON numeric constant {value!r}")
                ),
            )
        except (json.JSONDecodeError, RecursionError, ValueError):
            self.problems.append("JSON-LD is malformed or has duplicate members")
            return
        self.documents.append(document)
        self._collect_node_ids(document)
        self._walk(document)

    def close(self) -> None:
        super().close()
        if self.script_data is not None:
            self.script_data = None
            self.problems.append("JSON-LD script is unclosed or malformed")
        for fragment in self.same_document_fragments:
            if fragment not in self.document_ids and fragment not in self.jsonld_node_ids:
                self.problems.append(
                    "JSON-LD same-document fragment does not match any document or JSON-LD id"
                )

    def _collect_node_ids(self, value: object) -> None:
        if isinstance(value, dict):
            node_id = value.get("@id")
            defining_members = set(value) - {"@id", "@context"}
            if isinstance(node_id, str) and defining_members:
                target = urljoin(self.base_url, node_id.strip())
                parsed = urlparse(target)
                if (
                    parsed.fragment
                    and parsed._replace(fragment="")
                    == urlparse(self.base_url)._replace(fragment="")
                ):
                    self.jsonld_node_ids.add(unquote(parsed.fragment))
            for key, child in value.items():
                if key != "@context":
                    self._collect_node_ids(child)
        elif isinstance(value, list):
            for child in value:
                self._collect_node_ids(child)

    def _append(self, value: object) -> None:
        if isinstance(value, list):
            for child in value:
                self._append(child)
            return
        if isinstance(value, dict):
            if set(value) == {"@id"}:
                self._append(value["@id"])
            else:
                self.problems.append("JSON-LD sameAs object must contain only @id")
            return
        if not isinstance(value, str):
            self.problems.append("JSON-LD sameAs must be an IRI, @id object, or list")
            return
        raw = value.strip()
        parsed = urlparse(raw)
        if raw.startswith("//"):
            target = urljoin(self.base_url, raw)
        elif parsed.scheme.casefold() in {"http", "https"}:
            target = raw
        elif not parsed.scheme and raw and "\\" not in raw:
            target = urljoin(self.base_url, raw)
        else:
            self.problems.append("JSON-LD sameAs contains a non-HTTP IRI")
            return
        target_parts = urlparse(target)
        if (
            target_parts.fragment
            and target_parts._replace(fragment="")
            == urlparse(self.base_url)._replace(fragment="")
        ):
            self.same_document_fragments.append(unquote(target_parts.fragment))
            return
        if target not in self.seen:
            self.seen.add(target)
            self.urls.append(target)

    @staticmethod
    def _context_terms(
        context: object, aliases: set[str], prefixes: dict[str, str]
    ) -> tuple[set[str], dict[str, str]]:
        aliases = set(aliases)
        prefixes = dict(prefixes)
        contexts = context if isinstance(context, list) else [context]
        canonical = {"https://schema.org/sameAs", "http://schema.org/sameAs"}
        vocab: str | None = None
        definitions: list[tuple[str, str]] = []
        for item in contexts:
            if isinstance(item, str):
                # The supported schema.org remote context preserves the
                # ordinary sameAs term. Other remote contexts are rejected by
                # _context_problem before this helper runs.
                continue
            if not isinstance(item, dict):
                continue
            for term, definition in item.items():
                if term == "@vocab" and isinstance(definition, str):
                    vocab = definition
                    continue
                if definition is None:
                    aliases.discard(term)
                    continue
                target = (
                    definition.get("@id")
                    if isinstance(definition, dict)
                    else definition
                )
                if not isinstance(target, str):
                    continue
                if target.endswith(("/", "#")):
                    prefixes[term] = target
                definitions.append((term, target))
        if vocab is not None and vocab.rstrip("/#") not in {
            "https://schema.org",
            "http://schema.org",
        }:
            aliases.discard("sameAs")
        for term, target in definitions:
            expanded = target
            if ":" in target and not target.startswith(("http://", "https://")):
                prefix, suffix = target.split(":", 1)
                if prefix in prefixes:
                    expanded = prefixes[prefix] + suffix
            elif ":" not in target and vocab:
                expanded = vocab + target
            if expanded in canonical:
                aliases.add(term)
            elif term == "sameAs":
                aliases.discard("sameAs")
        return aliases, prefixes

    @staticmethod
    def _context_problem(context: object) -> str | None:
        supported_remote = {
            "https://schema.org",
            "https://schema.org/",
            "http://schema.org",
            "http://schema.org/",
        }
        contexts = context if isinstance(context, list) else [context]
        for item in contexts:
            if item is None:
                return "JSON-LD null @context is unsupported by the link audit"
            if isinstance(item, str):
                if item not in supported_remote:
                    return "JSON-LD uses an unsupported remote @context"
                continue
            if not isinstance(item, dict):
                return "JSON-LD @context has an unsupported shape"
            if "@base" in item:
                return "JSON-LD @base is unsupported by the link audit"
            for definition in item.values():
                if isinstance(definition, dict) and "@context" in definition:
                    return "JSON-LD scoped @context is unsupported by the link audit"
        return None

    def _walk(
        self,
        value: object,
        aliases: set[str] | None = None,
        prefixes: dict[str, str] | None = None,
    ) -> None:
        aliases = set({"sameAs"} if aliases is None else aliases)
        prefixes = dict({} if prefixes is None else prefixes)
        if isinstance(value, dict):
            if "@context" in value:
                if problem := self._context_problem(value["@context"]):
                    self.problems.append(problem)
                    return
                aliases, prefixes = self._context_terms(
                    value["@context"], aliases, prefixes
                )
            for key, child in value.items():
                if key == "@context":
                    continue
                expanded = key
                if ":" in key and not key.startswith(("http://", "https://")):
                    prefix, suffix = key.split(":", 1)
                    if prefix in prefixes:
                        expanded = prefixes[prefix] + suffix
                if key in aliases or expanded in {
                    "https://schema.org/sameAs",
                    "http://schema.org/sameAs",
                }:
                    self._append(child)
                self._walk(child, aliases, prefixes)
        elif isinstance(value, list):
            for child in value:
                self._walk(child, aliases, prefixes)


def _jsonld_article_truth_problems(
    body: str,
    *,
    expected_author: str,
    expected_changed: str,
    expected_checked: str,
) -> list[str]:
    """Reconcile Article byline/dateModified claims with the sole audit rail."""

    collector = _JsonLdSameAsCollector("https://audit-document.invalid/")
    collector.feed(body)
    collector.close()
    problems: list[str] = []
    article_count = 0
    node_index: dict[str, dict[str, object]] = {}

    def index_nodes(value: object) -> None:
        if isinstance(value, dict):
            node_id = value.get("@id")
            if isinstance(node_id, str) and any(key != "@id" for key in value):
                node_index[node_id] = value
            for key, child in value.items():
                if key != "@context":
                    index_nodes(child)
        elif isinstance(value, list):
            for child in value:
                index_nodes(child)

    for document in collector.documents:
        index_nodes(document)

    def expand_term(
        value: str, terms: dict[str, str], prefixes: dict[str, str], vocab: str
    ) -> str:
        if value in terms:
            return terms[value]
        if value.startswith(("https://", "http://")):
            return value
        if ":" in value:
            prefix, suffix = value.split(":", 1)
            if prefix in prefixes:
                return prefixes[prefix] + suffix
        return vocab + value if vocab else value

    def context_state(
        context: object,
        inherited_terms: dict[str, str],
        inherited_prefixes: dict[str, str],
        inherited_vocab: str,
    ) -> tuple[dict[str, str], dict[str, str], str]:
        terms = dict(inherited_terms)
        prefixes = dict(inherited_prefixes)
        vocab = inherited_vocab
        contexts = context if isinstance(context, list) else [context]
        for item in contexts:
            if item is None:
                terms, prefixes, vocab = {}, {}, ""
            elif isinstance(item, str) and item.rstrip("/") in {
                "https://schema.org", "http://schema.org",
            }:
                vocab = item.rstrip("/") + "/"
            elif isinstance(item, dict):
                if item.get("@vocab") is None and "@vocab" in item:
                    vocab = ""
                elif isinstance(item.get("@vocab"), str):
                    vocab = str(item["@vocab"])
                for term, definition in item.items():
                    if not term.startswith("@") and definition is None:
                        terms[term] = ""
                        prefixes.pop(term, None)
                        continue
                    target = (
                        definition.get("@id")
                        if isinstance(definition, dict)
                        else definition
                    )
                    if (
                        not term.startswith("@")
                        and isinstance(target, str)
                        and target.endswith(("/", "#"))
                    ):
                        prefixes[term] = target
                for term, definition in item.items():
                    target = (
                        definition.get("@id")
                        if isinstance(definition, dict)
                        else definition
                    )
                    if not term.startswith("@") and isinstance(target, str):
                        terms[term] = expand_term(target, terms, prefixes, vocab)
        return terms, prefixes, vocab

    def local_schema_name(expanded: str) -> str:
        if expanded.startswith(("https://schema.org/", "http://schema.org/")):
            return expanded.rstrip("/").rsplit("/", 1)[-1]
        return ""

    def article_type(
        value: object,
        terms: dict[str, str],
        prefixes: dict[str, str],
        vocab: str,
    ) -> bool:
        values = value if isinstance(value, list) else [value]
        return any(
            isinstance(item, str)
            and local_schema_name(
                expand_term(item, terms, prefixes, vocab)
            ).casefold().endswith("article")
            for item in values
        )

    def author_names(
        value: object,
        terms: dict[str, str],
        prefixes: dict[str, str],
        vocab: str,
        seen: set[str] | None = None,
    ) -> list[str]:
        seen = set() if seen is None else seen
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [
                name
                for item in value
                for name in author_names(item, terms, prefixes, vocab, seen)
            ]
        if isinstance(value, dict):
            local_terms, local_prefixes, local_vocab = terms, prefixes, vocab
            if "@context" in value:
                local_terms, local_prefixes, local_vocab = context_state(
                    value["@context"], terms, prefixes, vocab
                )
            names: list[str] = []
            for key, child in value.items():
                if key.startswith("@"):
                    continue
                if local_schema_name(
                    expand_term(key, local_terms, local_prefixes, local_vocab)
                ) == "name":
                    if isinstance(child, str):
                        names.append(child)
                    elif isinstance(child, list):
                        names.extend(item for item in child if isinstance(item, str))
            if names:
                return names
            reference = value.get("@id")
            if (
                isinstance(reference, str)
                and reference not in seen
                and reference in node_index
            ):
                seen.add(reference)
                return author_names(
                    node_index[reference],
                    local_terms,
                    local_prefixes,
                    local_vocab,
                    seen,
                )
        return []

    def walk(
        value: object,
        terms: dict[str, str] | None = None,
        prefixes: dict[str, str] | None = None,
        vocab: str = "",
    ) -> None:
        nonlocal article_count
        terms = {} if terms is None else terms
        prefixes = {} if prefixes is None else prefixes
        if isinstance(value, dict):
            if "@context" in value:
                terms, prefixes, vocab = context_state(
                    value["@context"], terms, prefixes, vocab
                )
            type_values: list[object] = []
            for key, child in value.items():
                if key == "@type" or expand_term(key, terms, prefixes, vocab) == "@type":
                    type_values.append(child)
            if any(article_type(item, terms, prefixes, vocab) for item in type_values):
                article_count += 1
                canonical: dict[str, list[object]] = {
                    "author": [], "dateModified": []
                }
                for key, child in value.items():
                    if key.startswith("@"):
                        continue
                    local = local_schema_name(
                        expand_term(key, terms, prefixes, vocab)
                    )
                    if local in {"author", "dateModified"}:
                        canonical[local].append(child)
                expected = _comparison_text(expected_author).casefold()
                for author_claim in canonical["author"]:
                    authors = author_names(
                        author_claim, terms, prefixes, vocab
                    )
                    if not authors:
                        problems.append(
                            "JSON-LD Article author has an unsupported or blank value"
                        )
                    for author in authors:
                        if _comparison_text(author).casefold() != expected:
                            problems.append(
                                "JSON-LD Article author contradicts data-human-author"
                            )
                for modified_claim in canonical["dateModified"]:
                    modified_values = (
                        modified_claim
                        if isinstance(modified_claim, list)
                        else [modified_claim]
                    )
                    for modified in modified_values:
                        if not isinstance(modified, str):
                            problems.append(
                                "JSON-LD Article dateModified must be an ISO instant"
                            )
                        elif not _matches_audit_clock_date(
                            modified, expected_checked, expected_changed
                        ):
                            problems.append(
                                "JSON-LD Article dateModified contradicts data-last-changed"
                            )
            for key, child in value.items():
                if key != "@context":
                    walk(child, terms, prefixes, vocab)
        elif isinstance(value, list):
            for child in value:
                walk(child, terms, prefixes, vocab)

    for document in collector.documents:
        walk(document)
    if article_count > 1:
        problems.append("document exposes more than one JSON-LD Article owner")
    return problems


def _extract_urls_with_problems(
    check: Check, body: str, base_url: str = "https://self-test.invalid/"
) -> tuple[list[str], list[str]]:
    if check.extractor == "html-anchors":
        parser = _OutboundAnchorCollector(base_url)
        parser.feed(body)
        parser.close()
        return parser.urls, parser.problems
    if check.extractor == "jsonld-sameas":
        parser = _JsonLdSameAsCollector(base_url)
        parser.feed(body)
        parser.close()
        return parser.urls, parser.problems

    if check.pattern is None:
        return [], []
    regions = (
        [m.group(0) for m in check.within.finditer(body)] if check.within else [body]
    )
    found: list[str] = []
    seen: set[str] = set()
    for region in regions:
        for raw in check.pattern.findall(normalise_json_slashes(region)):
            target = unescape(raw).strip().rstrip(".,)")
            if target not in seen:
                seen.add(target)
                found.append(target)
    return found, []


def extract_urls(
    check: Check, body: str, base_url: str = "https://self-test.invalid/"
) -> list[str]:
    return _extract_urls_with_problems(check, body, base_url)[0]


def _required_provenance_resolution_urls(body: str) -> list[str]:
    """Return provenance proof links that must bypass generic link sampling."""

    parser = _ProvenanceParser()
    parser.feed(body)
    parser.close()
    if len(parser.rails) != 1:
        return []
    attributes = parser.rails[0].attributes
    names = [
        "data-source-url",
        "data-source-contract-url",
        "data-publication-receipt-index",
    ]
    if attributes.get("data-document-provenance") == "receipt-linked":
        names.append("data-publication-receipt-discovery-url")
    result: list[str] = []
    for name in names:
        value = attributes.get(name, "")
        try:
            parsed = urlparse(value)
        except ValueError:
            continue
        if parsed.scheme in {"http", "https"} and parsed.netloc and value not in result:
            result.append(value)
    return result


def run_resolve_check(
    check: Check, url: str, body: str, severity: str, pause: float = LINK_PAUSE
) -> list[Finding]:
    host = urlparse(url).netloc.lower()
    findings: list[Finding] = []
    targets, extraction_problems = _extract_urls_with_problems(check, body, url)
    for problem in extraction_problems:
        findings.append(
            Finding(url, check.slug, check.id, severity, check.message, problem)
        )
    required = (
        _required_provenance_resolution_urls(body)
        if check.id == "outbound-links-resolve"
        else []
    )
    targets = required + [target for target in targets if target not in required]
    safe_targets: list[str] = []
    for target in targets:
        if public_problem := _public_link_url_problem(target):
            findings.append(
                Finding(
                    url,
                    check.slug,
                    check.id,
                    severity,
                    check.message,
                    "unsafe public URL omitted: " + public_problem,
                )
            )
        else:
            safe_targets.append(target)
    targets = safe_targets
    if check.skip_same_host:
        targets = [
            target
            for target in targets
            if target in required or urlparse(target).netloc.lower() != host
        ]

    ordinary = [target for target in targets if target not in required]
    if len(ordinary) > check.limit:
        findings.append(
            Finding(
                url,
                check.slug,
                check.id,
                severity,
                check.message,
                "audit incomplete: "
                f"{len(ordinary)} ordinary targets exceed the declared safe maximum "
                f"of {check.limit}; required provenance targets were still checked",
            )
        )
        # Do not silently sample. A blocking incomplete verdict is truthful and
        # prevents an attacker-controlled page from holding CI for hours.
        ordinary = []
    selected = required + ordinary
    audit_deadline = time.monotonic() + MAX_RESOLVE_AUDIT_SECONDS

    def social_bot_block_is_expected(target: str, code: int) -> bool:
        hostname = (urlparse(target).hostname or "").rstrip(".").casefold()
        social_hosts = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com")
        social = any(hostname == host or hostname.endswith("." + host) for host in social_hosts)
        if not social:
            return False
        if code in {401, 403, 405, 429}:
            return True
        return code == 999 and (hostname == "linkedin.com" or hostname.endswith(".linkedin.com"))

    for target in selected:
        if time.monotonic() >= audit_deadline:
            findings.append(
                Finding(
                    url,
                    check.slug,
                    check.id,
                    severity,
                    check.message,
                    "audit incomplete: total link-resolution time budget expired",
                )
            )
            break
        code, note = status_of(target)
        if code not in check.allow_status and not social_bot_block_is_expected(target, code):
            if not code and (note or "").startswith("unsafe public URL"):
                detail = f"{note} — target omitted"
            else:
                detail = (
                    f"HTTP {code} — {target}"
                    if code
                    else f"{note or 'no response'} — {target}"
                )
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, detail)
            )
        time.sleep(pause)
    return findings


def build_paths(check: Check, url: str) -> list[str]:
    """Absolute URLs for this check's paths, on the target's own origin."""
    parts = urlparse(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    return [origin + path for path in check.paths]


def run_paths_check(
    check: Check, url: str, severity: str, pause: float = LINK_PAUSE
) -> list[Finding]:
    """A URL nobody links to is a URL nothing else can check.

    Everything else in this sweep reads the page it fetched. Only this check can
    catch the address printed on a conference QR code going dead, because that
    address has no inbound link, no analytics until someone tries it, and no
    crawler path to find it.
    """
    findings: list[Finding] = []
    for target in build_paths(check, url):
        code, note = status_of(target)
        if code not in check.allow_status:
            detail = f"HTTP {code} — {target}" if code else f"{note or 'no response'} — {target}"
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, detail)
            )
        time.sleep(pause)
    return findings


def run_check(check: Check, url: str, body: str, severity: str, **kw) -> list[Finding]:
    if check.kind == "provenance_contract":
        return run_provenance_contract(
            check,
            url,
            body,
            severity,
            now=kw.get("provenance_now"),
            enforce_freshness=kw.get("enforce_provenance_freshness", True),
            freshness_policy=kw.get("provenance_freshness_policy"),
        )
    kw.pop("provenance_now", None)
    kw.pop("enforce_provenance_freshness", None)
    kw.pop("provenance_freshness_policy", None)
    if check.kind == "resolve_urls":
        return run_resolve_check(check, url, body, severity, **kw)
    if check.kind == "require_paths":
        return run_paths_check(check, url, severity, **kw)
    return run_regex_check(check, url, body, severity)


# ----------------------------------------------------------------------------
# self-test: every rule proves its own patterns


def self_test(standards: list[Standard]) -> list[str]:
    """Each check must flag its violating samples and pass its clean ones."""
    problems: list[str] = []
    for standard in standards:
        for check in standard.checks:
            if check.kind == "require_paths":
                for i, sample in enumerate(check.examples["builds"]):
                    got = build_paths(check, sample["target"])
                    want = sample["urls"]
                    if got != want:
                        problems.append(
                            f"{check.ref} builds[{i}]: expected {want}, got {got}"
                        )
                continue

            if check.kind == "resolve_urls":
                for i, sample in enumerate(check.examples["extracts"]):
                    got = extract_urls(check, sample["html"])
                    want = sample["urls"]
                    if got != want:
                        problems.append(
                            f"{check.ref} extracts[{i}]: expected {want}, got {got}"
                        )
                continue

            if check.kind == "provenance_contract":
                for sample in check.examples["violating"]:
                    if not run_provenance_contract(
                        check,
                        "self-test",
                        sample,
                        standard.severity,
                        enforce_freshness=False,
                    ):
                        problems.append(
                            f"{check.ref}: structural check did NOT flag a violating "
                            f"sample — {sample[:90]!r}"
                        )
                for sample in check.examples["clean"]:
                    hits = run_provenance_contract(
                        check,
                        "self-test",
                        sample,
                        standard.severity,
                        enforce_freshness=False,
                    )
                    if hits:
                        problems.append(
                            f"{check.ref}: structural check falsely flagged a clean "
                            f"sample — {sample[:90]!r}: {hits[0].detail}"
                        )
                continue

            for sample in check.examples["violating"]:
                if not run_regex_check(check, "self-test", sample, standard.severity):
                    problems.append(
                        f"{check.ref}: pattern did NOT flag a violating sample — "
                        f"{sample[:90]!r}. A check that matches nothing reports every "
                        f"site clean forever."
                    )
            for sample in check.examples["clean"]:
                hits = run_regex_check(check, "self-test", sample, standard.severity)
                if hits:
                    problems.append(
                        f"{check.ref}: pattern falsely flagged a clean sample — "
                        f"{sample[:90]!r}"
                    )
    return problems


# ----------------------------------------------------------------------------
# reporting


Target = tuple[str, tuple[str, ...]]


def applies_to_target(standard: Standard, tags: tuple[str, ...]) -> bool:
    """A rule with target_tags only runs on pages carrying one of them."""
    if not standard.target_tags:
        return True
    return bool(set(standard.target_tags) & set(tags))


def sweep(
    targets: list[Target], standards: list[Standard]
) -> tuple[list[Finding], list[str], dict[str, list[str]]]:
    findings: list[Finding] = []
    failures: list[str] = []
    skipped: dict[str, list[str]] = {}
    checkable = [s for s in standards if s.checks]

    for url, tags in targets:
        try:
            status, body = fetch(url)
        except urllib.error.HTTPError as exc:
            failures.append(f"{url}: HTTP {exc.code} — not swept")
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{url}: {exc.__class__.__name__}: {exc} — not swept")
            continue

        if status != 200:
            failures.append(f"{url}: HTTP {status} — not swept")
            continue

        for standard in checkable:
            if not applies_to_target(standard, tags):
                skipped.setdefault(url, []).append(
                    f"{standard.slug} (needs tag: {'/'.join(standard.target_tags)})"
                )
                continue
            for check in standard.checks:
                findings.extend(
                    run_check(
                        check,
                        url,
                        body,
                        standard.severity,
                        provenance_freshness_policy=(
                            "current-live-30d" if "current-live" in tags else None
                        ),
                    )
                )
    return findings, failures, skipped


def report(
    targets: list[Target],
    standards: list[Standard],
    findings: list[Finding],
    failures: list[str],
    skipped: dict[str, list[str]],
) -> None:
    checkable = [s for s in standards if s.checks]
    judgement = [s for s in standards if not s.checks]

    print(
        f"Fleet check — {len(targets)} page(s), "
        f"{len(checkable)} machine-checkable rule(s)"
    )
    print()

    for url, _tags in targets:
        page = [f for f in findings if f.url == url]
        failed = [f for f in failures if f.startswith(url + ":")]
        missed = skipped.get(url, [])
        if failed:
            print(f"  {url}\n    NOT SWEPT — {failed[0].split(': ', 1)[1]}")
            continue
        if not page:
            ran = len(checkable) - len(missed)
            print(f"  {url}\n    clean against all {ran} applicable rule(s)")
            for note in missed:
                print(f"    not applied: {note}")
            continue
        print(f"  {url}")
        for note in missed:
            print(f"    not applied: {note}")
        for finding in page:
            flag = "FAIL" if finding.blocking else "warn"
            print(f"    [{flag}] {finding.standard}/{finding.check}: {finding.message}")
            print(f"           {finding.detail}")
        print()

    blocking = [f for f in findings if f.blocking]
    warnings = [f for f in findings if not f.blocking]
    print()
    print(f"{len(blocking)} blocking, {len(warnings)} warning, {len(failures)} not swept")

    if judgement:
        print()
        print("Not verified by this sweep — judgement rules, enforced by reading:")
        for standard in judgement:
            print(f"  - {standard.slug}: {standard.title}")


def _write_json_report(path: Path, payload: str) -> None:
    """Atomically replace a regular report without following symlinks."""

    parent = path.parent if str(path.parent) else Path(".")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(parent, flags)
    temporary_name = f".{path.name}.tmp-{os.getpid()}-{secrets.token_hex(8)}"
    expected: tuple[int, int, int, int] | None = None
    try:
        try:
            existing = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            if stat.S_ISLNK(existing.st_mode) or not stat.S_ISREG(existing.st_mode):
                raise ValueError(
                    "JSON report destination must be a regular non-symlink file"
                )
            expected = (
                existing.st_dev,
                existing.st_ino,
                existing.st_size,
                existing.st_mtime_ns,
            )
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as handle:
                handle.write(payload.encode("utf-8"))
                handle.flush()
                os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if expected is not None:
            current = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
            observed = (
                current.st_dev,
                current.st_ino,
                current.st_size,
                current.st_mtime_ns,
            )
            if stat.S_ISLNK(current.st_mode) or observed != expected:
                raise ValueError("JSON report destination changed during write")
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    finally:
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def read_targets(path: Path) -> list[Target]:
    """One URL per line; optional comma-separated tags after whitespace."""
    targets: list[Target] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        url = parts[0]
        raw_tags = parts[1] if len(parts) == 2 else ""
        tags = tuple(
            tag.strip() for tag in raw_tags.replace(",", " ").split() if tag.strip()
        )
        targets.append((url.strip(), tags))
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="pages to sweep")
    parser.add_argument("--targets", type=Path, help="file of URLs, one per line")
    parser.add_argument(
        "--lint", action="store_true", help="parse standards and compile every regex"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run every check against its own examples (no network)",
    )
    parser.add_argument(
        "--tag",
        nargs="+",
        default=[],
        help="tags to apply to URLs given on the command line",
    )
    parser.add_argument("--json", type=Path, help="also write findings as JSON")
    args = parser.parse_args()

    try:
        standards = load_standards()
    except StandardError as exc:
        print(f"standards/ is malformed: {exc}")
        return 2

    if args.lint or args.self_test:
        checks = sum(len(s.checks) for s in standards)
        print(f"Parsed {len(standards)} standard(s), {checks} check(s).")
        for standard in standards:
            mark = f"{len(standard.checks)} check(s)" if standard.checks else "judgement"
            print(f"  - {standard.slug} [{standard.severity}] {mark}")
        if args.lint and not args.self_test:
            return 0

        problems = self_test(standards)
        if problems:
            print()
            print(f"Self-test FAILED — {len(problems)} problem(s):")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print()
        print("Self-test passed: every check flags its violating samples and clears "
              "its clean ones.")
        return 0

    cli_tags = tuple(args.tag)
    targets: list[Target] = [(url, cli_tags) for url in args.urls]
    if args.targets:
        targets += read_targets(args.targets)
    if not targets:
        parser.error("give at least one URL, or --targets, or --lint/--self-test")

    findings, failures, skipped = sweep(targets, standards)
    report(targets, standards, findings, failures, skipped)

    if args.json:
        try:
            _write_json_report(
                args.json,
                json.dumps(
                    {
                        "targets": [{"url": u, "tags": list(g)} for u, g in targets],
                        "findings": [asdict(f) for f in findings],
                        "not_swept": failures,
                        "not_applied": skipped,
                    },
                    indent=2,
                ),
            )
        except (OSError, ValueError) as exc:
            print(f"\nJSON report was not written safely: {exc}")
            return 2
        print(f"\nJSON written to {args.json}")

    if failures:
        return 2
    return 1 if any(f.blocking for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
