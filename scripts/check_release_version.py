#!/usr/bin/env python3
"""Require one release version across marketplace manifests and bump it on PRs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CLAUDE_MANIFEST = Path(".claude-plugin/marketplace.json")
GROK_MANIFEST = Path(".grok-plugin/plugin.json")
PROTECTED_PREFIXES = (
    ".claude-plugin/",
    ".grok-plugin/",
    "standards/",
    "skills/",
)
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseVersionError(ValueError):
    """A release-version contract could not be validated."""


@dataclass(frozen=True)
class ReleaseVersions:
    claude: str
    grok: str

    @property
    def equal(self) -> bool:
        return self.claude == self.grok


@dataclass(frozen=True)
class ReleaseVersionReport:
    base_commit: str
    current_version: str
    base_versions: ReleaseVersions | None
    protected_changes: tuple[str, ...]


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ReleaseVersionError(
            f"git {' '.join(arguments)} failed: {detail or 'unknown error'}"
        )
    return completed.stdout


def _load_json(text: str, source: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReleaseVersionError(f"cannot parse {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseVersionError(f"{source} must contain a JSON object")
    return value


def _version(value: Any, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseVersionError(f"{source} must contain a non-empty version string")
    normalized = value.strip()
    if SEMVER.fullmatch(normalized) is None:
        raise ReleaseVersionError(
            f"{source} must contain a stable semantic version such as 1.2.2"
        )
    return normalized


def _version_key(version: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(version)
    if match is None:  # All callers receive values validated by _version().
        raise ReleaseVersionError(f"invalid semantic version: {version!r}")
    return tuple(int(part) for part in match.groups())


def _versions_from_documents(
    claude_document: dict[str, Any],
    grok_document: dict[str, Any],
    source_prefix: str,
) -> ReleaseVersions:
    metadata = claude_document.get("metadata")
    if not isinstance(metadata, dict):
        raise ReleaseVersionError(
            f"{source_prefix}{CLAUDE_MANIFEST} must contain metadata.version"
        )
    return ReleaseVersions(
        claude=_version(
            metadata.get("version"),
            f"{source_prefix}{CLAUDE_MANIFEST}: metadata.version",
        ),
        grok=_version(
            grok_document.get("version"),
            f"{source_prefix}{GROK_MANIFEST}: version",
        ),
    )


def current_versions(root: Path) -> ReleaseVersions:
    try:
        claude_text = (root / CLAUDE_MANIFEST).read_text(encoding="utf-8")
        grok_text = (root / GROK_MANIFEST).read_text(encoding="utf-8")
    except OSError as exc:
        raise ReleaseVersionError(f"cannot read current release manifests: {exc}") from exc
    return _versions_from_documents(
        _load_json(claude_text, str(CLAUDE_MANIFEST)),
        _load_json(grok_text, str(GROK_MANIFEST)),
        "",
    )


def resolve_base_commit(root: Path, base_ref: str) -> str:
    if not base_ref.strip():
        raise ReleaseVersionError("--base-ref must not be empty")
    return _git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}").strip()


def base_versions(root: Path, base_commit: str) -> ReleaseVersions:
    claude_text = _git(root, "show", f"{base_commit}:{CLAUDE_MANIFEST.as_posix()}")
    grok_text = _git(root, "show", f"{base_commit}:{GROK_MANIFEST.as_posix()}")
    prefix = f"{base_commit}:"
    return _versions_from_documents(
        _load_json(claude_text, f"{prefix}{CLAUDE_MANIFEST}"),
        _load_json(grok_text, f"{prefix}{GROK_MANIFEST}"),
        prefix,
    )


def changed_paths(root: Path, base_commit: str) -> tuple[str, ...]:
    # Compare the base tree to the complete checkout, not just HEAD. --no-renames
    # preserves both sides of a move, so moving a file out of skills/ still counts.
    output = _git(root, "diff", "--name-only", "--no-renames", base_commit, "--")
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    paths = {
        line.strip()
        for text in (output, untracked)
        for line in text.splitlines()
        if line.strip()
    }
    return tuple(sorted(paths))


def is_protected_path(path: str) -> bool:
    return path == "AGENTS.md" or path.startswith(PROTECTED_PREFIXES)


def check_release(root: Path, base_ref: str) -> ReleaseVersionReport:
    root = root.resolve()
    current = current_versions(root)
    if not current.equal:
        raise ReleaseVersionError(
            "current release versions must match: "
            f"{CLAUDE_MANIFEST}={current.claude!r}, "
            f"{GROK_MANIFEST}={current.grok!r}"
        )

    base_commit = resolve_base_commit(root, base_ref)
    changed = changed_paths(root, base_commit)
    protected = tuple(path for path in changed if is_protected_path(path))
    previous: ReleaseVersions | None = None
    if protected:
        previous = base_versions(root, base_commit)
        non_increased_manifests = [
            name
            for name, version in (
                (str(CLAUDE_MANIFEST), previous.claude),
                (str(GROK_MANIFEST), previous.grok),
            )
            if _version_key(current.claude) <= _version_key(version)
        ]
        if non_increased_manifests:
            raise ReleaseVersionError(
                "protected marketplace files changed but the shared release version "
                "was not increased beyond every base manifest: "
                f"current={current.claude!r}; "
                f"base Claude={previous.claude!r}; base Grok={previous.grok!r}; "
                f"not increased against {', '.join(non_increased_manifests)}; "
                f"protected changes={', '.join(protected)}"
            )

    return ReleaseVersionReport(
        base_commit=base_commit,
        current_version=current.claude,
        base_versions=previous,
        protected_changes=protected,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-ref",
        required=True,
        help="Git commit or ref for the pull request base tree",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        report = check_release(root, args.base_ref)
    except ReleaseVersionError as exc:
        print(f"Release version gate failed: {exc}", file=sys.stderr)
        return 1

    if report.protected_changes:
        assert report.base_versions is not None
        print(
            "Release version gate passed: "
            f"{report.current_version}; base Claude={report.base_versions.claude}, "
            f"base Grok={report.base_versions.grok}; "
            f"{len(report.protected_changes)} protected path(s) changed."
        )
    else:
        print(
            "Release version gate passed: "
            f"{report.current_version}; no protected marketplace paths changed."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
