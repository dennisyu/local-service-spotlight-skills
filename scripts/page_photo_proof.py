#!/usr/bin/env python3
"""Check actual static page/photo bytes against a private reviewed provenance manifest.

This checks evidence consistency, never identity, permission, endorsement or visibility.
Run rendered_visual_check.mjs and fresh-context editorial review separately.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance_digest(asset: dict) -> str:
    """Bind review to every declared asset field, including permission/context."""
    canonical = json.dumps(asset, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def nonblank(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def public_url(value) -> bool:
    if not nonblank(value):
        return False
    parsed = urlsplit(value)
    return parsed.scheme in ("https", "http") and bool(parsed.hostname) and not parsed.username and not parsed.password


def inside(root: Path, relative: str) -> Path:
    if not nonblank(relative) or Path(relative).is_absolute():
        raise ValueError("path must be relative to the public root")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError("missing file or path escapes public root")
    return candidate


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.photos = []
        self.links = set()
        self.text = []
        self.has_base = False
        self.duplicate_attributes = []

    def excluded(self, attrs=None):
        entries = self.stack + ([("", attrs)] if attrs is not None else [])
        return any(t in ("nav", "footer", "script", "style", "template", "noscript") or
                   a.get("role") in ("navigation", "banner", "dialog") or
                   "hidden" in a or a.get("aria-hidden") == "true" for t, a in entries)

    def handle_starttag(self, tag, attrs):
        names = [name for name, _ in attrs]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            self.duplicate_attributes.append(f"{tag}: {', '.join(duplicates)}")
        attrs = dict(attrs)
        excluded = self.excluded(attrs)
        if tag == "base":
            self.has_base = True
        if tag == "a" and attrs.get("href") and not excluded:
            self.links.add(attrs["href"])
        if tag == "img" and not excluded:
            # This static contract intentionally supports one explicit local src.
            attrs["_unsupported_selection"] = "srcset" in attrs or any(t == "picture" for t, _ in self.stack)
            self.photos.append(attrs)
        if tag not in ("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"):
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not self.excluded():
            self.text.append(data)


def check(root: Path, manifest: dict) -> list[str]:
    root = root.resolve()
    errors = []
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        return ["manifest version must be 1"]
    assets = manifest.get("assets")
    pages = manifest.get("pages")
    if not isinstance(assets, dict) or not isinstance(pages, list):
        return ["manifest needs assets object and pages list"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.suffix.lower() in (".html", ".htm")}
    listed = [p.get("path") for p in pages if isinstance(p, dict)]
    if len(listed) != len(pages) or any(not nonblank(p) for p in listed):
        return ["every page entry needs a relative path"]
    if len(listed) != len(set(listed)):
        errors.append("duplicate page paths")
    if set(listed) != actual:
        errors.append(f"HTML inventory differs: unlisted={sorted(actual-set(listed))}; missing={sorted(set(listed)-actual)}")
    if not actual:
        errors.append("public root contains no HTML pages")
    for record in pages:
        name = record["path"]
        try:
            page_path = inside(root, name)
            sha = digest(page_path)
            parsed = Page()
            parsed.feed(page_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        if record.get("sha256") != sha:
            errors.append(f"{name}: page bytes changed or hash missing")
        if parsed.has_base:
            errors.append(f"{name}: base URL overrides are unsupported; use explicit local photo paths")
        if parsed.duplicate_attributes:
            errors.append(f"{name}: duplicate HTML attributes are unsupported: {'; '.join(parsed.duplicate_attributes)}")
        photo_ids = record.get("photo_ids")
        if not isinstance(photo_ids, list) or not photo_ids or any(not nonblank(x) for x in photo_ids):
            errors.append(f"{name}: no real photo ids")
            continue
        if len(photo_ids) != len(set(photo_ids)):
            errors.append(f"{name}: duplicate photo ids")
        if any(img.get("data-lss-real-image") == "verified" and img.get("data-lss-asset-id") not in photo_ids
               for img in parsed.photos):
            errors.append(f"{name}: marked photo omitted from page provenance")
        review = record.get("review", {})
        if not isinstance(review, dict):
            review = {}
        review_assets = review.get("asset_sha256", {})
        if not isinstance(review_assets, dict):
            review_assets = {}
        review_provenance = review.get("asset_provenance_sha256", {})
        if not isinstance(review_provenance, dict):
            review_provenance = {}
        prepared_by = record.get("prepared_by")
        if (not nonblank(prepared_by) or not nonblank(review.get("reviewer")) or
                review.get("reviewer") == prepared_by or review.get("result") != "PASS" or
                review.get("page_sha256") != sha or
                review.get("source_identity_context_and_permission_checked") is not True or
                review.get("caption_and_claims_checked") is not True):
            errors.append(f"{name}: missing or stale independent source/content review")
        for asset_id in photo_ids:
            asset = assets.get(asset_id)
            if not isinstance(asset, dict):
                errors.append(f"{name}: unknown photo {asset_id}")
                continue
            if (asset.get("kind") != "photo" or not public_url(asset.get("source_url")) or
                    not nonblank(asset.get("permission_basis")) or not nonblank(asset.get("caption")) or
                    not nonblank(asset.get("context"))):
                errors.append(f"{name}/{asset_id}: incomplete photo provenance")
            if review_provenance.get(asset_id) != provenance_digest(asset):
                errors.append(f"{name}/{asset_id}: provenance changed or review digest missing")
            try:
                photo = inside(root, asset.get("path"))
                photo_sha = digest(photo)
                # Signature screening only. Actual decode/load and identity are
                # checked by the separate rendered/source reviews, never here.
                magic = photo.read_bytes()[:16]
                raster = (magic.startswith(b"\xff\xd8\xff") or magic.startswith(b"\x89PNG\r\n\x1a\n") or
                          (magic.startswith(b"RIFF") and magic[8:12] == b"WEBP") or
                          magic.startswith((b"GIF87a", b"GIF89a")) or
                          (magic[4:8] == b"ftyp" and magic[8:12] in (b"avif", b"avis")))
                if not raster:
                    errors.append(f"{name}/{asset_id}: unsupported raster signature; diagram/text cannot count")
                if asset.get("sha256") != photo_sha or review_assets.get(asset_id) != photo_sha:
                    errors.append(f"{name}/{asset_id}: photo bytes changed or review hash missing")
                matching = []
                for img in parsed.photos:
                    source = urlsplit(img.get("src", ""))
                    if source.scheme or source.netloc or not source.path:
                        continue
                    relative = unquote(source.path)
                    target = (root / relative.lstrip("/") if relative.startswith("/") else page_path.parent / relative).resolve()
                    if target == photo and img.get("data-lss-asset-id") == asset_id:
                        matching.append(img)
                if any(img["_unsupported_selection"] for img in matching):
                    errors.append(f"{name}/{asset_id}: srcset/picture image selection is unsupported; review all selected bytes with an equivalent validator")
                if not any(img.get("data-lss-real-image") == "verified" and nonblank(img.get("alt")) for img in matching):
                    errors.append(f"{name}/{asset_id}: no matching marked photo with alt in page content")
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"{name}/{asset_id}: {exc}")
            if asset.get("source_url") not in parsed.links:
                errors.append(f"{name}/{asset_id}: source link absent from page")
            caption = asset.get("caption")
            if nonblank(caption) and " ".join(caption.split()) not in " ".join(" ".join(parsed.text).split()):
                errors.append(f"{name}/{asset_id}: declared caption absent from page text")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="exact static public output root")
    parser.add_argument("--manifest", required=True, type=Path, help="private provenance/review JSON; keep outside public root")
    args = parser.parse_args()
    try:
        if args.manifest.resolve().is_relative_to(args.root.resolve()):
            raise ValueError("private manifest must be outside public root")
        errors = check(args.root, json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"status": "HOLD" if errors else "CONSISTENT", "errors": errors,
                      "limit": "Byte/provenance declarations only; source truth, visibility, permissions and publication still need verification."}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
