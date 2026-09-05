#!/usr/bin/env python3
"""Validate a public bootstrap locally. Does not fetch, install, sync, or publish.

Exit 0: structurally valid; 1: invalid; 2: invocation error; 3: --require-ready
requested, but source/activation/rollback evidence is incomplete. Requires jsonschema.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def utc(value: str) -> datetime:
    """Parse an offset-aware RFC3339 timestamp; leap seconds are unsupported.

    Keep this check even with jsonschema format extras: optional dependencies
    must not turn malformed timestamps into comparison errors or accepted dates.
    """
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})", value):
        raise ValueError("unsupported_timestamp")
    return datetime.fromisoformat(value.replace("t", "T").replace("z", "Z").replace("Z", "+00:00"))


def public_url(value: str) -> bool:
    """Screen metadata, not DNS or destination content. No network requests."""
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        path = unquote(url.path).lower()
        if url.scheme != "https" or url.username or url.password or url.port not in (None, 443):
            return False
        if not host or host.endswith((".local", ".internal", ".localhost")):
            return False
        # Publication pointers use DNS names, never IP literals or shorthand IPs.
        if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host):
            return False
        if host in {"drive.google.com", "docs.google.com", "mail.google.com", "3.basecamp.com", "app.basecamp.com"}:
            return False  # Public release must use anonymous publication, not private work rails.
        if path.startswith("/users/"):
            return False
        if url.query:  # No signed URLs, credentials, or unstable tracking URLs in bootstrap.
            return False
        return True
    except ValueError:
        return False


def validate(data: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    schema = json.loads((ROOT / "schemas" / "public-bootstrap.schema.json").read_text())
    errors = []
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data):
        # Print paths and keywords only: malformed values may contain private material.
        errors.append(f"schema:{'/'.join(map(str, error.absolute_path)) or '$'}:{error.validator}")
    if errors:
        return {"valid_manifest": False, "ready_for_independent_review": False, "errors": sorted(set(errors)), "blockers": []}

    blockers = []
    urls = [("entrypoint", data["entrypoint"]), ("install_guide", data["install_guide"]), ("source/repository", data["source"]["repository"])]
    seen = set()
    for index, source in enumerate(data["memory"]["sources"]):
        key = f"memory/sources/{index}"
        urls.append((key, source["url"]))
        if source["id"] in seen:
            errors.append("duplicate_memory_id")
        seen.add(source["id"])
        try:
            checked, expiry = utc(source["checked_at"]), utc(source["expires_at"])
        except ValueError:
            errors.append(f"{key}:invalid_or_unsupported_timestamp")
        else:
            if checked > now or expiry <= checked:
                errors.append(f"{key}:invalid_freshness_window")
            if expiry <= now:
                blockers.append(f"{key}:expired")
        if source["fetch_status"] != "READ_BACK" or source["sha256"] is None:
            blockers.append(f"{key}:anonymous_readback_and_hash_required")
    seen.clear()
    for adapter in data["adapters"]:
        key = f"adapter/{adapter['id']}"
        if adapter["id"] in seen:
            errors.append("duplicate_adapter_id")
        seen.add(adapter["id"])
        receipt = adapter["receipt"]
        if adapter["state"] != "NOT_TESTED":
            if (not receipt or receipt["result"] != "PASS"
                    or receipt["commit"] != data["source"]["commit"]
                    or receipt["observed_state"] != adapter["state"]):
                errors.append(f"{key}:claimed_state_without_matching_pass_receipt")
        if adapter["state"] not in {"ACTIVATED", "OBSERVED"}:
            blockers.append(f"{key}:fresh_session_activation_required")
        if receipt:
            urls.append((key + "/receipt", receipt["output_url"]))
            try:
                recorded = utc(receipt["recorded_at"])
            except ValueError:
                errors.append(f"{key}:invalid_or_unsupported_timestamp")
            else:
                if recorded > now:
                    errors.append(f"{key}:future_receipt")
    for key, value in urls:
        if not public_url(value):
            errors.append(f"{key}:not_public_release_url")
    if not data["source"]["previous_accepted_commit"]:
        blockers.append("source:rollback_target_required")
    if data["status"] == "ACCEPTED" and (errors or blockers):
        errors.append("accepted_state_with_unmet_gates")
    return {"valid_manifest": not errors, "ready_for_independent_review": not errors and not blockers,
            "errors": sorted(set(errors)), "blockers": sorted(set(blockers)),
            "scope": "Metadata validation only; no fetch, install, account test, sync, or publication performed."}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("manifest", type=Path)
    cli.add_argument("--require-ready", action="store_true")
    args = cli.parse_args()
    try:
        data = json.loads(args.manifest.read_text())
    except (OSError, ValueError):
        print(json.dumps({"valid_manifest": False, "error": "manifest_read_or_json_error"}))
        return 1
    result = validate(data)
    print(json.dumps(result, indent=2))
    return 1 if not result["valid_manifest"] else 3 if args.require_ready and not result["ready_for_independent_review"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
