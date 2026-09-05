"""Strict public identity registries shared by fleet rails and receipts.

Fleet evidence selects immutable registry versions through a sanitized source
manifest.  A later current version may revoke an identity, but published
versions and their members cannot be removed or repurposed.  Generic public
documentation actors use a separate tracked append-only registry rather than
being inferred from the mutable ``skills/`` directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from pathlib import Path

try:
    from .public_value_safety import public_value_problem
except ImportError:  # pragma: no cover - direct script import
    from public_value_safety import public_value_problem  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_REGISTRY_PATH = (
    ROOT / "receipts" / "agent-fleet" / "public-identity-registry.json"
)
IDENTITY_REGISTRY_RELATIVE_PATH = "receipts/agent-fleet/public-identity-registry.json"
DOCUMENTATION_ACTOR_REGISTRY_PATH = (
    ROOT / "standards" / "public-documentation-actor-registry.json"
)
DOCUMENTATION_ACTOR_REGISTRY_RELATIVE_PATH = (
    "standards/public-documentation-actor-registry.json"
)
IDENTITY_REGISTRY_KEYS = {
    "schemaVersion",
    "currentActorRegistry",
    "currentHumanReviewerRegistry",
    "currentModelRegistry",
    "actorRegistries",
    "humanReviewerRegistries",
    "modelRegistries",
}
REGISTRY_VERSION = re.compile(
    r"fleet-public-(?:actors|human-reviewers|models)-v[1-9][0-9]*"
)
ACTOR_ID = re.compile(r"(?:agent|job):[a-z0-9][a-z0-9._-]{2,119}")
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:+-]{0,119}")
DOCUMENTATION_REGISTRY_VERSION = re.compile(
    r"public-documentation-actors-v[1-9][0-9]*"
)
STRONG_PLACEHOLDER_TOKENS = {
    "anonymous", "bot", "nobody", "none", "null", "pending", "placeholder",
    "robot", "tbd", "todo", "unavailable", "unassigned", "unknown",
    "unreviewed",
}
GENERIC_HUMAN_REGISTRY_VALUES = {
    "anonymous", "chatgpt", "claude", "codex", "deepseek", "gemini", "gpt",
    "human reviewer", "llama", "not disclosed", "qwen", "review required",
    "someone", "system", "unknown", "unassigned", "the reviewer",
}
GENERIC_MODEL_REGISTRY_VALUES = {
    "ai", "assistant", "bot", "default", "default model", "language model",
    "llm", "model", "runtime", "runtime model", "some model", "unknown",
    "unspecified", "unspecified model",
}
GENERIC_ACTOR_SLUG_TOKENS = {
    "agent", "audit", "bot", "cron", "current", "default", "human", "job",
    "latest", "model", "placeholder", "production", "reviewer", "someone",
    "system", "unknown",
}
GENERIC_MODEL_REGISTRY_TOKENS = {
    "ai", "assistant", "bot", "chatbot", "current", "default", "example",
    "language", "latest", "llm", "model", "placeholder", "production",
    "runtime", "some", "unknown", "unspecified", "vendor",
}
PLACEHOLDER_HUMAN_TOKENS = STRONG_PLACEHOLDER_TOKENS | {
    "example", "system", "test",
}
HUMAN_ROLE_TOKENS = {
    "a", "approved", "approver", "assigned", "audit", "board", "by",
    "committee", "compliance", "control", "department", "designated",
    "desk", "editorial", "external", "function", "group", "human",
    "independent", "lead", "member", "name", "named", "officer", "on",
    "party", "person", "qa", "quality", "review", "reviewed", "reviewer",
    "staff", "specialist", "team", "the", "third", "user", "verification",
}
FATAL_ACTOR_SLUG_TOKENS = STRONG_PLACEHOLDER_TOKENS | {
    "cron", "current", "default", "example", "latest", "production",
    "redacted", "reviewer", "sample", "someone", "system", "test",
}
FATAL_MODEL_REGISTRY_TOKENS = STRONG_PLACEHOLDER_TOKENS | {
    "current", "default", "example", "production", "some", "unspecified",
}
LEGACY_MUTABLE_MODEL_IDS = {"codestral:latest", "devstral:latest"}


def _reject_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def _has_disallowed_public_character(value: str) -> bool:
    return any(
        unicodedata.category(character).startswith("C")
        or "\u180b" <= character <= "\u180d"
        or "\ufe00" <= character <= "\ufe0f"
        or "\U000e0100" <= character <= "\U000e01ef"
        for character in value
    )


def _identity_tokens(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)


def _reserved_identity_token(token: str) -> bool:
    """Numeric/version suffixes cannot disguise a reserved identity word."""

    undecorated = re.sub(r"(?:v)?[0-9]+$", "", token)
    return (
        token in STRONG_PLACEHOLDER_TOKENS
        or undecorated in STRONG_PLACEHOLDER_TOKENS
    )


def _registry_value_problem(value: str) -> str:
    """Return a high-signal privacy/canonicality problem for a public ID."""

    if value != unicodedata.normalize("NFKC", value):
        return "is not Unicode NFKC-canonical"
    if value != " ".join(value.split()):
        return "does not use canonical single ASCII whitespace"
    if _has_disallowed_public_character(value):
        return "contains a Unicode control or variation character"
    if "://" in value:
        return "contains a URL"
    problem = public_value_problem(value)
    return problem or ""


def _valid_registry_human_name(value: str) -> bool:
    tokens = [token for token in re.findall(r"[^\W\d_]+", value.casefold(), re.UNICODE)]
    identity_tokens = _identity_tokens(value)
    folded = " ".join(tokens)
    genuine_name_tokens = [
        token for token in tokens if token not in HUMAN_ROLE_TOKENS
    ]
    unspaced_non_latin_name = (
        len(tokens) == 1
        and bool(tokens)
        and any(ord(character) > 127 for character in value)
    )
    return (
        value.casefold() not in GENERIC_HUMAN_REGISTRY_VALUES
        and folded not in {
            "some one", "no one", "not assigned", "not yet reviewed",
            "not yet review", "review pending",
            "reviewer tbd", "review required person", "not disclosed person",
            "human reviewer name", "deep seek",
        }
        and not any(token in PLACEHOLDER_HUMAN_TOKENS for token in tokens)
        and not any(_reserved_identity_token(token) for token in identity_tokens)
        and (len(genuine_name_tokens) >= 2 or unspaced_non_latin_name)
        and any(character.isalpha() for character in value)
        and all(
            unicodedata.category(character)[0] in {"L", "M"}
            or character == " "
            or character in {"'", "’", "-", "."}
            for character in value
        )
    )


def _version_number(version: str) -> int:
    return int(version.rsplit("-v", 1)[1])


def _valid_registry_actor(value: str) -> bool:
    if ACTOR_ID.fullmatch(value) is None:
        return False
    tokens = [token for token in re.split(r"[._-]+", value.split(":", 1)[1]) if token]
    semantic = []
    for token in tokens:
        if token.isdigit() or re.fullmatch(r"v[0-9]+", token) is not None:
            continue
        placeholder_base = re.sub(
            r"(?:v?[0-9]+)$", "", token, flags=re.IGNORECASE
        )
        semantic.append(placeholder_base or token)
    return (
        bool(semantic)
        and not any(token in FATAL_ACTOR_SLUG_TOKENS for token in semantic)
        and not all(
        token in GENERIC_ACTOR_SLUG_TOKENS for token in semantic
        )
    )


def _valid_registry_model(value: str) -> bool:
    if value.casefold() in GENERIC_MODEL_REGISTRY_VALUES:
        return False
    tokens = [token for token in re.split(r"[ ._:+-]+", value.casefold()) if token]
    semantic = [
        token
        for token in tokens
        if not token.isdigit()
        and re.fullmatch(r"v[0-9]+", token) is None
        and len(token) > 1
    ]
    return (
        bool(semantic)
        and not any(_reserved_identity_token(token) for token in _identity_tokens(value))
        and not any(token in FATAL_MODEL_REGISTRY_TOKENS for token in semantic)
        and (
            "latest" not in semantic or value.casefold() in LEGACY_MUTABLE_MODEL_IDS
        )
        and not all(
            token in GENERIC_MODEL_REGISTRY_TOKENS for token in semantic
        )
    )


def _parse_registry_bytes(payload: bytes) -> dict:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-JSON numeric constant {value!r}")

    document = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_members,
        parse_constant=reject_constant,
    )
    if not isinstance(document, dict) or set(document) != IDENTITY_REGISTRY_KEYS:
        raise ValueError("identity registry has missing or extra fields")
    if type(document.get("schemaVersion")) is not int or document["schemaVersion"] != 1:
        raise ValueError("identity registry schemaVersion must be exactly integer 1")
    for kind, prefix in (
        ("actorRegistries", "fleet-public-actors-"),
        ("humanReviewerRegistries", "fleet-public-human-reviewers-"),
        ("modelRegistries", "fleet-public-models-"),
    ):
        registries = document.get(kind)
        if not isinstance(registries, dict) or not registries:
            raise ValueError(f"identity registry {kind} must be a nonempty object")
        for version, values in registries.items():
            if (
                not isinstance(version, str)
                or REGISTRY_VERSION.fullmatch(version) is None
                or not version.startswith(prefix)
            ):
                raise ValueError(f"identity registry has invalid {kind} version")
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(value, str) for value in values)
                or values != sorted(values)
                or len(values) != len(set(values))
            ):
                raise ValueError(f"identity registry {version} must be sorted and unique")
            for value in values:
                if kind == "actorRegistries" and (
                    not _valid_registry_actor(value)
                    or bool(_registry_value_problem(value))
                ):
                    raise ValueError(f"identity registry has invalid actor ID {value!r}")
                if kind == "modelRegistries" and (
                    not 1 <= len(value) <= 120
                    or value != value.strip()
                    or MODEL_ID.fullmatch(value) is None
                    or not _valid_registry_model(value)
                    or bool(_registry_value_problem(value))
                ):
                    raise ValueError(f"identity registry has invalid model ID {value!r}")
                if kind == "humanReviewerRegistries" and (
                    not 3 <= len(value) <= 120
                    or value != value.strip()
                    or not _valid_registry_human_name(value)
                    or bool(_registry_value_problem(value))
                ):
                    raise ValueError(
                        f"identity registry has invalid human reviewer {value!r}"
                    )
    for field, kind in (
        ("currentActorRegistry", "actorRegistries"),
        ("currentHumanReviewerRegistry", "humanReviewerRegistries"),
        ("currentModelRegistry", "modelRegistries"),
    ):
        if document.get(field) not in document[kind]:
            raise ValueError(f"identity registry {field} is not defined")
        if _version_number(document[field]) != max(
            _version_number(version) for version in document[kind]
        ):
            raise ValueError(f"identity registry {field} must select the newest version")
    return document


def parse_identity_registry_bytes(payload: bytes) -> dict:
    """Parse one exact immutable fleet registry artifact."""

    return _parse_registry_bytes(payload)


def _read_registry_bytes(path: Path = IDENTITY_REGISTRY_PATH) -> bytes:
    if path.is_symlink():
        raise ValueError("identity registry must not be a symlink")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > 100_000:
            raise ValueError("identity registry is not a bounded regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(100_001)
        after = os.fstat(descriptor)
        if len(payload) > 100_000 or (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError("identity registry changed during bounded read")
        final_path = path.lstat()
        if (
            stat.S_ISLNK(final_path.st_mode)
            or final_path.st_dev != after.st_dev
            or final_path.st_ino != after.st_ino
            or final_path.st_size != after.st_size
            or final_path.st_mtime_ns != after.st_mtime_ns
        ):
            raise ValueError("identity registry path changed during bounded read")
        return payload
    finally:
        os.close(descriptor)


def registry_history_problem(previous_bytes: bytes, current_bytes: bytes) -> str:
    """Return a problem if a published registry version/member was removed."""

    try:
        previous = _parse_registry_bytes(previous_bytes)
        current = _parse_registry_bytes(current_bytes)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return f"identity registry history is unreadable: {exc}"
    for kind in ("actorRegistries", "humanReviewerRegistries", "modelRegistries"):
        for version, old_values in previous[kind].items():
            if version not in current[kind]:
                return f"identity registry removed historical version {version}"
            if current[kind][version] != old_values:
                return f"identity registry changed immutable version {version}"
    return ""


def _parse_documentation_actor_registry_bytes(payload: bytes) -> dict:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-JSON numeric constant {value!r}")

    document = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_members,
        parse_constant=reject_constant,
    )
    expected = {"schemaVersion", "currentActorRegistry", "actorRegistries"}
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError("documentation actor registry has missing or extra fields")
    if type(document.get("schemaVersion")) is not int or document["schemaVersion"] != 1:
        raise ValueError("documentation actor registry schemaVersion must be integer 1")
    registries = document.get("actorRegistries")
    if not isinstance(registries, dict) or not registries:
        raise ValueError("documentation actorRegistries must be a nonempty object")
    for version, values in registries.items():
        if (
            not isinstance(version, str)
            or DOCUMENTATION_REGISTRY_VERSION.fullmatch(version) is None
        ):
            raise ValueError("documentation actor registry has an invalid version")
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) for value in values)
            or values != sorted(values)
            or len(values) != len(set(values))
        ):
            raise ValueError(f"documentation actor registry {version} must be sorted and unique")
        if any(
            not _valid_registry_actor(value) or bool(_registry_value_problem(value))
            for value in values
        ):
            raise ValueError(
                f"documentation actor registry {version} has an invalid actor ID"
            )
    if document.get("currentActorRegistry") not in registries:
        raise ValueError("documentation currentActorRegistry is not defined")
    if _version_number(document["currentActorRegistry"]) != max(
        _version_number(version) for version in registries
    ):
        raise ValueError(
            "documentation currentActorRegistry must select the newest version"
        )
    return document


def documentation_actor_registry_history_problem(
    previous_bytes: bytes, current_bytes: bytes
) -> str:
    """Reject removal or mutation of a published documentation actor version."""

    try:
        previous = _parse_documentation_actor_registry_bytes(previous_bytes)
        current = _parse_documentation_actor_registry_bytes(current_bytes)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return f"documentation actor registry history is unreadable: {exc}"
    for version, old_values in previous["actorRegistries"].items():
        if version not in current["actorRegistries"]:
            return f"documentation actor registry removed historical version {version}"
        if current["actorRegistries"][version] != old_values:
            return f"documentation actor registry changed immutable version {version}"
    return ""


IDENTITY_REGISTRY_BYTES = _read_registry_bytes()
IDENTITY_REGISTRY_DOCUMENT = _parse_registry_bytes(IDENTITY_REGISTRY_BYTES)
IDENTITY_REGISTRY_SHA256 = hashlib.sha256(IDENTITY_REGISTRY_BYTES).hexdigest()
PUBLIC_ACTOR_REGISTRY_VERSION = IDENTITY_REGISTRY_DOCUMENT["currentActorRegistry"]
PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION = IDENTITY_REGISTRY_DOCUMENT[
    "currentHumanReviewerRegistry"
]
PUBLIC_MODEL_REGISTRY_VERSION = IDENTITY_REGISTRY_DOCUMENT["currentModelRegistry"]
PUBLIC_ACTOR_IDS = frozenset(
    IDENTITY_REGISTRY_DOCUMENT["actorRegistries"][PUBLIC_ACTOR_REGISTRY_VERSION]
)
PUBLIC_HUMAN_REVIEWERS = frozenset(
    IDENTITY_REGISTRY_DOCUMENT["humanReviewerRegistries"]
    [PUBLIC_HUMAN_REVIEWER_REGISTRY_VERSION]
)
PUBLIC_MODEL_IDS = frozenset(
    IDENTITY_REGISTRY_DOCUMENT["modelRegistries"][PUBLIC_MODEL_REGISTRY_VERSION]
)
ALL_PUBLIC_ACTOR_IDS = frozenset(
    value
    for values in IDENTITY_REGISTRY_DOCUMENT["actorRegistries"].values()
    for value in values
)
ALL_PUBLIC_HUMAN_REVIEWERS = frozenset(
    value
    for values in IDENTITY_REGISTRY_DOCUMENT["humanReviewerRegistries"].values()
    for value in values
)
ALL_PUBLIC_MODEL_IDS = frozenset(
    value
    for values in IDENTITY_REGISTRY_DOCUMENT["modelRegistries"].values()
    for value in values
)

DOCUMENTATION_ACTOR_REGISTRY_BYTES = _read_registry_bytes(
    DOCUMENTATION_ACTOR_REGISTRY_PATH
)
DOCUMENTATION_ACTOR_REGISTRY_DOCUMENT = _parse_documentation_actor_registry_bytes(
    DOCUMENTATION_ACTOR_REGISTRY_BYTES
)
PUBLIC_DOCUMENTATION_ACTOR_REGISTRY_VERSION = (
    DOCUMENTATION_ACTOR_REGISTRY_DOCUMENT["currentActorRegistry"]
)
# Generic rails do not serialize a registry version, so the current selection
# is the authorization boundary for every fresh audit. Historical version
# arrays remain immutable evidence, while a later current version may revoke an
# actor from signing new/current public documentation.
PUBLIC_DOCUMENTATION_ACTOR_IDS = frozenset(
    DOCUMENTATION_ACTOR_REGISTRY_DOCUMENT["actorRegistries"]
    [PUBLIC_DOCUMENTATION_ACTOR_REGISTRY_VERSION]
)
