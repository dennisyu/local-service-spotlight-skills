#!/usr/bin/env python3
"""Convert one or more skill-pack directories or ZIPs into .plugin archives."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path


VERSION_SUFFIX = re.compile(
    r"(?:[-_.]v?\d+(?:[-_.]\d+)*(?:[-_.](?:alpha|beta|rc)\d*)?)$",
    re.IGNORECASE,
)


def kebab_name(value: str) -> str:
    name = VERSION_SUFFIX.sub("", value.strip())
    name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    if not name:
        raise ValueError(f"cannot derive a stable plugin name from {value!r}")
    return name


def _safe_extract(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"unsafe path in {archive}: {member.filename}")
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"symbolic links are not allowed in {archive}: {member.filename}")
        source.extractall(destination)


def _content_root(extracted: Path) -> Path:
    visible = [path for path in extracted.iterdir() if path.name != "__MACOSX"]
    if len(visible) == 1 and visible[0].is_dir():
        return visible[0]
    return extracted


def _repair_frontmatter(skill_file: Path, expected_name: str) -> None:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        raise ValueError(f"{skill_file} has no valid YAML frontmatter")
    header_end = text.find("\n---", 4)
    header = text[4:header_end]
    if re.search(r"^name:\s*.*$", header, flags=re.MULTILINE):
        header = re.sub(
            r"^name:\s*.*$", f'name: "{expected_name}"', header,
            count=1, flags=re.MULTILINE,
        )
    else:
        header = f'name: "{expected_name}"\n{header}'
    skill_file.write_text(f"---\n{header}\n{text[header_end + 1:]}", encoding="utf-8")


def _find_skills(root: Path) -> list[Path]:
    return sorted(
        path.parent for path in root.rglob("SKILL.md")
        if "__MACOSX" not in path.parts and ".git" not in path.parts
    )


def build_plugin(source: Path, output_dir: Path, dry_run: bool = False) -> Path:
    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    source_stem = source.stem if source.is_file() else source.name
    plugin_name = kebab_name(source_stem)
    output_path = output_dir.resolve() / f"{plugin_name}.plugin"

    with tempfile.TemporaryDirectory(prefix="pack2plugin-") as temp_name:
        temp = Path(temp_name)
        if source.is_dir():
            content_root = source
        elif source.suffix.lower() == ".zip":
            extracted = temp / "extracted"
            extracted.mkdir()
            _safe_extract(source, extracted)
            content_root = _content_root(extracted)
        else:
            raise ValueError(f"input must be a directory or .zip: {source}")

        skill_dirs = _find_skills(content_root)
        if not skill_dirs:
            raise ValueError(f"no SKILL.md files found in {source}")
        skill_names = [kebab_name(path.name) for path in skill_dirs]
        if len(skill_names) != len(set(skill_names)):
            raise ValueError(f"two skill directories normalize to the same name in {source}")

        if dry_run:
            print(f"Would create {output_path} with {len(skill_dirs)} skill(s):")
            for name in skill_names:
                print(f"- {name}")
            return output_path

        stage = temp / plugin_name
        (stage / ".claude-plugin").mkdir(parents=True)
        (stage / "skills").mkdir()
        manifest = {
            "name": plugin_name,
            "description": f"Converted skill pack: {source_stem}",
            "version": "1.0.0",
        }
        (stage / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

        for source_skill, skill_name in zip(skill_dirs, skill_names):
            destination = stage / "skills" / skill_name
            shutil.copytree(
                source_skill, destination,
                ignore=shutil.ignore_patterns("__MACOSX", ".DS_Store", "*.pyc", "__pycache__"),
            )
            _repair_frontmatter(destination / "SKILL.md", skill_name)

        for optional in ("agents", "commands"):
            candidate = content_root / optional
            if candidate.is_dir():
                shutil.copytree(
                    candidate, stage / optional,
                    ignore=shutil.ignore_patterns("__MACOSX", ".DS_Store"),
                )

        output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(stage).as_posix())
    print(f"Created {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packs", nargs="+", type=Path, help="pack directories or ZIP files")
    parser.add_argument("--out", type=Path, default=Path("dist"), help="output directory")
    parser.add_argument("--dry-run", action="store_true", help="show work without writing")
    args = parser.parse_args()
    for pack in args.packs:
        build_plugin(pack, args.out, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
