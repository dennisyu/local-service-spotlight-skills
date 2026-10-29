#!/usr/bin/env python3
"""Check portable setup files and recorded handoff consistency, without network access.

Passing this tool does not prove remote reads, identities, permissions, installation,
runtime obedience, independent judgment, or an actual business outcome.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_FILES = (
    "AGENTS.md",
    "COORDINATION.md",
    "status/JOBS.md",
    "status/NOW.md",
    "agent-notes/README.md",
    "handoff.example.json",
    "handoff.schema.json",
)
STATUSES = {"NOT_DELIVERED", "DELIVERED", "VERIFIED", "BLOCKED"}
RESULTS = {"PASS", "FAIL", "NOT_CHECKED"}
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
REFERENCE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", re.MULTILINE)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _choice(value: object, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def _local_path(root: Path, value: object, label: str, errors: list[str]) -> Path | None:
    """Resolve an explicitly local index path, rejecting traversal and symlink escapes."""
    if not _nonempty(value):
        errors.append(f"{label} must be a non-empty local path")
        return None
    assert isinstance(value, str)
    try:
        parsed = urlsplit(value)
        relative = Path(unquote(parsed.path))
        destination = (root / relative).resolve()
    except (ValueError, OSError, RuntimeError):
        errors.append(f"{label} contains an invalid local path")
        return None
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        errors.append(f"{label} must be a local path without a query or fragment")
        return None
    if relative.is_absolute():
        errors.append(f"{label} must be relative to the repository")
        return None
    if not destination.is_relative_to(root.resolve()):
        errors.append(f"{label} escapes the allowed root")
        return None
    return destination


def _markdown_links(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    try:
        if not path.resolve().is_relative_to(root.resolve()):
            return [f"{path.relative_to(root)} escapes the allowed root"]
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, RuntimeError, ValueError):
        return [f"cannot read setup Markdown: {path.relative_to(root)}"]
    # Code examples are not navigable Markdown links.
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", source)
    destinations = [match.group(1) for match in LINK.finditer(text)]
    destinations.extend(match.group(1) for match in REFERENCE.finditer(text))
    for value in destinations:
        value = value.removeprefix("<").removesuffix(">")
        try:
            parsed = urlsplit(value)
            target_path = Path(unquote(parsed.path))
            target = (path.parent / target_path).resolve()
        except (ValueError, OSError, RuntimeError):
            errors.append(f"{path.relative_to(root)} contains an invalid link path")
            continue
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        if target_path.is_absolute() or not target.is_relative_to(root.resolve()):
            errors.append(f"{path.relative_to(root)} link escapes the allowed root: {value}")
        elif not target.exists():
            errors.append(f"{path.relative_to(root)} has a missing local link target: {value}")
    return errors


def _read_json(path: Path, errors: list[str]) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read JSON {path.name}: {exc}")
        return None


def validate_source(root: Path) -> list[str]:
    """Validate the public machine index, its targets, and setup Markdown links."""
    root = root.resolve()
    errors: list[str] = []
    index = _read_json(root / "agent-setup.json", errors)
    if not isinstance(index, dict):
        if not errors:
            errors.append("agent-setup.json must contain an object")
        return errors
    if type(index.get("schema_version")) is not int or index["schema_version"] != 1:
        errors.append("agent-setup.json schema_version must be 1")
    candidates: set[Path] = set()
    entrypoint = _local_path(root, index.get("entrypoint"), "entrypoint", errors)
    if entrypoint is not None:
        if not entrypoint.is_file():
            errors.append("entrypoint must name an existing file")
        else:
            candidates.add(entrypoint)
    docs = index.get("docs")
    if not isinstance(docs, list) or not docs:
        errors.append("docs must be a non-empty array of local paths")
    else:
        for i, value in enumerate(docs):
            target = _local_path(root, value, f"docs[{i}]", errors)
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"docs[{i}] must name an existing file: {value}")
            else:
                candidates.add(target)
    template_dir = _local_path(root, index.get("templates_dir"), "templates_dir", errors)
    if template_dir is not None:
        if not template_dir.is_dir():
            errors.append("templates_dir must name an existing directory")
        else:
            errors.extend(validate_workspace(template_dir))
            candidates.update(template_dir.rglob("*.md"))
    for path in sorted(candidates):
        if path.suffix.lower() == ".md":
            errors.extend(_markdown_links(path, root))
    return sorted(set(errors))


def validate_workspace(root: Path) -> list[str]:
    """Check starter files; this does not enforce claims, locks, or access controls."""
    root = root.resolve()
    errors: list[str] = []
    for name in WORKSPACE_FILES:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            errors.append(f"workspace file escapes the allowed root: {name}")
        elif not path.is_file():
            errors.append(f"workspace is missing {name}")
    return errors


def _timestamp(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO timestamp with timezone")
        return
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timezone missing")
    except ValueError:
        errors.append(f"{label} must be an ISO timestamp with timezone")


def validate_receipt(receipt: object, *, require_verified: bool = False) -> list[str]:
    """Check authored evidence fields for internal consistency, never their truth."""
    if not isinstance(receipt, dict):
        return ["receipt must contain an object"]
    errors: list[str] = []
    required = (
        "schema_version", "exercise", "task_id", "source_revision", "scope", "acceptance",
        "producer", "receiver", "artifact", "receiver_ack", "verification", "status",
    )
    for field in required:
        if field not in receipt:
            errors.append(f"receipt is missing {field}")
    if type(receipt.get("schema_version")) is not int or receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")
    if not _choice(receipt.get("exercise"), {"practice", "real"}):
        errors.append("exercise must be practice or real")
    for field in ("task_id", "source_revision", "scope", "acceptance"):
        if not _nonempty(receipt.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in ("producer", "receiver"):
        identity = receipt.get(field)
        if not isinstance(identity, dict):
            errors.append(f"{field} must contain agent and runtime")
            continue
        for key in ("agent", "runtime"):
            if not _nonempty(identity.get(key)):
                errors.append(f"{field}.{key} must be a non-empty string")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("artifact must contain ref and revision")
        artifact = {}
    for field in ("ref", "revision"):
        if not _nonempty(artifact.get(field)):
            errors.append(f"artifact.{field} must be a non-empty string")
    status = receipt.get("status")
    if not _choice(status, STATUSES):
        errors.append("status must be NOT_DELIVERED, DELIVERED, VERIFIED, or BLOCKED")
    ack = receipt.get("receiver_ack")
    if ack is not None:
        if not isinstance(ack, dict):
            errors.append("receiver_ack must be an object or null")
        else:
            for field in ("artifact_ref", "artifact_revision", "evidence"):
                if not _nonempty(ack.get(field)):
                    errors.append(f"receiver_ack.{field} must be a non-empty string")
            if ack.get("artifact_ref") != artifact.get("ref"):
                errors.append("receiver_ack artifact_ref must match artifact.ref exactly")
            if ack.get("artifact_revision") != artifact.get("revision"):
                errors.append("receiver_ack artifact_revision must match artifact.revision exactly")
            _timestamp(ack.get("observed_at"), "receiver_ack.observed_at", errors)
    elif _choice(status, {"DELIVERED", "VERIFIED"}):
        errors.append(f"{status} requires receiver_ack for the exact artifact revision")
    verification = receipt.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification must be an object")
        verification = {}
    for field in ("reviewer", "result", "evidence", "observed_at"):
        if field not in verification:
            errors.append(f"verification is missing {field}")
    if not _nonempty(verification.get("reviewer")):
        errors.append("verification.reviewer must be a non-empty string")
    result = verification.get("result")
    if not _choice(result, RESULTS):
        errors.append("verification.result must be PASS, FAIL, or NOT_CHECKED")
    if _choice(result, {"PASS", "FAIL"}):
        if not _nonempty(verification.get("evidence")):
            errors.append(f"verification {result} requires non-empty evidence")
        _timestamp(verification.get("observed_at"), "verification.observed_at", errors)
    elif result == "NOT_CHECKED":
        if not isinstance(verification.get("evidence"), str):
            errors.append("verification.evidence must be a string")
        if verification.get("observed_at") is not None:
            _timestamp(verification.get("observed_at"), "verification.observed_at", errors)
    if status == "VERIFIED":
        if result != "PASS":
            errors.append("VERIFIED requires verification.result PASS")
        producer = receipt.get("producer")
        if isinstance(producer, dict) and verification.get("reviewer") == producer.get("agent"):
            errors.append("VERIFIED requires a reviewer different from producer.agent")
    if require_verified and status != "VERIFIED":
        errors.append(f"terminal gate requires VERIFIED; recorded status is {status}")
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="check an existing starter workspace")
    parser.add_argument("--receipt", type=Path, help="check a handoff JSON receipt")
    parser.add_argument("--require-verified", action="store_true", help="fail unless the receipt records VERIFIED")
    args = parser.parse_args(argv)
    if args.require_verified and args.receipt is None:
        parser.error("--require-verified requires --receipt")
    errors: list[str] = []
    if args.workspace is None and args.receipt is None:
        errors.extend(validate_source(ROOT))
    if args.workspace is not None:
        errors.extend(validate_workspace(args.workspace))
    receipt = None
    if args.receipt is not None:
        receipt = _read_json(args.receipt, errors)
        errors.extend(validate_receipt(receipt, require_verified=args.require_verified))
    if errors:
        print("Agent setup check FAILED:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print("Agent setup consistency check PASSED.")
    if isinstance(receipt, dict):
        print(f"Recorded exercise: {receipt['exercise']}; recorded status: {receipt['status']}.")
        if receipt["status"] != "VERIFIED":
            print("This receipt does not record verified completion.")
    print("Checks recorded fields and local files only; does not prove remote reads, runtime behavior, or consensus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
