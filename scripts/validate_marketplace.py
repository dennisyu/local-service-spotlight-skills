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

    readme = (root / "README.md").read_text(encoding="utf-8")
    advertised = re.search(r"all (\d+) skills", readme, flags=re.IGNORECASE)
    if advertised and int(advertised.group(1)) != len(skill_dirs):
        errors.append(
            f"README advertises {advertised.group(1)} skills but found {len(skill_dirs)}"
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
