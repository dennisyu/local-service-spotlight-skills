#!/usr/bin/env python3
"""Validate the local Local Service Spotlight Claude marketplace without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import (  # noqa: E402
    StandardError,
    load_standards,
    skill_scopes,
    standards_for,
)


EVERYTHING_PLUGIN = "lss-everything"
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_REFERENCE = re.compile(
    r"(?<![\w/])((?:references|scripts|assets)/[A-Za-z0-9_.\-/]+)"
)
DOCUMENTED_SKILL_COUNT_CLAIMS = (
    (
        "README.md",
        "marketplace overview",
        re.compile(
            r"canonical marketplace for the (?P<count>\d+) "
            r"Local Service Spotlight skills",
            re.IGNORECASE,
        ),
    ),
    (
        "README.md",
        "everything bundle table",
        re.compile(r"\| `lss-everything` \| All (?P<count>\d+) skills \|"),
    ),
    (
        "README.md",
        "generated skill-file total",
        re.compile(r"(?P<count>\d+) `SKILL\.md` files"),
    ),
    (
        "ACCEPTANCE.md",
        "fresh-account total",
        re.compile(r"Confirm all (?P<count>\d+) expected skills"),
    ),
    (
        "ACCEPTANCE.md",
        "propagation-copy total",
        re.compile(r"wc -l` returns (?P<count>\d+)"),
    ),
    (
        "CONTRIBUTING.md",
        "sync target total",
        re.compile(r"stamps it into all (?P<count>\d+) skills"),
    ),
    (
        "HOW-KNOWLEDGE-PROPAGATES.md",
        "pack total",
        re.compile(r"pack contains (?P<count>\d+) skills"),
    ),
    (
        "HOW-KNOWLEDGE-PROPAGATES.md",
        "stamp target total",
        re.compile(r"into all (?P<count>\d+) skill files"),
    ),
    (
        "HOW-KNOWLEDGE-PROPAGATES.md",
        "manual-edit total",
        re.compile(r"No editing (?P<count>\d+) files"),
    ),
    (
        "HOW-KNOWLEDGE-PROPAGATES.md",
        "diagram target total",
        re.compile(r"all (?P<count>\d+) skills\s+a site"),
    ),
    (
        "skills/skill-registry/SKILL.md",
        "reconciliation total",
        re.compile(r"all (?P<count>\d+) available skills"),
    ),
    (
        "skills/skill-registry/references/inventory.md",
        "canonical inventory total",
        re.compile(r"\| Skills in `lss-everything` \| (?P<count>\d+)\b"),
    ),
    (
        "skills/skill-registry/references/inventory.md",
        "bundle inventory total",
        re.compile(r"\| `lss-everything` \| (?P<count>\d+) \|"),
    ),
    (
        "skills/skill-registry/references/inventory.md",
        "directory inventory total",
        re.compile(r"same (?P<count>\d+) directories"),
    ),
)


def documented_skill_count_errors(root: Path, expected: int) -> list[str]:
    """Keep every human-facing inventory count congruent with the manifest.

    The `lss-everything` skills array is the source. The explicit claims below are
    checked because they are acceptance and propagation instructions where an old
    number can make a correct release look broken (or an incomplete release look
    complete).
    """
    errors: list[str] = []
    texts: dict[str, str] = {}
    for relative, label, pattern in DOCUMENTED_SKILL_COUNT_CLAIMS:
        if relative not in texts:
            try:
                texts[relative] = (root / relative).read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"cannot read {relative} for skill-count validation: {exc}")
                texts[relative] = ""
        match = pattern.search(texts[relative])
        if not match:
            errors.append(f"{relative} is missing its {label} skill-count claim")
            continue
        found = int(match.group("count"))
        if found != expected:
            errors.append(
                f"{relative} {label} says {found} skills but "
                f"{EVERYTHING_PLUGIN} lists {expected}"
            )
    return errors


def expected_blocks(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ([(slug, block)], errors) for every rule in standards/.

    Every rule is checked in every distributed skill, not one chosen rule.
    Hardcoding a single slug here was the second place propagation silently
    narrowed to a single file.
    """
    try:
        standards = load_standards(root / "standards")
    except StandardError as exc:
        return [], [f"standards/ is malformed: {exc}"]
    if not standards:
        return [], ["standards/ contains no rules"]
    return [(s.slug, s.block()) for s in standards], []


def blocks_for_skill(root: Path, skill_file: Path) -> list[tuple[str, str]]:
    standards = load_standards(root / "standards")
    keep = standards_for(standards, skill_scopes(skill_file))
    return [(s.slug, s.block()) for s in keep]


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / ".claude-plugin" / "marketplace.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {manifest_path.relative_to(root)}: {exc}"]

    plugins = manifest.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        return ["marketplace.json must contain a non-empty plugins array"]

    plugin_names: set[str] = set()
    everything: list[str] | None = None
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            errors.append(f"plugins[{index}] must be an object")
            continue
        name = plugin.get("name")
        if not isinstance(name, str) or not KEBAB.fullmatch(name):
            errors.append(f"plugins[{index}].name must be stable kebab-case")
        elif name in plugin_names:
            errors.append(f"duplicate plugin name: {name}")
        else:
            plugin_names.add(name)
        if plugin.get("source") != "./":
            errors.append(f"plugin {name!r} must use the local source './'")
        skills = plugin.get("skills")
        if not isinstance(skills, list) or not skills:
            errors.append(f"plugin {name!r} must have a non-empty skills array")
            continue
        description = plugin.get("description")
        if isinstance(description, str):
            advertised = re.search(
                r"\b(?P<count>\d+)(?:\s+Local Service Spotlight)?\s+skills\b",
                description,
                flags=re.IGNORECASE,
            )
            if advertised and int(advertised.group("count")) != len(skills):
                errors.append(
                    f"plugin {name!r} description advertises "
                    f"{advertised.group('count')} skills but lists {len(skills)}"
                )
        if len(skills) != len(set(skills)):
            errors.append(f"plugin {name!r} lists a skill more than once")
        for skill_ref in skills:
            if not isinstance(skill_ref, str) or not skill_ref.startswith("./skills/"):
                errors.append(f"plugin {name!r} has invalid skill path: {skill_ref!r}")
                continue
            skill_path = root / skill_ref.removeprefix("./")
            if not (skill_path / "SKILL.md").is_file():
                errors.append(f"plugin {name!r} references missing {skill_ref}/SKILL.md")
        if name == EVERYTHING_PLUGIN:
            if everything is not None:
                errors.append(f"{EVERYTHING_PLUGIN} must appear exactly once")
            everything = skills

    if everything is None:
        errors.append(f"missing required {EVERYTHING_PLUGIN} plugin")
        everything_set: set[str] = set()
    else:
        everything_set = set(everything)

    skill_dirs = sorted(
        path for path in (root / "skills").iterdir() if path.is_dir()
    ) if (root / "skills").is_dir() else []
    actual_refs = {f"./skills/{path.name}" for path in skill_dirs}
    for missing in sorted(actual_refs - everything_set):
        errors.append(f"skill is not in {EVERYTHING_PLUGIN}: {missing}")
    for stale in sorted(everything_set - actual_refs):
        errors.append(f"{EVERYTHING_PLUGIN} has a stale skill path: {stale}")
    if everything is not None:
        errors.extend(documented_skill_count_errors(root, len(everything)))

    blocks, block_errors = expected_blocks(root)
    errors.extend(block_errors)

    agents_file = root / "AGENTS.md"
    if not agents_file.is_file():
        errors.append("missing AGENTS.md with the shared house rules")
    else:
        agents_text = agents_file.read_text(encoding="utf-8")
        for slug, block in blocks:
            if block not in agents_text:
                errors.append(f"AGENTS.md has a missing or stale shared rule: {slug}")

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"missing skills/{skill_dir.name}/SKILL.md")
            continue
        metadata = _frontmatter(skill_file)
        if metadata.get("name") != skill_dir.name:
            errors.append(
                f"{skill_file.relative_to(root)} name must be {skill_dir.name!r}, "
                f"found {metadata.get('name')!r}"
            )
        if not metadata.get("description"):
            errors.append(f"{skill_file.relative_to(root)} needs a description")
        skill_text = skill_file.read_text(encoding="utf-8")
        try:
            expected_here = blocks_for_skill(root, skill_file)
        except StandardError as exc:
            errors.append(str(exc))
            expected_here = []
        for slug, block in expected_here:
            if block not in skill_text:
                errors.append(
                    f"{skill_file.relative_to(root)} has a missing or stale "
                    f"shared rule: {slug}"
                )

        for markdown in skill_dir.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            for relative in LOCAL_REFERENCE.findall(text):
                relative = relative.rstrip(".,:;!?)]}")
                candidates = (skill_dir / relative, root / relative)
                if not any(candidate.exists() for candidate in candidates):
                    errors.append(
                        f"{markdown.relative_to(root)} references missing {relative}"
                    )

    return sorted(set(errors))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print(f"Marketplace validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    skill_count = sum(1 for path in (root / "skills").iterdir() if path.is_dir())
    print(f"Marketplace validation passed: {skill_count} skills, all references present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
