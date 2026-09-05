#!/usr/bin/env python3
"""Validate the local Local Service Spotlight Claude marketplace without dependencies."""

from __future__ import annotations

import json
import html
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import (  # noqa: E402
    DuplicateJsonMember,
    StandardError,
    load_standards,
    skill_scopes,
    standards_for,
    strict_json_loads,
)


EVERYTHING_PLUGIN = "lss-everything"
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CANONICAL_SKILL_REFERENCE = re.compile(
    r"^\./skills/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
LOCAL_REFERENCE = re.compile(
    r"(?<![\w/])((?:references|scripts|assets)/[A-Za-z0-9_.\-/]+)"
)
NUMBER_WORD_VALUES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
NUMBER_TOKEN = (
    r"(?<!\d)(?<!\d[.,/½])(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"thirty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"forty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"fifty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"sixty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"seventy(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"eighty(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|"
    r"ninety(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?)(?!\d)(?![.,/½]\d)"
)
SKILL_MODIFIER = (
    r"(?:marketplace|distributed|released|bundled|included|available|total|practical|"
    r"different|unique|distinct|curated|separate|installable|"
    r"separately\s+installable|individually\s+installable|downloadable|agent|"
    r"professional|public|core|highly\s+practical|lss|best-in-class|"
    r"local\s+service\s+spotlight|custom|claude|useful|highly\s+useful|"
    r"ready-to-use)"
)
COUNT_MODIFIER_SEPARATOR = r"(?:\s*,?\s+)"
SKILL_COUNT_PATTERNS = (
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})(?:\s*\+)?"
        rf"(?:{COUNT_MODIFIER_SEPARATOR}{SKILL_MODIFIER}){{0,3}}"
        rf"{COUNT_MODIFIER_SEPARATOR}skills?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})-skills?\b(?:\s+{SKILL_MODIFIER})?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s*(?:\(|:|=)\s*(?P<count>{NUMBER_TOKEN})\s*\)?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s*(?:—|-)\s*(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s*(?:[|/:=—-]\s*)?(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s+(?:total|count)\s*(?:(?:of\s+)|[:=]\s*)?"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s+count\s*(?:is|[|:=])\s*(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:our\s+)?skills?\s+(?:currently\s+)?number\s+"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:the\s+)?number\s+of\s+skills?\s+is\s+"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})\s+is\s+(?:the\s+)?number\s+of\s+skills?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s+comprise\s+(?P<count>{NUMBER_TOKEN})\s+entries\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:the\s+)?skill\s+catalog\s+(?:has|contains|comprises)\s+"
        rf"(?P<count>{NUMBER_TOKEN})\s+entries\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})\s+entries\s+in\s+(?:the\s+)?skill\s+catalog\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskill\s+catalog\s+size\s*[:=|]\s*(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\ball\s+(?P<count>{NUMBER_TOKEN})\s+are\s+(?:individually\s+)?"
        rf"installable\s+skills?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bskills?\s*[x×]\s*(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})\s*[x×]\s*skills?\b",
        re.IGNORECASE,
    ),
)
BUNDLE_MODIFIER = (
    r"(?:marketplace|topical|released|included|available|total|installable|curated|"
    r"separate|different|unique|distinct|plugin|skill|topic|core|lss|best-in-class|"
    r"custom|claude|useful|highly\s+useful|ready-to-use)"
)
BUNDLE_NOUN = (
    r"(?:bundles?|packs?(?:\s+of\s+skills?)?|collections?(?:\s+of\s+skills?)?|"
    r"groups?\s+of\s+skills?)"
)
BUNDLE_COUNT_PATTERNS = (
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})(?:\s*\+)?"
        rf"(?:{COUNT_MODIFIER_SEPARATOR}{BUNDLE_MODIFIER}){{0,3}}"
        rf"{COUNT_MODIFIER_SEPARATOR}{BUNDLE_NOUN}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})-bundles?\b(?:\s+{BUNDLE_MODIFIER})?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{BUNDLE_NOUN}\s*(?:\(|:|=)\s*(?P<count>{NUMBER_TOKEN})\s*\)?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{BUNDLE_NOUN}\s*(?:—|-)\s*(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{BUNDLE_NOUN}\s*(?:[|/:=—-]\s*)?(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{BUNDLE_NOUN}\s+(?:total|count)\s*(?:(?:of\s+)|[:=]\s*)?"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:bundle|pack)\s+count\s*(?:is|[|:=])\s*"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:our\s+)?bundles?\s+(?:currently\s+)?number\s+"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:the\s+)?number\s+of\s+(?:bundles?|packs?)\s+is\s+"
        rf"(?P<count>{NUMBER_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})\s+is\s+(?:the\s+)?number\s+of\s+"
        rf"(?:bundles?|packs?|collections?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{BUNDLE_NOUN}\s+comprise\s+(?P<count>{NUMBER_TOKEN})\s+entries\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?P<count>{NUMBER_TOKEN})-(?:packs?|collections?)"
        rf"(?:\s+of\s+skills?|\s+marketplace)?\b",
        re.IGNORECASE,
    ),
)
SKILL_FILE_COUNT_PATTERN = re.compile(
    rf"\b(?P<count>{NUMBER_TOKEN})(?:\s*\+)?"
    rf"(?:{COUNT_MODIFIER_SEPARATOR}(?:distributed|released|bundled|included|"
    r"available|total|installable|downloadable|public|professional)){0,3}"
    rf"{COUNT_MODIFIER_SEPARATOR}`?SKILL\.md`?\s+files\b",
    re.IGNORECASE,
)


def _count_value(token: str) -> int:
    normalized = token.casefold().replace("-", " ")
    if normalized.isdigit():
        return int(normalized)
    return sum(NUMBER_WORD_VALUES[part] for part in normalized.split())


def _count_claims(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
    *,
    selection_exempt_max: int,
) -> list[tuple[int, str]]:
    # README is Markdown/HTML. Normalize reader-visible markup before deciding
    # whether prose duplicates a manifest-derived catalog total.
    search_text = unicodedata.normalize("NFKC", html.unescape(text))
    search_text = "".join(
        "" if unicodedata.category(character) == "Cf" else
        "-" if unicodedata.category(character) == "Pd" else
        "/" if character in {"\u2044", "\u2215"} else character
        for character in search_text
    )
    search_text = re.sub(r"```.*?```", " ", search_text, flags=re.DOTALL)
    search_text = re.sub(
        r"`([^`\n]+)`",
        lambda match: match.group(1)
        if match.group(1).casefold() == "skill.md"
        else " ",
        search_text,
    )
    search_text = re.sub(r"!?(?:\[([^\]]+)\])\([^)]*\)", r"\1", search_text)
    search_text = re.sub(r"\bhttps?://[^\s<>]+", " ", search_text, flags=re.IGNORECASE)
    search_text = re.sub(
        rf"\b{NUMBER_TOKEN}-skills?\.(?:md|html?|txt|json)\b",
        " ",
        search_text,
        flags=re.IGNORECASE,
    )
    search_text = re.sub(r"<!--.*?-->", "", search_text, flags=re.DOTALL)
    search_text = re.sub(
        r"</?(?:address|article|aside|blockquote|br|dd|div|dl|dt|fieldset|"
        r"figcaption|figure|footer|form|h[1-6]|header|hr|li|main|nav|ol|p|pre|"
        r"section|table|tbody|td|tfoot|th|thead|tr|ul)\b[^>]*>",
        " ",
        search_text,
        flags=re.IGNORECASE,
    )
    search_text = re.sub(r"<[^>]+>", "", search_text)
    search_text = re.sub(r"(?<=\w)_(?=\w)", "-", search_text)
    search_text = re.sub(r"[*_`]", "", search_text)
    found: dict[tuple[int, int], tuple[int, str]] = {}
    for pattern in patterns:
        for match in pattern.finditer(search_text):
            if re.search(r"\b(?:years?|months?|weeks?|days?|hours?)\b", match.group(0), re.I):
                continue
            clause_prefix = re.split(
                r"[.!?;\n]", search_text[max(0, match.start() - 100) : match.start()]
            )[-1]
            clause_suffix = re.split(
                r"[.!?;\n]", search_text[match.end() : match.end() + 100]
            )[0]
            count = _count_value(match.group("count"))
            small_selection_count = count <= selection_exempt_max and re.search(
                r"\b(?:choose|pick)(?:\s+from)?"
                r"(?:\s+(?:any|these|the|our|from|up\s+to))?\s*$",
                clause_prefix,
                re.IGNORECASE,
            )
            small_action_count = count <= 5 and re.search(
                r"\b(?:install|use|uses|using|need|needs|compare|learn|"
                r"complete|combines?|combined|pair|"
                r"quizzes?\s+for|first|no\s+more\s+than)"
                r"(?:\s+(?:any|these|the|our|from|up\s+to))?\s*$",
                clause_prefix,
                re.IGNORECASE,
            )
            historical_or_fixture = re.search(
                r"\b(?:review|reviewed|cover|covered|tested?|audit)\s*$|"
                r"\b(?:test|example)?\s*fixture(?:\s+(?:has|contains))?\s*$",
                clause_prefix,
                re.IGNORECASE,
            )
            if small_selection_count or small_action_count or historical_or_fixture or re.search(
                r"\b(?:may|can|could|should)\s+"
                r"(?:include|use|combine|install|choose)\s*$",
                clause_prefix,
                re.IGNORECASE,
            ) or re.search(
                r"\bat\s+least\s*$|\bexactly\s*$",
                clause_prefix,
                re.IGNORECASE,
            ) or re.search(
                r"(?:\b(?:january|february|march|april|may|june|july|august|"
                r"september|october|november|december)|\bPR\s*#|\bstep)\s*$",
                clause_prefix,
                re.IGNORECASE,
            ) or re.match(r"\s*-related\b", clause_suffix, re.IGNORECASE) or re.match(
                r"\s+(?:together\b|failed\b|were\s+reviewed\b|"
                r"share(?:s|d)?\b|are\s+(?:required|"
                r"prerequisites|optional)\b|should\s+activate\b|per\s+task\b|"
                r"for\s+(?:this|the|a)\s+task\b)",
                clause_suffix,
                re.IGNORECASE,
            ):
                continue
            found[match.span()] = (count, match.group(0))
    return [found[span] for span in sorted(found)]


def skill_count_claims(text: str) -> list[tuple[int, str]]:
    """Return every explicit count-of-skills claim, not unrelated numbers."""
    return _count_claims(text, SKILL_COUNT_PATTERNS, selection_exempt_max=5)


def bundle_count_claims(text: str) -> list[tuple[int, str]]:
    """Return explicit bundle-count claims that would duplicate the manifest."""
    return _count_claims(text, BUNDLE_COUNT_PATTERNS, selection_exempt_max=1)


def expected_blocks(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ([(slug, block)], errors) for every rule in standards/.

    All rules are checked in AGENTS.md. ``blocks_for_skill`` then derives each
    skill's applicable subset. Hardcoding a single slug here was the second
    place propagation silently narrowed to a single file.
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
    raw_bytes = path.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raise StandardError(f"{path}: UTF-8 BOM is not allowed in frontmatter")
    if b"\r" in raw_bytes:
        raise StandardError(f"{path}: frontmatter must use canonical LF line endings")
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StandardError(f"{path}: frontmatter must be valid UTF-8") from exc
    if not text.startswith("---\n"):
        raise StandardError(f"{path}: missing canonical opening frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise StandardError(f"{path}: missing canonical closing frontmatter delimiter")
    values: dict[str, str] = {}
    core_keys = {"name", "description", "rule-scopes"}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            comparable_line = "".join(
                character
                for character in unicodedata.normalize("NFKC", line).casefold()
                if unicodedata.category(character) != "Cf"
            ).lstrip()
            compact_key = re.sub(
                r"[^a-z]", "", re.split(r"[:=\s]", comparable_line, 1)[0]
            )
            if compact_key in {"name", "description", "rulescopes"}:
                raise StandardError(
                    f"{path}: malformed or confusable core frontmatter line {line!r}"
                )
            continue
        raw_key = match.group(1)
        comparable_key = re.sub(
            r"[^a-z]",
            "",
            "".join(
                character
                for character in unicodedata.normalize("NFKC", raw_key).casefold()
                if unicodedata.category(character) != "Cf"
            ),
        )
        if comparable_key in {"name", "description", "rulescopes"} and raw_key not in core_keys:
            raise StandardError(
                f"{path}: confusable core frontmatter key {raw_key!r}"
            )
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if raw_key in core_keys and raw_key in values:
            raise StandardError(f"{path}: duplicate core frontmatter key {raw_key!r}")
        values[raw_key] = value
    return values


def _safe_local_reference_file(boundary: Path, relative: str) -> bool:
    parts = Path(relative).parts
    if (
        not parts
        or parts[0] not in {"references", "scripts", "assets"}
        or any(part in {"", ".", ".."} for part in parts)
        or "\\" in relative
        or Path(relative).is_absolute()
    ):
        return False
    candidate = boundary.joinpath(*parts)
    cursor = boundary
    for part in parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return False
    return candidate.is_file() and not candidate.is_symlink()


def _distribution_path_errors(root: Path) -> list[str]:
    """Reject symlinks/special files anywhere that a plugin ships or validates."""

    errors: list[str] = []
    for relative in ("README.md", "AGENTS.md", ".claude-plugin/marketplace.json"):
        path = root / relative
        try:
            item = path.lstat()
        except OSError as exc:
            errors.append(f"{relative}: cannot inspect distribution input: {exc}")
            continue
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            errors.append(f"{relative}: distribution inputs must be regular non-symlink files")
    for subtree in (root / "skills", root / "standards"):
        if not subtree.is_dir() or subtree.is_symlink():
            errors.append(
                f"{subtree.relative_to(root)}: distribution root must be a real directory"
            )
            continue
        for current_name, directories, files in os.walk(
            subtree, topdown=True, followlinks=False
        ):
            current = Path(current_name)
            for name in list(directories):
                path = current / name
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                    errors.append(
                        f"{path.relative_to(root)}: distributed paths must not be symlinks or special files"
                    )
                    directories.remove(name)
            for name in files:
                path = current / name
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                    errors.append(
                        f"{path.relative_to(root)}: distributed files must be regular non-symlink files"
                    )
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = _distribution_path_errors(root)
    if errors:
        # Never continue by opening a path already proven to be a symlink,
        # special file, or unreadable distribution input.
        return sorted(set(errors))
    manifest_path = root / ".claude-plugin" / "marketplace.json"
    try:
        manifest = strict_json_loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return [f"cannot read {manifest_path.relative_to(root)}: {exc}"]

    if not isinstance(manifest, dict):
        return ["marketplace.json must contain a JSON object"]

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
        advertised_counts = (
            skill_count_claims(description) if isinstance(description, str) else []
        )
        for advertised_count, _ in advertised_counts:
            if advertised_count != len(skills):
                errors.append(
                    f"plugin {name!r} advertises {advertised_count} skills "
                    f"but lists {len(skills)}"
                )
        string_skills: list[str] = []
        for skill_index, skill_ref in enumerate(skills):
            if not isinstance(skill_ref, str):
                errors.append(
                    f"plugin {name!r} skills[{skill_index}] must be a string path, "
                    f"found {skill_ref!r}"
                )
                continue
            string_skills.append(skill_ref)

        if len(string_skills) != len(set(string_skills)):
            errors.append(f"plugin {name!r} lists a skill more than once")
        for skill_ref in string_skills:
            reference_match = CANONICAL_SKILL_REFERENCE.fullmatch(skill_ref)
            if reference_match is None:
                errors.append(f"plugin {name!r} has invalid skill path: {skill_ref!r}")
                continue
            skill_path = root / "skills" / reference_match.group("slug")
            skill_file = skill_path / "SKILL.md"
            if (
                skill_path.is_symlink()
                or skill_file.is_symlink()
                or not skill_path.is_dir()
                or not skill_file.is_file()
            ):
                errors.append(f"plugin {name!r} references missing {skill_ref}/SKILL.md")
        if name == EVERYTHING_PLUGIN:
            if everything is not None:
                errors.append(f"{EVERYTHING_PLUGIN} must appear exactly once")
            everything = string_skills

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
        try:
            metadata = _frontmatter(skill_file)
        except (OSError, UnicodeDecodeError, StandardError) as exc:
            errors.append(str(exc))
            continue
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
                if not any(
                    _safe_local_reference_file(boundary, relative)
                    for boundary in (skill_dir, root)
                ):
                    errors.append(
                        f"{markdown.relative_to(root)} references missing, unsafe, or "
                        f"non-regular {relative}"
                    )

    readme = (root / "README.md").read_text(encoding="utf-8")
    hard_coded_counts = skill_count_claims(readme)
    hard_coded_bundle_counts = bundle_count_claims(readme)
    hard_coded_skill_files = [
        match.group(0) for match in SKILL_FILE_COUNT_PATTERN.finditer(readme)
    ]
    for _, claim in hard_coded_counts:
        errors.append(
            f"README hard-codes a derived skill count ({claim!r}); derive it from "
            ".claude-plugin/marketplace.json instead"
        )
    for claim in hard_coded_skill_files:
        errors.append(
            f"README hard-codes a derived skill count ({claim!r}); derive it from "
            ".claude-plugin/marketplace.json instead"
        )
    for _, claim in hard_coded_bundle_counts:
        errors.append(
            f"README hard-codes a derived bundle count ({claim!r}); derive it from "
            ".claude-plugin/marketplace.json instead"
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
