#!/usr/bin/env python3
"""Validate the local BlitzMetrics Claude marketplace without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_REFERENCE = re.compile(
    r"(?<![\w/])((?:references|scripts|assets)/[A-Za-z0-9_.\-/]+)"
)
SHARED_RULE_START = "<!-- shared-rule:silent-media-playback:start -->"
SHARED_RULE_END = "<!-- shared-rule:silent-media-playback:end -->"


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
    everything_plugin: dict[str, object] | None = None
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
        if name == "blitzmetrics-everything":
            if everything is not None:
                errors.append("blitzmetrics-everything must appear exactly once")
            everything = skills
            everything_plugin = plugin

    if everything is None:
        errors.append("missing required blitzmetrics-everything plugin")
        everything_set: set[str] = set()
    else:
        everything_set = set(everything)

    skill_dirs = sorted(
        path for path in (root / "skills").iterdir() if path.is_dir()
    ) if (root / "skills").is_dir() else []
    actual_refs = {f"./skills/{path.name}" for path in skill_dirs}
    for missing in sorted(actual_refs - everything_set):
        errors.append(f"skill is not in blitzmetrics-everything: {missing}")
    for stale in sorted(everything_set - actual_refs):
        errors.append(f"blitzmetrics-everything has a stale skill path: {stale}")

    grok_manifest_path = root / ".grok-plugin" / "plugin.json"
    try:
        grok_manifest = json.loads(grok_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"cannot read {grok_manifest_path.relative_to(root)}: {exc}"
        )
        grok_manifest = None

    if not isinstance(grok_manifest, dict):
        if grok_manifest is not None:
            errors.append(".grok-plugin/plugin.json must contain an object")
    elif everything_plugin is not None:
        expected_name = everything_plugin.get("name")
        if grok_manifest.get("name") != expected_name:
            errors.append(
                "Grok plugin name must match the Claude blitzmetrics-everything "
                f"name {expected_name!r}, found {grok_manifest.get('name')!r}"
            )

        metadata = manifest.get("metadata")
        expected_version = metadata.get("version") if isinstance(metadata, dict) else None
        if not isinstance(expected_version, str) or not expected_version:
            errors.append("Claude marketplace metadata.version must be a non-empty string")
        elif grok_manifest.get("version") != expected_version:
            errors.append(
                "Grok plugin version must match Claude marketplace metadata.version "
                f"{expected_version!r}, found {grok_manifest.get('version')!r}"
            )

        grok_skills = grok_manifest.get("skills")
        if grok_skills != "./skills/":
            errors.append(
                "Grok plugin skills must be './skills/' so it resolves to the "
                "Claude blitzmetrics-everything inventory, "
                f"found {grok_skills!r}"
            )
        elif actual_refs != everything_set:
            errors.append(
                "Grok ./skills/ inventory must match Claude blitzmetrics-everything"
            )

    try:
        shared_rule = (
            root / "standards" / "silent-media-playback.md"
        ).read_text(encoding="utf-8").strip()
        expected_rule_block = (
            f"{SHARED_RULE_START}\n{shared_rule}\n{SHARED_RULE_END}"
        )
    except OSError as exc:
        errors.append(f"cannot read shared media rule: {exc}")
        expected_rule_block = ""

    agents_file = root / "AGENTS.md"
    if not agents_file.is_file():
        errors.append("missing AGENTS.md with the shared media rule")
    elif expected_rule_block and expected_rule_block not in agents_file.read_text(
        encoding="utf-8"
    ):
        errors.append("AGENTS.md has a missing or stale shared media rule")

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
        if expected_rule_block and expected_rule_block not in skill_file.read_text(
            encoding="utf-8"
        ):
            errors.append(
                f"{skill_file.relative_to(root)} has a missing or stale shared media rule"
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
