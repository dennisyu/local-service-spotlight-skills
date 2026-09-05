#!/usr/bin/env python3
"""Validate sanitized public agent-fleet receipts and append-only history."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

try:  # package import in tests; direct import when run as this script
    from .agent_fleet_contract import (
        ALL_PUBLIC_ACTOR_IDS,
        ALL_PUBLIC_HUMAN_REVIEWERS,
        ALL_PUBLIC_MODEL_IDS,
        DOCUMENTATION_ACTOR_REGISTRY_RELATIVE_PATH,
        IDENTITY_REGISTRY_DOCUMENT,
        IDENTITY_REGISTRY_RELATIVE_PATH,
        IDENTITY_REGISTRY_SHA256,
        PUBLIC_ACTOR_IDS,
        PUBLIC_ACTOR_REGISTRY_VERSION,
        PUBLIC_HUMAN_REVIEWERS,
        PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION,
        PUBLIC_MODEL_IDS,
        PUBLIC_MODEL_REGISTRY_VERSION,
        documentation_actor_registry_history_problem,
        parse_identity_registry_bytes,
        registry_history_problem,
    )
except ImportError:  # pragma: no cover - exercised by CLI integration tests
    from agent_fleet_contract import (  # type: ignore
        ALL_PUBLIC_ACTOR_IDS,
        ALL_PUBLIC_HUMAN_REVIEWERS,
        ALL_PUBLIC_MODEL_IDS,
        DOCUMENTATION_ACTOR_REGISTRY_RELATIVE_PATH,
        IDENTITY_REGISTRY_DOCUMENT,
        IDENTITY_REGISTRY_RELATIVE_PATH,
        IDENTITY_REGISTRY_SHA256,
        PUBLIC_ACTOR_IDS,
        PUBLIC_ACTOR_REGISTRY_VERSION,
        PUBLIC_HUMAN_REVIEWERS,
        PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION,
        PUBLIC_MODEL_IDS,
        PUBLIC_MODEL_REGISTRY_VERSION,
        documentation_actor_registry_history_problem,
        parse_identity_registry_bytes,
        registry_history_problem,
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


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS_DIR = ROOT / "receipts" / "agent-fleet"
SCHEMA_FILE = "receipt.schema.json"
SOURCES_DIR = RECEIPTS_DIR / "sources"
IDENTITY_REGISTRIES_DIR = RECEIPTS_DIR / "identity-registries"
SOURCE_SCHEMA_FILE = "source.schema.json"
GOLDEN_RECEIPT = (
    RECEIPTS_DIR
    / "examples"
    / "fleet-page-bbbbbbbbbbbbbbbbbbbb.json"
)
GOLDEN_RAIL = GOLDEN_RECEIPT.with_suffix(".html")
GOLDEN_SOURCE = (
    RECEIPTS_DIR
    / "examples"
    / "sources"
    / "0123456789abcdef0123456789abcdef01234567.json"
)
FLEET_LIVE_URL = "https://blitzmetrics.com/scheduled-jobs-fleet/"
FLEET_SOURCE_REPOSITORY = "https://github.com/Local-Service-Spotlight/agent-fleet"
FLEET_GENERATOR_CONTRACT = "fleet-public-render-v3"
MAX_LEDGER_FILE_BYTES = 1024 * 1024
STATUSES = {"verified", "verification-failed"}
HASH = re.compile(r"^[0-9a-f]{64}$")
SOURCE_REVISION = re.compile(r"^[0-9a-f]{40}$")
RECEIPT_ID = re.compile(r"^fleet-page-[0-9a-f]{20}$")
PUBLIC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,199}$")
WORDPRESS_REVISION = re.compile(
    r"^wp:110278:[A-Za-z0-9][A-Za-z0-9._-]{0,119}$"
)
ISO_INSTANT = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
PLACEHOLDER = re.compile(
    r"\b(?:unknown|nobody|none|null|unset|unassigned|someone|anonymous|anonymized|"
    r"redacted|system|invalid|unverified|fabricated|synthetic|placeholder|example|"
    r"sample|pending|awaiting|unavailable|"
    r"undisclosed|withheld|tbd|todo|n/?a|review required|not (?:known|provided|"
    r"recorded|reviewed|disclosed|assigned))\b",
    re.IGNORECASE,
)
PENDING_REVIEW = re.compile(
    r"(?:\bunreviewed\b|\b(?:not|no|without|pending|awaiting|missing|unknown|none|tbd)\b"
    r"[^.]{0,60}\breview(?:ed|er)?\b|\breview(?:ed|er)?\b[^.]{0,60}"
    r"\b(?:pending|awaiting|missing|unknown|none|tbd)\b)",
    re.IGNORECASE,
)
GENERIC_IDENTITIES = {
    "agent",
    "human",
    "human reviewer",
    "person",
    "review complete",
    "reviewed",
    "reviewer",
    "verifier",
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
KNOWN_AGENT_REVIEWERS = {
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
FORBIDDEN_KEY_FRAGMENTS = {
    "apikey",
    "clientdata",
    "credential",
    "email",
    "immutablereceipturl",
    "jobid",
    "ledgercommit",
    "ledgerpath",
    "machinepath",
    "password",
    "privateartifact",
    "privatejob",
    "prompt",
    "publicreceiptsha256",
    "receiptsha256",
    "registrypath",
    "schedule",
    "secret",
    "token",
}
COMMON_FIELDS = {
    "schemaVersion",
    "status",
    "receiptId",
    "contentHash",
    "verificationHash",
    "sourceRevision",
    "model",
    "humanReviewer",
    "humanReviewerRole",
    "runId",
    "liveUrl",
    "checkedAt",
    "checkedBy",
}
SUCCESS_FIELDS = {
    "postContentHash",
    "extractedPostContentSha256",
    "anonymousResponseSha256",
    "anonymousContentLength",
    "extractionStart",
    "extractionEnd",
    "sourceManifestSha256",
    "configuredCount",
    "publicDefinitionCount",
    "itemListCount",
    "linkContentHash",
    "linkReceiptId",
    "finalAnonymousReadback",
    "browserVisibilityVerified",
    "browserCheckedAt",
    "browserCheckedBy",
    "browserRunReceiptId",
    "httpStatus",
    "cacheBuster",
    "wordpressRevision",
    "articleSchemaCount",
    "articleDateModified",
    "wordpressModifiedAt",
}
FAILURE_FIELDS = {"failureStage", "failureCode", "failureDetail"}
ALLOWED_FIELDS = COMMON_FIELDS | SUCCESS_FIELDS | FAILURE_FIELDS
SOURCE_MANIFEST_FIELDS = {
    "schemaVersion",
    "status",
    "sourceRepository",
    "sourceRevision",
    "generatorContract",
    "configuredCount",
    "archivedCount",
    "invalidDefinitionCount",
    "publicDefinitionCount",
    "actorRegistryVersion",
    "humanReviewerRegistryVersion",
    "modelRegistryVersion",
    "identityRegistrySha256",
}
MAX_PUBLIC_DECODE_ROUNDS = 16
RECEIPT_SCHEMA_CANONICAL_SHA256 = (
    "25926a0cb59a99671d625d5217b22394f07d872880cebbdc552427a37efb2db2"
)
SOURCE_SCHEMA_CANONICAL_SHA256 = (
    "28ef64a21ee7328c58d4a9471acc0e186f2f81399ec1bc556f38231af2fbaa4b"
)
EVIDENCE_CLOCK_FUTURE_TOLERANCE = timedelta(minutes=5)
MARKER_START = "<!-- BM-FLEET-PAGE:START -->"
MARKER_END = "<!-- BM-FLEET-PAGE:END -->"
LEDGER_DIRECTORIES = {
    "examples",
    "examples/sources",
    "identity-registries",
    "sources",
}
LEDGER_STATIC_FILES = {
    "README.md",
    SCHEMA_FILE,
    "identity-registry.schema.json",
    "public-identity-registry.json",
    "sources/" + SOURCE_SCHEMA_FILE,
    "examples/" + GOLDEN_RECEIPT.name,
    "examples/" + GOLDEN_RAIL.name,
    "examples/sources/" + GOLDEN_SOURCE.name,
}
LEDGER_RECEIPT_PATH = re.compile(r"^fleet-page-[0-9a-f]{20}\.json$")
LEDGER_SOURCE_PATH = re.compile(
    r"^sources/[0-9a-f]{40}\.json$"
)
LEDGER_IDENTITY_REGISTRY_PATH = re.compile(
    r"^identity-registries/[0-9a-f]{64}\.json$"
)
FAILURE_CONTRACTS = {
    (
        "candidate-validation",
        "CANDIDATE_INVALID",
        "The publication candidate failed the public contract.",
    ),
    (
        "link-verification",
        "LINK_VERIFICATION_FAILED",
        "Required public links did not pass verification.",
    ),
    (
        "wordpress-readback",
        "WORDPRESS_READBACK_FAILED",
        "The exact WordPress post-content body could not be verified.",
    ),
    (
        "anonymous-readback",
        "HTTP_ERROR",
        "The anonymous publication readback did not return HTTP 200.",
    ),
    (
        "anonymous-readback",
        "HASH_MISMATCH",
        "The published bytes did not match the expected hashes.",
    ),
    (
        "anonymous-readback",
        "MARKER_CONTRACT_FAILED",
        "The anonymous response did not contain one ordered marker pair.",
    ),
    (
        "schema-validation",
        "ARTICLE_SCHEMA_INVALID",
        "The anonymous response did not contain exactly one valid Article owner.",
    ),
    (
        "publication-validation",
        "COUNT_MISMATCH",
        "Published fleet counts did not match the configured public definitions.",
    ),
}


def _placeholder_digest(value: object) -> bool:
    """Reject synthetic low-entropy digests outside the explicit golden fixture."""

    return isinstance(value, str) and HASH.fullmatch(value) is not None and len(
        set(value)
    ) < 4


def _placeholder_source_revision(value: object) -> bool:
    """Reject obvious synthetic 40-hex values where a real commit is claimed."""

    return (
        isinstance(value, str)
        and SOURCE_REVISION.fullmatch(value) is not None
        and len(set(value)) < 4
    )


def _canonical_receipt_id(receipt: dict) -> str | None:
    """Return the generator's fixed receipt ID formula."""
    verification_hash = receipt.get("verificationHash")
    if not isinstance(verification_hash, str) or HASH.fullmatch(verification_hash) is None:
        return None
    return "fleet-page-" + verification_hash[:20]


def _parse_iso_instant(value: object) -> datetime | None:
    if not isinstance(value, str) or ISO_INSTANT.fullmatch(value) is None:
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
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _valid_iso_instant(value: object) -> bool:
    return _parse_iso_instant(value) is not None


def _evidence_clock_is_future(value: object) -> bool:
    parsed = _parse_iso_instant(value)
    return (
        parsed is not None
        and parsed
        > datetime.now(timezone.utc) + EVIDENCE_CLOCK_FUTURE_TOLERANCE
    )


def _https_problem(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return "must be a non-empty string"
    if re.search(r"[\s\x00-\x1f\x7f]", value) or re.search(
        r"[\s\x00-\x1f\x7f]", unquote(value)
    ):
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
    if value != FLEET_LIVE_URL:
        return f"must equal the canonical public fleet URL {FLEET_LIVE_URL!r}"
    return None


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _walk_keys(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _walk_strings(value: object):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value


def _decoded_public_values(value: str) -> tuple[str, ...]:
    values = [value]
    for _ in range(MAX_PUBLIC_DECODE_ROUNDS):
        decoded = unquote(unescape(values[-1]))
        if decoded == values[-1]:
            break
        values.append(decoded)
    return tuple(values)


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


def _contains_url_form(value: str) -> bool:
    return any(
        "://" in _comparison_text(item)
        for item in _decoded_public_values(value)
    )


def _private_string(value: str) -> str | None:
    shared_problem = _shared_public_value_problem(value)
    if shared_problem is not None:
        if "URL" in shared_problem and "protocol-relative" not in shared_problem:
            return "unapproved artifact URL"
        for prefix in ("contains an ", "contains a ", "contains "):
            if shared_problem.startswith(prefix):
                return shared_problem[len(prefix) :]
        return shared_problem
    raw_decoded_values = _decoded_public_values(value)
    if any(
        re.search(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]", item)
        for item in raw_decoded_values
    ):
        return "bidirectional text controls"
    if any(
        any(unicodedata.category(character).startswith("C") for character in item)
        for item in raw_decoded_values
    ):
        return "control characters"
    if unquote(unescape(raw_decoded_values[-1])) != raw_decoded_values[-1]:
        return "excessively nested URL/HTML encoding"
    decoded_values = [_comparison_text(item) for item in raw_decoded_values]
    if re.search(r"%[0-9a-f]{2}", decoded_values[-1], re.IGNORECASE):
        return "excessively nested URL encoding"
    inspected = "\n".join(decoded_values)

    if re.search(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", inspected):
        return "email address"
    allowed_public_urls = {FLEET_LIVE_URL, FLEET_SOURCE_REPOSITORY}
    url_tokens = re.findall(
        r"\b(?!file:)[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"']+",
        inspected,
        flags=re.IGNORECASE,
    )
    if url_tokens and (
        value not in allowed_public_urls
        or any(url_token != value for url_token in url_tokens)
    ):
        return "unapproved artifact URL"
    path_inspected = re.sub(
        r"\b(?!file:)[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"']+",
        "",
        inspected,
        flags=re.IGNORECASE,
    )
    if re.search(
        r"(?:^|[^A-Za-z0-9])\.\.[/\\]|"
        r"(?:^|[\s:=,;([{-])\.[/\\](?:Applications|bin|boot|data|dev|etc|home|"
        r"Library|media|mnt|Network|nix|opt|private|proc|root|run|sbin|sdcard|"
        r"snap|srv|storage|sys|System|tmp|usr|Users|var|Volumes|workspace)"
        r"(?=$|[/\\])|"
        r"(?:^|[\s:=,;([{-])(?:Users[/\\]|Library[/\\]Application\s+Support[/\\])",
        path_inspected,
        re.IGNORECASE,
    ):
        return "relative or traversing private machine path"
    if re.search(
        r"(?:file://|(?<![A-Za-z0-9._~-])~[/\\](?:[^\s<>\"']*)|"
        r"%(?:USERPROFILE|APPDATA|LOCALAPPDATA|TEMP|TMP)%[/\\][^\s<>\"']*|"
        r"\$(?:\{)?(?:HOME|USERPROFILE|TMPDIR|TEMP|TMP)(?:\})?[/\\][^\s<>\"']*|"
        r"(?<![A-Za-z0-9._~-])[A-Za-z]:[/\\](?:[^\s<>\"']*)|"
        r"(?<![\\])\\\\[^\\/\s<>\"']+(?:[\\/][^\s<>\"']*)?|"
        r"(?<![A-Za-z0-9._~/-])/(?:Applications|bin|data|dev|etc|home|Library|mnt|opt|"
        r"boot|media|Network|nix|private|proc|root|run|sbin|sdcard|snap|srv|"
        r"storage|sys|System|tmp|usr|Users|var|Volumes|workspace)"
        r"(?=$|[/\\\s<>\[\](){}\"',;:])(?:[/\\][^\s<>\"']*)?)",
        path_inspected,
        re.IGNORECASE,
    ):
        return "private machine path"
    if re.search(r"(?:^|[/\\])\.ssh(?:$|[/\\])", path_inspected, re.IGNORECASE):
        return "private machine path"
    if re.search(
        r"(?:[?&;]|\b)(?:api[_-]?key|authorization|auth|password|passwd|sig|"
        r"session(?:id)?|[A-Za-z0-9_-]*(?:token|secret|credential|signature)|"
        r"private[_-]?key)\s*=",
        inspected,
        re.IGNORECASE,
    ):
        return "credential-bearing query parameter"
    label_inspected = "".join(
        " "
        if character.isspace()
        or character == "_"
        or unicodedata.category(character) == "Pd"
        or character in {"\u2212", "\ufe58"}
        else character
        for character in inspected
    )
    label_inspected = re.sub(r"\s+", " ", label_inspected)
    if re.search(
        r"\b(?:cron|schedule|(?:private )?prompt|private job(?: id)?|job id|"
        r"task id|client(?: id| secret| data)?|customer(?: id| data)?|registry path|"
        r"machine path|api key|access token|auth token|session token|"
        r"credential|password|token|secret)"
        r"\s*[:=/]\s*\S",
        label_inspected,
        re.IGNORECASE,
    ):
        return "sensitive private-data label"
    if re.search(
        r"\b(?:clientid|customerid|jobid|taskid|registrypath|machinepath|apikey|"
        r"accesstoken|authtoken|sessiontoken|clientsecret|privateprompt|privatejob)"
        r"\s*[:=/]\s*\S",
        label_inspected,
        re.IGNORECASE,
    ):
        return "sensitive private-data label"
    if re.search(
        r"(?<![:/])//[A-Za-z0-9][A-Za-z0-9.-]*(?::\d+)?(?:/[^\s<>\"']*)?",
        inspected,
    ):
        return "protocol-relative or network-path URL"
    if re.search(
        r"(?:\bsk_(?:live|test|proj)_[A-Za-z0-9_-]{8,}\b|"
        r"\brk_live_[A-Za-z0-9_-]{8,}\b|\bsk-[A-Za-z0-9_-]{12,}\b|"
        r"\bgh[pousr]_[A-Za-z0-9]{12,}\b|\bgithub_pat_[A-Za-z0-9_]{16,}\b|"
        r"\bglpat-[A-Za-z0-9_-]{16,}\b|\bxox[baprs]-[A-Za-z0-9-]{12,}\b|"
        r"\bA[KS]IA[0-9A-Z]{16}\b|\bAIza[0-9A-Za-z_-]{20,}\b|"
        r"\bnpm_[A-Za-z0-9]{20,}\b|\bya29\.[A-Za-z0-9_-]{20,}\b|"
        r"\bpypi-[A-Za-z0-9_-]{8,}\b|\bdop_v1_[A-Za-z0-9_-]{8,}\b|"
        r"\bhf_[A-Za-z0-9_-]{8,}\b|\bSK[0-9A-Fa-f]{32}\b|"
        r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----|"
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b|"
        r"\bSG\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}\b|"
        r"\bBearer\s+[A-Za-z0-9._~-]{12,}|"
        r"\bBasic\s+[A-Za-z0-9+/]{12,}={0,2})",
        inspected,
        re.IGNORECASE,
    ):
        return "credential/token pattern"
    return None


def _private_key(key: object) -> bool:
    normalized = _normalized_key(key)
    return any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS)


def _valid_identity(value: object, *, allow_unknown_model: bool = False) -> bool:
    if not isinstance(value, str) or value != value.strip():
        return False
    normalized = " ".join(value.split())
    comparison = _comparison_text(normalized)
    if re.search(r"%[0-9a-f]{2}", normalized, re.IGNORECASE):
        return False
    if allow_unknown_model and normalized == "UNKNOWN":
        return True
    return (
        len(comparison) >= 2
        and len(value) <= 200
        and not _has_ignored_format_character(normalized)
        and not any(
            unicodedata.category(character).startswith("C") for character in value
        )
        and any(character.isalpha() for character in comparison)
        and not _contains_url_form(comparison)
        and comparison.casefold() not in GENERIC_IDENTITIES
        and PLACEHOLDER.search(comparison) is None
        and re.search(r"[\x00-\x1f\x7f]", normalized) is None
    )


def _looks_like_agent_identity(value: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", _comparison_text(value).casefold())
    if not set(tokens) & KNOWN_AGENT_REVIEWERS:
        return False
    non_name_tokens = (
        KNOWN_AGENT_REVIEWERS
        | GENERIC_ROLE_TOKENS
        | GENERIC_MODEL_TOKENS
        | {"v", "version"}
    )
    if any(
        token not in non_name_tokens
        and not token.isdigit()
        and re.fullmatch(r"v\d+", token) is None
        for token in tokens
    ):
        return False
    return True


def _looks_like_generic_role_identity(value: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", _comparison_text(value).casefold())
    return bool(tokens) and all(token in GENERIC_ROLE_TOKENS for token in tokens)


def _valid_human_identity(value: object) -> bool:
    if not _valid_identity(value) or not isinstance(value, str):
        return False
    tokens = _unicode_word_tokens(value)
    if not tokens:
        return False
    non_name_tokens = (
        GENERIC_ROLE_TOKENS | KNOWN_AGENT_REVIEWERS | GENERIC_MODEL_TOKENS
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


def _valid_verifier_identity(value: object) -> bool:
    if not isinstance(value, str) or value != value.strip() or not _valid_identity(value):
        return False
    return (
        PUBLIC_AGENT_IDENTITY.fullmatch(value) is not None
        and value in ALL_PUBLIC_ACTOR_IDS
    )


def _valid_model(value: object) -> bool:
    if not _valid_identity(value, allow_unknown_model=True):
        return False
    if value == "UNKNOWN":
        return True
    assert isinstance(value, str)
    return value in ALL_PUBLIC_MODEL_IDS


def _valid_public_id(value: object) -> bool:
    comparison = _comparison_text(value) if isinstance(value, str) else ""
    return (
        isinstance(value, str)
        and PUBLIC_ID.fullmatch(value) is not None
        and not _contains_url_form(comparison)
        and PLACEHOLDER.search(comparison) is None
        and not _has_placeholder_slug_token(comparison)
    )


def _valid_nonnegative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class DuplicateJsonMember(ValueError):
    """Raised when a JSON object repeats a member name."""


def _reject_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, child in pairs:
        if key in value:
            raise DuplicateJsonMember(f"duplicate JSON member {key!r}")
        value[key] = child
    return value


def _read_bounded_regular_bytes(path: Path, boundary: Path) -> bytes:
    candidate = Path(os.path.abspath(path))
    root = Path(os.path.abspath(boundary))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise OSError(f"{candidate} escapes ledger boundary {root}") from exc

    root_stat = root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise OSError(f"{root} must be a real, non-symlink directory")
    cursor = root
    for part in relative.parts:
        cursor /= part
        item_stat = cursor.lstat()
        if stat.S_ISLNK(item_stat.st_mode):
            raise OSError(f"{cursor} must not be a symlink")
        if cursor != candidate and not stat.S_ISDIR(item_stat.st_mode):
            raise OSError(f"{cursor} must be a directory")
    candidate_stat = candidate.lstat()
    if not stat.S_ISREG(candidate_stat.st_mode):
        raise OSError(f"{candidate} must be a regular file")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(candidate, flags)
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise OSError(f"{candidate} must remain a regular file")
        identity = lambda item: (
            item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns
        )
        if identity(candidate_stat) != identity(opened_stat):
            raise OSError(f"{candidate} changed between inspection and open")
        if opened_stat.st_size > MAX_LEDGER_FILE_BYTES:
            raise OSError(
                f"{candidate} exceeds {MAX_LEDGER_FILE_BYTES} byte ledger limit"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(MAX_LEDGER_FILE_BYTES + 1)
            if len(raw) > MAX_LEDGER_FILE_BYTES:
                raise OSError(
                    f"{candidate} exceeds {MAX_LEDGER_FILE_BYTES} byte ledger limit"
                )
        after_stat = os.fstat(descriptor)
        if identity(opened_stat) != identity(after_stat):
            raise OSError(f"{candidate} changed during bounded read")
        final_stat = candidate.lstat()
        if stat.S_ISLNK(final_stat.st_mode) or identity(after_stat) != identity(final_stat):
            raise OSError(f"{candidate} path changed during bounded read")
        return raw
    finally:
        os.close(descriptor)


def _load_json(path: Path, boundary: Path | None = None) -> object:
    raw = _read_bounded_regular_bytes(path, boundary or path.parent)
    return _loads_json(raw.decode("utf-8"))


def _loads_json(text: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-JSON numeric constant {value!r}")

    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_members,
        parse_constant=reject_constant,
    )


def _string_member_set(value: object) -> set[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return set(value)


def _canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _schema_contract_errors(directory: Path) -> list[str]:
    path = directory / SCHEMA_FILE
    try:
        schema = _load_json(path, directory)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return [f"{SCHEMA_FILE}: cannot parse required schema: {exc}"]
    if not isinstance(schema, dict):
        return [f"{SCHEMA_FILE}: schema must be a JSON object"]

    errors: list[str] = []
    if _canonical_json_sha256(schema) != RECEIPT_SCHEMA_CANONICAL_SHA256:
        errors.append(
            f"{SCHEMA_FILE}: full canonical schema contract drifted"
        )
    properties = schema.get("properties")
    if not isinstance(properties, dict) or set(properties) != ALLOWED_FIELDS:
        errors.append(f"{SCHEMA_FILE}: properties must equal the validator field set")
    if _string_member_set(schema.get("required")) != COMMON_FIELDS:
        errors.append(f"{SCHEMA_FILE}: required fields must equal the common envelope")
    if schema.get("additionalProperties") is not False:
        errors.append(f"{SCHEMA_FILE}: additionalProperties must be false")
    if isinstance(properties, dict):
        if properties.get("humanReviewerRole") != {"const": "human"}:
            errors.append(f"{SCHEMA_FILE}: humanReviewerRole must be exactly 'human'")
        if properties.get("liveUrl") != {"const": FLEET_LIVE_URL}:
            errors.append(f"{SCHEMA_FILE}: liveUrl must be the canonical public fleet URL")
        if properties.get("extractionStart") != {"const": MARKER_START}:
            errors.append(f"{SCHEMA_FILE}: extractionStart marker drifted")
        if properties.get("extractionEnd") != {"const": MARKER_END}:
            errors.append(f"{SCHEMA_FILE}: extractionEnd marker drifted")
        expected_failure_values = {
            "failureStage": {stage for stage, _, _ in FAILURE_CONTRACTS},
            "failureCode": {code for _, code, _ in FAILURE_CONTRACTS},
            "failureDetail": {detail for _, _, detail in FAILURE_CONTRACTS},
        }
        for field, expected in expected_failure_values.items():
            definition = properties.get(field, {})
            if (
                not isinstance(definition, dict)
                or _string_member_set(definition.get("enum")) != expected
            ):
                errors.append(f"{SCHEMA_FILE}: {field} approved vocabulary drifted")
    branches = schema.get("allOf")
    conditional = (
        branches[0]
        if isinstance(branches, list) and branches and isinstance(branches[0], dict)
        else {}
    )
    then_branch = conditional.get("then")
    else_branch = conditional.get("else")
    then_required = (
        _string_member_set(then_branch.get("required"))
        if isinstance(then_branch, dict)
        else None
    )
    else_required = (
        _string_member_set(else_branch.get("required"))
        if isinstance(else_branch, dict)
        else None
    )
    if then_required != SUCCESS_FIELDS:
        errors.append(f"{SCHEMA_FILE}: verified required fields drifted")
    if else_required != FAILURE_FIELDS:
        errors.append(f"{SCHEMA_FILE}: failed-attempt required fields drifted")
    failure_branches = else_branch.get("oneOf") if isinstance(else_branch, dict) else None
    schema_failure_contracts: set[tuple[object, object, object]] = set()
    if isinstance(failure_branches, list):
        for branch in failure_branches:
            definitions = branch.get("properties", {}) if isinstance(branch, dict) else {}
            if isinstance(definitions, dict):
                schema_failure_contracts.add(
                    tuple(
                        definitions.get(field, {}).get("const")
                        if isinstance(definitions.get(field), dict)
                        else None
                        for field in ("failureStage", "failureCode", "failureDetail")
                    )
                )
    if schema_failure_contracts != FAILURE_CONTRACTS:
        errors.append(f"{SCHEMA_FILE}: approved failure template combinations drifted")
    return errors


def _source_schema_contract_errors(directory: Path) -> list[str]:
    path = directory / SOURCE_SCHEMA_FILE
    try:
        schema = _load_json(path, directory)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return [f"sources/{SOURCE_SCHEMA_FILE}: cannot parse required schema: {exc}"]
    if not isinstance(schema, dict):
        return [f"sources/{SOURCE_SCHEMA_FILE}: schema must be a JSON object"]
    errors: list[str] = []
    if _canonical_json_sha256(schema) != SOURCE_SCHEMA_CANONICAL_SHA256:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: full canonical schema contract drifted"
        )
    properties = schema.get("properties")
    if not isinstance(properties, dict) or set(properties) != SOURCE_MANIFEST_FIELDS:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: properties must equal the source-manifest field set"
        )
    if _string_member_set(schema.get("required")) != SOURCE_MANIFEST_FIELDS:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: required fields must equal the source-manifest field set"
        )
    if schema.get("additionalProperties") is not False:
        errors.append(f"sources/{SOURCE_SCHEMA_FILE}: additionalProperties must be false")
    if isinstance(properties, dict) and properties.get("status") != {
        "const": "sanitized-source-manifest"
    }:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: status must be sanitized-source-manifest"
        )
    if isinstance(properties, dict) and properties.get("sourceRepository") != {
        "const": FLEET_SOURCE_REPOSITORY
    }:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: sourceRepository canonical URL drifted"
        )
    if isinstance(properties, dict) and properties.get("generatorContract") != {
        "const": FLEET_GENERATOR_CONTRACT
    }:
        errors.append(
            f"sources/{SOURCE_SCHEMA_FILE}: generatorContract version drifted"
        )
    return errors


def validate_source_manifest(
    manifest: object, path: Path, namespace: str = "sources"
) -> list[str]:
    where = f"{namespace}/{path.name}"
    if not isinstance(manifest, dict):
        return [f"{where}: source manifest must be a JSON object"]
    errors: list[str] = []
    unknown = sorted(
        (key for key in manifest if key not in SOURCE_MANIFEST_FIELDS), key=str
    )
    missing = sorted(SOURCE_MANIFEST_FIELDS - set(manifest))
    if unknown:
        errors.append(
            f"{where}: unknown source-manifest field(s): "
            + ", ".join(repr(key) for key in unknown)
        )
    if missing:
        errors.append(f"{where}: missing source-manifest field(s): {', '.join(missing)}")
    schema_version = manifest.get("schemaVersion")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        errors.append(f"{where}: schemaVersion must be integer 1")
    if manifest.get("status") != "sanitized-source-manifest":
        errors.append(f"{where}: status must be sanitized-source-manifest")
    if manifest.get("sourceRepository") != FLEET_SOURCE_REPOSITORY:
        errors.append(f"{where}: sourceRepository must equal the canonical agent-fleet URL")
    source_revision = manifest.get("sourceRevision")
    if not isinstance(source_revision, str) or SOURCE_REVISION.fullmatch(source_revision) is None:
        errors.append(f"{where}: sourceRevision must be a full lowercase 40-hex commit")
    elif _placeholder_source_revision(source_revision):
        errors.append(f"{where}: sourceRevision must not be a placeholder commit")
    if SOURCE_REVISION.fullmatch(path.stem) is None or path.suffix != ".json":
        errors.append(
            f"{where}: filename must equal the full lowercase 40-hex sourceRevision plus '.json'"
        )
    elif source_revision != path.stem:
        errors.append(f"{where}: filename must equal sourceRevision + '.json'")
    if manifest.get("generatorContract") != FLEET_GENERATOR_CONTRACT:
        errors.append(f"{where}: generatorContract must equal {FLEET_GENERATOR_CONTRACT!r}")
    registry_fields = (
        (
            "actorRegistryVersion",
            re.compile(r"^fleet-public-actors-v[1-9][0-9]*$"),
        ),
        (
            "humanReviewerRegistryVersion",
            re.compile(r"^fleet-public-human-reviewers-v[1-9][0-9]*$"),
        ),
        (
            "modelRegistryVersion",
            re.compile(r"^fleet-public-models-v[1-9][0-9]*$"),
        ),
    )
    for field_name, pattern in registry_fields:
        value = manifest.get(field_name)
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            errors.append(f"{where}: {field_name} has an invalid registry version")
    identity_registry_sha256 = manifest.get("identityRegistrySha256")
    if (
        not isinstance(identity_registry_sha256, str)
        or HASH.fullmatch(identity_registry_sha256) is None
    ):
        errors.append(f"{where}: identityRegistrySha256 must be a lowercase SHA-256")
    counts: dict[str, int] = {}
    for field_name in (
        "configuredCount",
        "archivedCount",
        "invalidDefinitionCount",
        "publicDefinitionCount",
    ):
        value = manifest.get(field_name)
        if not _valid_nonnegative_integer(value):
            errors.append(f"{where}: {field_name} must be a non-negative integer")
        else:
            counts[field_name] = value
    if counts.get("publicDefinitionCount", 0) > counts.get("configuredCount", 0):
        errors.append(f"{where}: publicDefinitionCount exceeds configuredCount")
    forbidden = sorted(
        {str(key) for key in _walk_keys(manifest) if _private_key(key)}, key=str.casefold
    )
    if forbidden:
        errors.append(f"{where}: private field(s) are forbidden: {', '.join(forbidden)}")
    for problem in sorted(
        {problem for value in _walk_strings(manifest) if (problem := _private_string(value))}
    ):
        errors.append(f"{where}: source manifest contains a {problem}")
    return errors


def _source_registry_binding_errors(
    manifest: object,
    path: Path,
    registries: dict[str, tuple[dict, Path, bytes]],
) -> list[str]:
    """Bind a sanitized source to one immutable identity-registry artifact."""

    if not isinstance(manifest, dict):
        return []
    where = f"sources/{path.name}"
    registry_hash = manifest.get("identityRegistrySha256")
    if not isinstance(registry_hash, str):
        return []
    companion = registries.get(registry_hash)
    if companion is None:
        return [
            f"{where}: no exact identity-registry artifact exists at "
            f"identity-registries/{registry_hash}.json"
        ]
    registry, _, _ = companion
    errors: list[str] = []
    for field, collection in (
        ("actorRegistryVersion", "actorRegistries"),
        ("humanReviewerRegistryVersion", "humanReviewerRegistries"),
        ("modelRegistryVersion", "modelRegistries"),
    ):
        version = manifest.get(field)
        versions = registry.get(collection)
        if not isinstance(versions, dict) or version not in versions:
            errors.append(
                f"{where}: {field} is not defined by identity registry {registry_hash}"
            )
    return errors


def _receipt_registry_binding_errors(
    receipt: object,
    path: Path,
    manifest: object,
    registries: dict[str, tuple[dict, Path, bytes]],
) -> list[str]:
    """Check receipt signers/model against versions selected by its source."""

    if not isinstance(receipt, dict) or not isinstance(manifest, dict):
        return []
    registry_hash = manifest.get("identityRegistrySha256")
    if not isinstance(registry_hash, str) or registry_hash not in registries:
        return []
    registry = registries[registry_hash][0]
    where = path.name
    errors: list[str] = []

    def members(version_field: str, collection: str) -> set[str]:
        version = manifest.get(version_field)
        versions = registry.get(collection)
        values = versions.get(version) if isinstance(versions, dict) else None
        return set(values) if isinstance(values, list) else set()

    actor_ids = members("actorRegistryVersion", "actorRegistries")
    human_reviewers = members(
        "humanReviewerRegistryVersion", "humanReviewerRegistries"
    )
    model_ids = members("modelRegistryVersion", "modelRegistries")
    for field in ("checkedBy", "browserCheckedBy"):
        if field in receipt and receipt.get(field) not in actor_ids:
            errors.append(
                f"{where}: {field} is not in source-selected actor registry"
            )
    if receipt.get("humanReviewer") not in human_reviewers:
        errors.append(
            f"{where}: humanReviewer is not in source-selected human-reviewer registry"
        )
    model = receipt.get("model")
    if model != "UNKNOWN" and model not in model_ids:
        errors.append(f"{where}: model is not in source-selected model registry")
    return errors


def validate_receipt(receipt: object, path: Path) -> list[str]:
    where = path.name
    if not isinstance(receipt, dict):
        return [f"{where}: receipt must be a JSON object"]
    errors: list[str] = []
    # Only the one tracked golden file may use deliberately obvious fixture
    # digests. A clone beneath an unrelated directory named ``examples`` must
    # not weaken production receipt validation.
    fixture_receipt = path == GOLDEN_RECEIPT

    unknown = sorted((key for key in receipt if key not in ALLOWED_FIELDS), key=str)
    if unknown:
        errors.append(
            f"{where}: unknown public field(s): "
            + ", ".join(repr(key) for key in unknown)
        )
    missing = sorted(COMMON_FIELDS - set(receipt))
    if missing:
        errors.append(f"{where}: missing common field(s): {', '.join(missing)}")

    forbidden = sorted(
        {str(key) for key in _walk_keys(receipt) if _private_key(key)},
        key=str.casefold,
    )
    if forbidden:
        errors.append(
            f"{where}: private/wrapper field(s) are forbidden: {', '.join(forbidden)}"
        )

    schema_version = receipt.get("schemaVersion")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        errors.append(f"{where}: schemaVersion must be integer 1")
    status = receipt.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        errors.append(f"{where}: status must discriminate verified or verification-failed")

    verification_hash = receipt.get("verificationHash")
    if not isinstance(verification_hash, str) or HASH.fullmatch(verification_hash) is None:
        errors.append(f"{where}: verificationHash must be a lowercase SHA-256")
    elif not fixture_receipt and _placeholder_digest(verification_hash):
        errors.append(f"{where}: verificationHash must not be a placeholder digest")
    receipt_id = receipt.get("receiptId")
    if not isinstance(receipt_id, str) or RECEIPT_ID.fullmatch(receipt_id) is None:
        errors.append(f"{where}: receiptId must be fleet-page- plus 20 lowercase hex")
    else:
        if path.name != f"{receipt_id}.json":
            errors.append(f"{where}: filename must equal receiptId + '.json'")
        expected_id = _canonical_receipt_id(receipt)
        if expected_id is not None and receipt_id != expected_id:
            errors.append(
                f"{where}: receiptId must equal fleet-page-${{verificationHash[:20]}}"
            )

    for field in ("contentHash",):
        value = receipt.get(field)
        if not isinstance(value, str) or HASH.fullmatch(value) is None:
            errors.append(f"{where}: {field} must be a lowercase SHA-256")
        elif not fixture_receipt and _placeholder_digest(value):
            errors.append(f"{where}: {field} must not be a placeholder digest")
    source_revision = receipt.get("sourceRevision")
    if not isinstance(source_revision, str) or SOURCE_REVISION.fullmatch(source_revision) is None:
        errors.append(f"{where}: sourceRevision must be a full lowercase 40-hex commit")
    elif not fixture_receipt and _placeholder_source_revision(source_revision):
        errors.append(f"{where}: sourceRevision must not be a placeholder commit")
    if not _valid_public_id(receipt.get("runId")):
        errors.append(f"{where}: runId must be a stable public scheduler-capture alias")
    if not _valid_verifier_identity(receipt.get("checkedBy")):
        errors.append(
            f"{where}: checkedBy actual verifier must use a public agent:<slug> "
            "or job:<slug> ID"
        )
    reviewer = receipt.get("humanReviewer")
    if (
        not _valid_human_identity(reviewer)
        or (
            isinstance(reviewer, str)
            and (
                PENDING_REVIEW.search(reviewer)
                or _looks_like_agent_identity(reviewer)
                or _looks_like_generic_role_identity(reviewer)
            )
        )
    ):
        errors.append(f"{where}: humanReviewer must name the actual human reviewer")
    elif reviewer not in ALL_PUBLIC_HUMAN_REVIEWERS:
        errors.append(
            f"{where}: humanReviewer is not in {PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION}"
        )
    if receipt.get("humanReviewerRole") != "human":
        errors.append(f"{where}: humanReviewerRole must be exactly 'human'")
    if not _valid_model(receipt.get("model")):
        errors.append(f"{where}: model must be runtime-reported or literal UNKNOWN")
    if not _valid_iso_instant(receipt.get("checkedAt")):
        errors.append(f"{where}: checkedAt must be a real timezone-qualified ISO instant")
    elif _evidence_clock_is_future(receipt.get("checkedAt")):
        errors.append(f"{where}: checkedAt cannot be in the future")
    live_problem = _https_problem(receipt.get("liveUrl"))
    if live_problem:
        errors.append(f"{where}: liveUrl {live_problem}")

    try:
        json.dumps(receipt, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        errors.append(f"{where}: receipt is not JSON-serializable ({exc})")
    private_value_problems = sorted(
        {problem for value in _walk_strings(receipt) if (problem := _private_string(value))}
    )
    for problem in private_value_problems:
        errors.append(f"{where}: receipt contains a {problem}")

    if status == "verified":
        absent = sorted(SUCCESS_FIELDS - set(receipt))
        if absent:
            errors.append(f"{where}: verified receipt missing: {', '.join(absent)}")
        leaked_failure = sorted(FAILURE_FIELDS & set(receipt))
        if leaked_failure:
            errors.append(
                f"{where}: verified receipt must not carry failure-only field(s): "
                + ", ".join(leaked_failure)
            )
        if receipt.get("finalAnonymousReadback") is not True:
            errors.append(f"{where}: verified receipt requires finalAnonymousReadback=true")
        if receipt.get("browserVisibilityVerified") is not True:
            errors.append(
                f"{where}: verified receipt requires browserVisibilityVerified=true"
            )
        http_status = receipt.get("httpStatus")
        if (
            not isinstance(http_status, int)
            or isinstance(http_status, bool)
            or http_status != 200
        ):
            errors.append(f"{where}: verified receipt requires integer httpStatus=200")
        article_count = receipt.get("articleSchemaCount")
        if (
            not isinstance(article_count, int)
            or isinstance(article_count, bool)
            or article_count != 1
        ):
            errors.append(
                f"{where}: articleSchemaCount must be integer 1 (one Article owner)"
            )
        if receipt.get("extractionStart") != MARKER_START:
            errors.append(f"{where}: extractionStart is missing or changed")
        if receipt.get("extractionEnd") != MARKER_END:
            errors.append(f"{where}: extractionEnd is missing or changed")

        for field in (
            "postContentHash",
            "extractedPostContentSha256",
            "anonymousResponseSha256",
            "linkContentHash",
            "sourceManifestSha256",
        ):
            value = receipt.get(field)
            if not isinstance(value, str) or HASH.fullmatch(value) is None:
                errors.append(f"{where}: {field} must be a lowercase SHA-256")
            elif not fixture_receipt and _placeholder_digest(value):
                errors.append(f"{where}: {field} must not be a placeholder digest")
        if receipt.get("linkContentHash") != receipt.get("contentHash"):
            errors.append(f"{where}: linkContentHash must equal contentHash")

        length = receipt.get("anonymousContentLength")
        if not isinstance(length, int) or isinstance(length, bool) or length < 1:
            errors.append(f"{where}: anonymousContentLength must be a positive integer")
        counts: dict[str, int] = {}
        for field in ("configuredCount", "publicDefinitionCount", "itemListCount"):
            value = receipt.get(field)
            if not _valid_nonnegative_integer(value):
                errors.append(f"{where}: {field} must be a non-negative integer")
            else:
                counts[field] = value
        if {
            "configuredCount",
            "publicDefinitionCount",
            "itemListCount",
        } <= counts.keys():
            if counts["publicDefinitionCount"] > counts["configuredCount"]:
                errors.append(f"{where}: publicDefinitionCount exceeds configuredCount")
            if counts["itemListCount"] != counts["publicDefinitionCount"]:
                errors.append(f"{where}: itemListCount must equal publicDefinitionCount")

        if not _valid_public_id(receipt.get("linkReceiptId")):
            errors.append(f"{where}: linkReceiptId must be a stable public identifier")
        if not _valid_public_id(receipt.get("cacheBuster")):
            errors.append(f"{where}: cacheBuster must be a public-safe stable reference")
        wordpress_revision = receipt.get("wordpressRevision")
        if (
            not isinstance(wordpress_revision, str)
            or WORDPRESS_REVISION.fullmatch(wordpress_revision) is None
        ):
            errors.append(
                f"{where}: wordpressRevision must match "
                "wp:110278:<public-safe-revision>"
            )
        for field in ("articleDateModified", "wordpressModifiedAt"):
            if not _valid_iso_instant(receipt.get(field)):
                errors.append(f"{where}: {field} must be a real ISO instant")
        if receipt.get("wordpressModifiedAt") != receipt.get("articleDateModified"):
            errors.append(f"{where}: WordPress and Article modified instants differ")
        if not _valid_iso_instant(receipt.get("browserCheckedAt")):
            errors.append(f"{where}: browserCheckedAt must be a real ISO instant")
        if not _valid_verifier_identity(receipt.get("browserCheckedBy")):
            errors.append(
                f"{where}: browserCheckedBy actual verifier must use a public "
                "agent:<slug> or job:<slug> ID"
            )
        if not _valid_public_id(receipt.get("browserRunReceiptId")):
            errors.append(
                f"{where}: browserRunReceiptId must be a stable public identifier"
            )
        article_modified = _parse_iso_instant(receipt.get("articleDateModified"))
        browser_checked = _parse_iso_instant(receipt.get("browserCheckedAt"))
        receipt_checked = _parse_iso_instant(receipt.get("checkedAt"))
        if (
            article_modified is not None
            and receipt_checked is not None
            and article_modified > receipt_checked
        ):
            errors.append(f"{where}: articleDateModified cannot be later than checkedAt")
        if (
            article_modified is not None
            and browser_checked is not None
            and article_modified > browser_checked
        ):
            errors.append(f"{where}: browserCheckedAt cannot precede articleDateModified")
        if (
            browser_checked is not None
            and receipt_checked is not None
            and browser_checked > receipt_checked
        ):
            errors.append(f"{where}: browserCheckedAt cannot be later than checkedAt")

    elif status == "verification-failed":
        absent = sorted(FAILURE_FIELDS - set(receipt))
        if absent:
            errors.append(f"{where}: failed receipt missing: {', '.join(absent)}")
        leaked_success = sorted(SUCCESS_FIELDS & set(receipt))
        if leaked_success:
            errors.append(
                f"{where}: failed receipt must omit success-only field(s): "
                + ", ".join(leaked_success)
            )
        failure_contract = (
            receipt.get("failureStage"),
            receipt.get("failureCode"),
            receipt.get("failureDetail"),
        )
        if failure_contract not in FAILURE_CONTRACTS:
            errors.append(
                f"{where}: failureStage/failureCode/failureDetail must equal one "
                "approved sanitized public failure template"
            )

    return errors


def _source_binding_errors(
    receipt: object,
    path: Path,
    manifests: dict[str, tuple[dict, Path, str]],
    registries: dict[str, tuple[dict, Path, bytes]] | None = None,
) -> list[str]:
    if not isinstance(receipt, dict) or receipt.get("status") not in STATUSES:
        return []
    where = path.name
    source_revision = receipt.get("sourceRevision")
    if not isinstance(source_revision, str):
        return []
    companion = manifests.get(source_revision)
    if companion is None:
        return [
            f"{where}: receipt has no sanitized source manifest for "
            f"sourceRevision {source_revision!r}"
        ]
    manifest, manifest_path, manifest_sha256 = companion
    if not isinstance(manifest, dict):
        return [f"{where}: sanitized source manifest must be a JSON object"]
    errors = _receipt_registry_binding_errors(
        receipt, path, manifest, registries or {}
    )
    if receipt.get("status") != "verified":
        return errors
    if receipt.get("sourceManifestSha256") != manifest_sha256:
        errors.append(
            f"{where}: sourceManifestSha256 does not match exact bytes of "
            f"sources/{manifest_path.name}"
        )
    for receipt_field, manifest_field in (
        ("sourceRevision", "sourceRevision"),
        ("configuredCount", "configuredCount"),
        ("publicDefinitionCount", "publicDefinitionCount"),
    ):
        if receipt.get(receipt_field) != manifest.get(manifest_field):
            errors.append(
                f"{where}: {receipt_field} does not match sanitized source manifest"
            )
    return errors


def _ledger_namespace_errors(directory: Path = RECEIPTS_DIR) -> list[str]:
    """Reject files the strict public ledger contract does not read and validate."""
    errors: list[str] = []
    try:
        root_stat = directory.lstat()
    except OSError as exc:
        return [f"receipt ledger cannot be inspected: {exc}"]
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        return ["receipt ledger root must be a real, non-symlink directory"]

    for current_name, directory_names, file_names in os.walk(
        directory, topdown=True, followlinks=False
    ):
        current = Path(current_name)
        for name in list(directory_names):
            item = current / name
            relative = item.relative_to(directory).as_posix()
            try:
                item_stat = item.lstat()
            except OSError as exc:
                errors.append(f"{relative}: cannot inspect ledger path: {exc}")
                directory_names.remove(name)
                continue
            if stat.S_ISLNK(item_stat.st_mode):
                errors.append(f"{relative}: ledger paths must not be symlinks")
                directory_names.remove(name)
            elif not stat.S_ISDIR(item_stat.st_mode):
                errors.append(f"{relative}: expected a real directory")
                directory_names.remove(name)
            elif relative not in LEDGER_DIRECTORIES:
                errors.append(f"{relative}: unexpected directory in strict ledger namespace")
                directory_names.remove(name)

        for name in file_names:
            item = current / name
            relative = item.relative_to(directory).as_posix()
            try:
                item_stat = item.lstat()
            except OSError as exc:
                errors.append(f"{relative}: cannot inspect ledger path: {exc}")
                continue
            if stat.S_ISLNK(item_stat.st_mode):
                errors.append(f"{relative}: ledger paths must not be symlinks")
                continue
            if not stat.S_ISREG(item_stat.st_mode):
                errors.append(f"{relative}: ledger paths must be regular files")
                continue
            allowed = (
                relative in LEDGER_STATIC_FILES
                or LEDGER_RECEIPT_PATH.fullmatch(relative) is not None
                or LEDGER_SOURCE_PATH.fullmatch(relative) is not None
                or LEDGER_IDENTITY_REGISTRY_PATH.fullmatch(relative) is not None
            )
            if not allowed:
                errors.append(f"{relative}: unexpected file in strict ledger namespace")
    return errors


def validate_directory(directory: Path = RECEIPTS_DIR) -> list[str]:
    errors: list[str] = []
    is_contract_directory = directory.resolve() == RECEIPTS_DIR.resolve()
    if is_contract_directory:
        errors.extend(_ledger_namespace_errors(directory))
        errors.extend(_schema_contract_errors(directory))
        errors.extend(_source_schema_contract_errors(SOURCES_DIR))

    registries: dict[str, tuple[dict, Path, bytes]] = {}
    if is_contract_directory:
        for path in sorted(IDENTITY_REGISTRIES_DIR.glob("*.json")):
            try:
                raw = _read_bounded_regular_bytes(path, IDENTITY_REGISTRIES_DIR)
                digest = hashlib.sha256(raw).hexdigest()
                registry = parse_identity_registry_bytes(raw)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
                errors.append(
                    f"identity-registries/{path.name}: cannot parse registry: {exc}"
                )
                continue
            if path.name != f"{digest}.json":
                errors.append(
                    f"identity-registries/{path.name}: filename must equal exact-byte SHA-256"
                )
                continue
            registries[digest] = (registry, path, raw)
        try:
            discovery_raw = _read_bounded_regular_bytes(
                RECEIPTS_DIR / "public-identity-registry.json", RECEIPTS_DIR
            )
            discovery = parse_identity_registry_bytes(discovery_raw)
            discovery_hash = hashlib.sha256(discovery_raw).hexdigest()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            errors.append(f"public-identity-registry.json: cannot parse registry: {exc}")
        else:
            if discovery_hash != IDENTITY_REGISTRY_SHA256:
                errors.append(
                    "public-identity-registry.json: imported registry hash is stale"
                )
            artifact = registries.get(discovery_hash)
            if artifact is None or artifact[2] != discovery_raw:
                errors.append(
                    "public-identity-registry.json: exact content-addressed registry artifact is missing"
                )
            if discovery != IDENTITY_REGISTRY_DOCUMENT:
                errors.append(
                    "public-identity-registry.json: parsed registry differs from imported contract"
                )

    manifests: dict[str, tuple[dict, Path, str]] = {}
    if is_contract_directory:
        for path in sorted(SOURCES_DIR.glob("*.json")):
            if path.name == SOURCE_SCHEMA_FILE:
                continue
            try:
                raw = _read_bounded_regular_bytes(path, SOURCES_DIR)
                manifest = _loads_json(raw.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
                errors.append(f"sources/{path.name}: cannot parse JSON: {exc}")
                continue
            manifest_errors = validate_source_manifest(manifest, path)
            manifest_errors.extend(
                _source_registry_binding_errors(manifest, path, registries)
            )
            errors.extend(manifest_errors)
            if not manifest_errors and isinstance(manifest, dict):
                manifests[path.stem] = (
                    manifest,
                    path,
                    hashlib.sha256(raw).hexdigest(),
                )

    for path in sorted(directory.glob("*.json")):
        if path.name in {
            SCHEMA_FILE,
            "identity-registry.schema.json",
            "public-identity-registry.json",
        }:
            continue
        try:
            receipt = _load_json(path, directory)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            RecursionError,
        ) as exc:
            errors.append(f"{path.name}: cannot parse JSON: {exc}")
            continue
        errors.extend(validate_receipt(receipt, path))
        errors.extend(_source_binding_errors(receipt, path, manifests, registries))

    if is_contract_directory:
        golden_manifests: dict[str, tuple[dict, Path, str]] = {}
        try:
            golden_source_raw = _read_bounded_regular_bytes(
                GOLDEN_SOURCE, RECEIPTS_DIR
            )
            golden_source = _loads_json(golden_source_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            errors.append(
                f"examples/sources/{GOLDEN_SOURCE.name}: cannot parse JSON: {exc}"
            )
        else:
            golden_source_errors = validate_source_manifest(
                golden_source, GOLDEN_SOURCE, "examples/sources"
            )
            golden_source_errors.extend(
                _source_registry_binding_errors(
                    golden_source, GOLDEN_SOURCE, registries
                )
            )
            errors.extend(golden_source_errors)
            if not golden_source_errors and isinstance(golden_source, dict):
                golden_manifests[GOLDEN_SOURCE.stem] = (
                    golden_source,
                    GOLDEN_SOURCE,
                    hashlib.sha256(golden_source_raw).hexdigest(),
                )
        try:
            golden = _load_json(GOLDEN_RECEIPT, RECEIPTS_DIR)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            RecursionError,
        ) as exc:
            errors.append(f"{GOLDEN_RECEIPT.relative_to(ROOT)}: cannot parse golden receipt: {exc}")
        else:
            errors.extend(validate_receipt(golden, GOLDEN_RECEIPT))
            errors.extend(
                _source_binding_errors(
                    golden, GOLDEN_RECEIPT, golden_manifests, registries
                )
            )
    return errors


def _git_diff_paths(
    base_ref: str, diff_filter: str, root: Path
) -> tuple[list[str], str | None]:
    command = [
        "git",
        "diff",
        "--no-renames",
        "--name-only",
        f"--diff-filter={diff_filter}",
        base_ref,
        "--",
        "receipts/agent-fleet",
    ]
    completed = subprocess.run(
        command, cwd=root, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        return [], f"cannot compare receipts with {base_ref!r}: {detail}"
    return completed.stdout.splitlines(), None


def _immutable_evidence_path(path: str) -> bool:
    prefix = "receipts/agent-fleet/"
    if not path.startswith(prefix):
        return False
    relative = path[len(prefix) :]
    return bool(
        LEDGER_RECEIPT_PATH.fullmatch(relative)
        or LEDGER_SOURCE_PATH.fullmatch(relative)
        or LEDGER_IDENTITY_REGISTRY_PATH.fullmatch(relative)
        or (
            "/" not in relative
            and relative.endswith(".json")
            and relative
            not in {
                SCHEMA_FILE,
                "identity-registry.schema.json",
                "public-identity-registry.json",
            }
        )
    )


def _intermediate_history_errors(base_ref: str, root: Path) -> list[str]:
    """Reject immutable-evidence mutations hidden by a later restoring commit."""

    revisions = subprocess.run(
        ["git", "rev-list", "--reverse", "--topo-order", f"{base_ref}..HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if revisions.returncode:
        detail = revisions.stderr.strip() or revisions.stdout.strip()
        return [f"cannot inspect intermediate receipt history: {detail}"]
    errors: list[str] = []
    for revision in revisions.stdout.splitlines():
        if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            return ["intermediate receipt history returned a malformed commit ID"]
        changed = subprocess.run(
            [
                "git", "diff-tree", "--root", "-m", "--no-commit-id",
                "--no-renames", "--name-status", "-r", revision, "--",
                "receipts/agent-fleet",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if changed.returncode:
            detail = changed.stderr.strip() or changed.stdout.strip()
            errors.append(
                f"cannot inspect receipt changes in intermediate commit {revision}: {detail}"
            )
            continue
        for line in changed.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) != 2:
                errors.append(
                    f"intermediate commit {revision} returned malformed receipt change metadata"
                )
                continue
            status, path = fields
            if status != "A" and _immutable_evidence_path(path):
                errors.append(
                    "merged public evidence is append-only; intermediate commit "
                    f"{revision} {status} {path}"
                )
    return sorted(set(errors))


def _resolve_base_commit(base_ref: str, root: Path) -> tuple[str | None, str | None]:
    """Resolve a user-supplied ref once, without letting it become a git option."""

    if (
        not isinstance(base_ref, str)
        or not base_ref
        or len(base_ref) > 200
        or base_ref.startswith("-")
        or any(character.isspace() or ord(character) < 32 for character in base_ref)
    ):
        return None, "base ref must be a non-option, single-token git revision"
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{base_ref}^{{commit}}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    commit = completed.stdout.strip()
    if completed.returncode or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        detail = completed.stderr.strip() or completed.stdout.strip() or "not a commit"
        return None, f"cannot resolve base ref {base_ref!r} to one commit: {detail}"
    return commit, None


def _base_regular_blob(base_ref: str, relative_path: str, root: Path) -> tuple[bytes | None, str | None]:
    """Read one regular git blob without consulting the mutable worktree path."""

    listed = subprocess.run(
        ["git", "ls-tree", "-z", base_ref, "--", relative_path],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if listed.returncode:
        detail = listed.stderr.decode("utf-8", "replace").strip()
        return None, f"cannot inspect {relative_path} at {base_ref!r}: {detail}"
    records = [record for record in listed.stdout.split(b"\0") if record]
    if not records:
        return None, None
    if len(records) != 1 or b"\t" not in records[0]:
        return None, f"{relative_path}: base-ref entry is ambiguous"
    metadata, recorded_path = records[0].split(b"\t", 1)
    parts = metadata.split()
    if (
        len(parts) != 3
        or parts[0] not in {b"100644", b"100755"}
        or parts[1] != b"blob"
        or recorded_path.decode("utf-8", "replace") != relative_path
    ):
        return None, f"{relative_path}: base-ref entry must be a regular git blob"
    shown = subprocess.run(
        ["git", "show", f"{base_ref}:{relative_path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if shown.returncode:
        detail = shown.stderr.decode("utf-8", "replace").strip()
        return None, f"cannot read {relative_path} at {base_ref!r}: {detail}"
    if len(shown.stdout) > MAX_LEDGER_FILE_BYTES:
        return None, f"{relative_path}: base-ref blob exceeds the public ledger limit"
    return shown.stdout, None


def _registry_history_errors(base_ref: str, root: Path) -> list[str]:
    errors: list[str] = []
    contracts = (
        (
            IDENTITY_REGISTRY_RELATIVE_PATH,
            registry_history_problem,
        ),
        (
            DOCUMENTATION_ACTOR_REGISTRY_RELATIVE_PATH,
            documentation_actor_registry_history_problem,
        ),
    )
    for relative_path, comparator in contracts:
        previous, problem = _base_regular_blob(base_ref, relative_path, root)
        if problem:
            errors.append(problem)
            continue
        if previous is None:
            continue
        current_path = root / relative_path
        try:
            current = _read_bounded_regular_bytes(current_path, root)
        except (OSError, ValueError) as exc:
            errors.append(f"{relative_path}: current registry cannot be read safely: {exc}")
            continue
        history_problem = comparator(previous, current)
        if history_problem:
            errors.append(f"{relative_path}: {history_problem}")
    return errors


def _base_source_manifest_errors(
    base_ref: str, source_path: str, root: Path
) -> list[str]:
    """Load a companion from the base tree without following worktree symlinks."""
    listed = subprocess.run(
        ["git", "ls-tree", "-z", base_ref, "--", source_path],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if listed.returncode:
        detail = listed.stderr.decode("utf-8", "replace").strip()
        return [f"{source_path}: cannot inspect base-ref companion: {detail}"]
    records = [record for record in listed.stdout.split(b"\0") if record]
    if len(records) != 1 or b"\t" not in records[0]:
        return [
            f"{source_path}: source companion must already exist in base ref "
            f"{base_ref!r} before its publication receipt is added"
        ]
    metadata, recorded_path = records[0].split(b"\t", 1)
    parts = metadata.split()
    if (
        len(parts) != 3
        or parts[0] not in {b"100644", b"100755"}
        or parts[1] != b"blob"
        or recorded_path.decode("utf-8", "replace") != source_path
    ):
        return [
            f"{source_path}: base-ref source companion must be a regular git blob, "
            "not a symlink or tree"
        ]

    shown = subprocess.run(
        ["git", "show", f"{base_ref}:{source_path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if shown.returncode:
        detail = shown.stderr.decode("utf-8", "replace").strip()
        return [f"{source_path}: cannot read base-ref companion: {detail}"]
    try:
        manifest = _loads_json(shown.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return [f"{source_path}: base-ref source companion cannot parse JSON: {exc}"]
    source = Path(source_path)
    return [
        f"{source_path}: invalid base-ref source companion: {problem}"
        for problem in validate_source_manifest(manifest, source)
    ]


def _added_receipt_source_revision(
    added_path: str, root: Path
) -> tuple[str | None, list[str]]:
    ledger = root / "receipts" / "agent-fleet"
    path = root / added_path
    try:
        receipt = _load_json(path, ledger)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return None, [f"{added_path}: added receipt cannot parse safely: {exc}"]
    if not isinstance(receipt, dict):
        return None, [f"{added_path}: added receipt must be a JSON object"]
    receipt_errors = validate_receipt(receipt, path)
    if receipt_errors:
        return None, [
            f"{added_path}: added receipt is invalid: {problem}"
            for problem in receipt_errors
        ]
    source_revision = receipt.get("sourceRevision")
    if (
        not isinstance(source_revision, str)
        or SOURCE_REVISION.fullmatch(source_revision) is None
    ):
        return None, [
            f"{added_path}: added receipt lacks a valid 40-hex sourceRevision"
        ]
    return source_revision, []


def _added_source_registry_errors(
    base_ref: str, added_path: str, root: Path
) -> list[str]:
    """Require a new source to select the current, precommitted registry bytes."""

    path = root / added_path
    try:
        manifest = _load_json(path, root / "receipts" / "agent-fleet" / "sources")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return [f"{added_path}: added source manifest cannot parse safely: {exc}"]
    if not isinstance(manifest, dict):
        return [f"{added_path}: added source manifest must be a JSON object"]
    problems = validate_source_manifest(manifest, path)
    if problems:
        return [f"{added_path}: added source manifest is invalid: {item}" for item in problems]
    expected = {
        "actorRegistryVersion": PUBLIC_ACTOR_REGISTRY_VERSION,
        "humanReviewerRegistryVersion": PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION,
        "modelRegistryVersion": PUBLIC_MODEL_REGISTRY_VERSION,
        "identityRegistrySha256": IDENTITY_REGISTRY_SHA256,
    }
    errors = [
        f"{added_path}: new source manifest must select current {field}={value!r}"
        for field, value in expected.items()
        if manifest.get(field) != value
    ]
    registry_hash = manifest.get("identityRegistrySha256")
    if isinstance(registry_hash, str) and HASH.fullmatch(registry_hash):
        relative = (
            "receipts/agent-fleet/identity-registries/"
            + registry_hash
            + ".json"
        )
        prior, problem = _base_regular_blob(base_ref, relative, root)
        if problem:
            errors.append(problem)
        elif prior is None:
            errors.append(
                f"{relative}: exact identity registry must already exist in base ref "
                f"{base_ref!r} before its source manifest is added"
            )
        else:
            digest = hashlib.sha256(prior).hexdigest()
            if digest != registry_hash:
                errors.append(f"{relative}: base-ref registry bytes do not match filename")
            else:
                try:
                    parse_identity_registry_bytes(prior)
                except (UnicodeError, ValueError, json.JSONDecodeError, RecursionError) as exc:
                    errors.append(f"{relative}: base-ref registry is invalid: {exc}")
    return errors


def append_only_errors(base_ref: str, root: Path = ROOT) -> list[str]:
    resolved_base, problem = _resolve_base_commit(base_ref, root)
    if problem or resolved_base is None:
        return [problem or f"cannot resolve base ref {base_ref!r}"]
    base_ref = resolved_base
    errors = _intermediate_history_errors(base_ref, root)
    changed_paths, problem = _git_diff_paths(base_ref, "DMRTUXB", root)
    if problem:
        return errors + [problem]
    receipt_prefix = "receipts/agent-fleet/"
    changed_receipts = [path for path in changed_paths if _immutable_evidence_path(path)]
    errors.extend(
        f"merged public evidence is append-only; cannot modify/delete/rename {path}"
        for path in changed_receipts
    )
    errors.extend(_registry_history_errors(base_ref, root))

    added_paths, problem = _git_diff_paths(base_ref, "A", root)
    if problem:
        errors.append(problem)
        return errors
    for added_path in added_paths:
        if not added_path.startswith(receipt_prefix):
            continue
        relative = added_path[len(receipt_prefix) :]
        if LEDGER_SOURCE_PATH.fullmatch(relative) is not None:
            errors.extend(_added_source_registry_errors(base_ref, added_path, root))
            continue
        if LEDGER_RECEIPT_PATH.fullmatch(relative) is None:
            continue
        source_revision, receipt_errors = _added_receipt_source_revision(
            added_path, root
        )
        errors.extend(receipt_errors)
        if source_revision is None:
            continue
        source_path = f"{receipt_prefix}sources/{source_revision}.json"
        errors.extend(_base_source_manifest_errors(base_ref, source_path, root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-ref",
        help="also reject modification/deletion/rename of receipt JSON versus this ref",
    )
    args = parser.parse_args()
    errors = validate_directory()
    if args.base_ref:
        errors.extend(append_only_errors(args.base_ref))
    if errors:
        print(f"Agent-fleet receipt validation failed with {len(set(errors))} error(s):")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    count = sum(
        1
        for path in RECEIPTS_DIR.glob("*.json")
        if LEDGER_RECEIPT_PATH.fullmatch(path.name) is not None
    )
    print(
        "Agent-fleet receipt validation passed: "
        f"{count} production public receipt(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
