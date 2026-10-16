#!/usr/bin/env python3
"""Sweep live pages against every machine-checkable rule in ``standards/``.

The sweep is *generated from the rules*, never written beside them. Add a
``checks`` block to a standard and the next sweep enforces it; nothing else has
to be edited, and there is no second copy of the rule to drift out of sync.

    # prove every rule's own patterns actually work — no network
    python3 scripts/fleet_check.py --self-test

    # check the manifest parses and every regex compiles — no network
    python3 scripts/fleet_check.py --lint

    # sweep live pages
    python3 scripts/fleet_check.py https://georgepaladichuk.com/ --tag personal-brand
    python3 scripts/fleet_check.py --targets fleet.txt --json report.json

A targets file is one URL per line, with optional comma-separated tags after
whitespace. Tags decide which rules apply, so a personal-brand rule does not fire
on a product site:

    https://georgepaladichuk.com/     personal-brand,client
    https://blitzmetrics.com/         company

Exit codes
----------
0  no ``error``-severity findings (warnings may be present)
1  at least one ``error``-severity finding
2  the sweep could not run — a page failed to load, or a standard is malformed

The distinction matters. A sweep that cannot fetch a page has not found the page
clean; it has found nothing. Exit 2 says so instead of reporting a pass.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import (  # noqa: E402
    Check,
    Standard,
    StandardError,
    load_standards,
)


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 LSSFleetCheck/1.0"
)
EXEMPT_WINDOW = 160
SNIPPET = 140
PAGE_TIMEOUT = 30
LINK_TIMEOUT = 20
LINK_PAUSE = 0.4


@dataclass
class Finding:
    url: str
    standard: str
    check: str
    severity: str
    message: str
    detail: str

    @property
    def blocking(self) -> bool:
        return self.severity == "error"


# ----------------------------------------------------------------------------
# fetching


def fetch(url: str, timeout: int = PAGE_TIMEOUT) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return response.status, raw.decode(charset, errors="replace")


def status_of(url: str) -> tuple[int, str]:
    """Return (status, note). Status 0 means the request never completed."""
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(
            url, headers={"User-Agent": UA}, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=LINK_TIMEOUT) as response:
                return response.status, ""
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue
            return exc.code, ""
        except urllib.error.URLError as exc:
            return 0, str(exc.reason)
        except Exception as exc:  # noqa: BLE001 - a sweep must not die on one link
            return 0, exc.__class__.__name__
    return 0, "unreachable"


# ----------------------------------------------------------------------------
# running one check


def _snippet(text: str, start: int, end: int) -> str:
    fragment = text[max(0, start - 20) : min(len(text), end + 20)]
    return re.sub(r"\s+", " ", fragment).strip()[:SNIPPET]


def _exempted(text: str, start: int, end: int, marker: str) -> bool:
    window = text[max(0, start - EXEMPT_WINDOW) : end + EXEMPT_WINDOW]
    return marker in window


def normalise_json_slashes(text: str) -> str:
    """JSON-LD is often emitted with escaped slashes (``https:\\/\\/``)."""
    return text.replace("\\/", "/")


def run_regex_check(check: Check, url: str, body: str, severity: str) -> list[Finding]:
    findings: list[Finding] = []

    if check.kind == "require_regex":
        if check.pattern.search(body) is None:
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, "not found")
            )
        return findings

    hits = 0
    for match in check.pattern.finditer(body):
        if check.exempt_if_near and _exempted(
            body, match.start(), match.end(), check.exempt_if_near
        ):
            continue
        hits += 1
        if hits <= 5:
            findings.append(
                Finding(
                    url,
                    check.slug,
                    check.id,
                    severity,
                    check.message,
                    _snippet(body, match.start(), match.end()),
                )
            )
    if hits > 5:
        findings.append(
            Finding(
                url,
                check.slug,
                check.id,
                severity,
                check.message,
                f"...and {hits - 5} more occurrence(s)",
            )
        )
    return findings


def extract_urls(check: Check, body: str) -> list[str]:
    regions = (
        [m.group(0) for m in check.within.finditer(body)] if check.within else [body]
    )
    found: list[str] = []
    seen: set[str] = set()
    for region in regions:
        for raw in check.pattern.findall(normalise_json_slashes(region)):
            target = raw.strip().rstrip(".,)")
            if target not in seen:
                seen.add(target)
                found.append(target)
    return found


def run_resolve_check(
    check: Check, url: str, body: str, severity: str, pause: float = LINK_PAUSE
) -> list[Finding]:
    host = urlparse(url).netloc.lower()
    findings: list[Finding] = []
    targets = extract_urls(check, body)
    if check.skip_same_host:
        targets = [t for t in targets if urlparse(t).netloc.lower() != host]

    dropped = max(0, len(targets) - check.limit)
    for target in targets[: check.limit]:
        code, note = status_of(target)
        if code not in check.allow_status:
            detail = f"HTTP {code} — {target}" if code else f"{note or 'no response'} — {target}"
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, detail)
            )
        time.sleep(pause)

    if dropped:
        findings.append(
            Finding(
                url,
                check.slug,
                check.id,
                "warn",
                "link check truncated",
                f"{dropped} URL(s) beyond limit={check.limit} were NOT checked",
            )
        )
    return findings


def build_paths(check: Check, url: str) -> list[str]:
    """Absolute URLs for this check's paths, on the target's own origin."""
    parts = urlparse(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    return [origin + path for path in check.paths]


def run_paths_check(
    check: Check, url: str, severity: str, pause: float = LINK_PAUSE
) -> list[Finding]:
    """A URL nobody links to is a URL nothing else can check.

    Everything else in this sweep reads the page it fetched. Only this check can
    catch the address printed on a conference QR code going dead, because that
    address has no inbound link, no analytics until someone tries it, and no
    crawler path to find it.
    """
    findings: list[Finding] = []
    for target in build_paths(check, url):
        code, note = status_of(target)
        if code not in check.allow_status:
            detail = f"HTTP {code} — {target}" if code else f"{note or 'no response'} — {target}"
            findings.append(
                Finding(url, check.slug, check.id, severity, check.message, detail)
            )
        time.sleep(pause)
    return findings


def run_check(check: Check, url: str, body: str, severity: str, **kw) -> list[Finding]:
    if check.kind == "resolve_urls":
        return run_resolve_check(check, url, body, severity, **kw)
    if check.kind == "require_paths":
        return run_paths_check(check, url, severity, **kw)
    return run_regex_check(check, url, body, severity)


# ----------------------------------------------------------------------------
# self-test: every rule proves its own patterns


def self_test(standards: list[Standard]) -> list[str]:
    """Each check must flag its violating samples and pass its clean ones."""
    problems: list[str] = []
    for standard in standards:
        for check in standard.checks:
            if check.kind == "require_paths":
                for i, sample in enumerate(check.examples["builds"]):
                    got = build_paths(check, sample["target"])
                    want = sample["urls"]
                    if got != want:
                        problems.append(
                            f"{check.ref} builds[{i}]: expected {want}, got {got}"
                        )
                continue

            if check.kind == "resolve_urls":
                for i, sample in enumerate(check.examples["extracts"]):
                    got = extract_urls(check, sample["html"])
                    want = sample["urls"]
                    if got != want:
                        problems.append(
                            f"{check.ref} extracts[{i}]: expected {want}, got {got}"
                        )
                continue

            for sample in check.examples["violating"]:
                if not run_regex_check(check, "self-test", sample, standard.severity):
                    problems.append(
                        f"{check.ref}: pattern did NOT flag a violating sample — "
                        f"{sample[:90]!r}. A check that matches nothing reports every "
                        f"site clean forever."
                    )
            for sample in check.examples["clean"]:
                hits = run_regex_check(check, "self-test", sample, standard.severity)
                if hits:
                    problems.append(
                        f"{check.ref}: pattern falsely flagged a clean sample — "
                        f"{sample[:90]!r}"
                    )
    return problems


# ----------------------------------------------------------------------------
# reporting


Target = tuple[str, tuple[str, ...]]


def applies_to_target(standard: Standard, tags: tuple[str, ...]) -> bool:
    """A rule with target_tags only runs on pages carrying one of them."""
    if not standard.target_tags:
        return True
    return bool(set(standard.target_tags) & set(tags))


def sweep(
    targets: list[Target], standards: list[Standard]
) -> tuple[list[Finding], list[str], dict[str, list[str]]]:
    findings: list[Finding] = []
    failures: list[str] = []
    skipped: dict[str, list[str]] = {}
    checkable = [s for s in standards if s.checks]

    for url, tags in targets:
        try:
            status, body = fetch(url)
        except urllib.error.HTTPError as exc:
            failures.append(f"{url}: HTTP {exc.code} — not swept")
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{url}: {exc.__class__.__name__}: {exc} — not swept")
            continue

        if status != 200:
            failures.append(f"{url}: HTTP {status} — not swept")
            continue

        for standard in checkable:
            if not applies_to_target(standard, tags):
                skipped.setdefault(url, []).append(
                    f"{standard.slug} (needs tag: {'/'.join(standard.target_tags)})"
                )
                continue
            for check in standard.checks:
                findings.extend(run_check(check, url, body, standard.severity))
    return findings, failures, skipped


def report(
    targets: list[Target],
    standards: list[Standard],
    findings: list[Finding],
    failures: list[str],
    skipped: dict[str, list[str]],
) -> None:
    checkable = [s for s in standards if s.checks]
    judgement = [s for s in standards if not s.checks]

    print(
        f"Fleet check — {len(targets)} page(s), "
        f"{len(checkable)} machine-checkable rule(s)"
    )
    print()

    for url, _tags in targets:
        page = [f for f in findings if f.url == url]
        failed = [f for f in failures if f.startswith(url + ":")]
        missed = skipped.get(url, [])
        if failed:
            print(f"  {url}\n    NOT SWEPT — {failed[0].split(': ', 1)[1]}")
            continue
        if not page:
            ran = len(checkable) - len(missed)
            print(f"  {url}\n    clean against all {ran} applicable rule(s)")
            for note in missed:
                print(f"    not applied: {note}")
            continue
        print(f"  {url}")
        for note in missed:
            print(f"    not applied: {note}")
        for finding in page:
            flag = "FAIL" if finding.blocking else "warn"
            print(f"    [{flag}] {finding.standard}/{finding.check}: {finding.message}")
            print(f"           {finding.detail}")
        print()

    blocking = [f for f in findings if f.blocking]
    warnings = [f for f in findings if not f.blocking]
    print()
    print(f"{len(blocking)} blocking, {len(warnings)} warning, {len(failures)} not swept")

    if judgement:
        print()
        print("Not verified by this sweep — judgement rules, enforced by reading:")
        for standard in judgement:
            print(f"  - {standard.slug}: {standard.title}")


def read_targets(path: Path) -> list[Target]:
    """One URL per line; optional comma-separated tags after whitespace."""
    targets: list[Target] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        url, _, raw_tags = line.partition(" ")
        tags = tuple(
            tag.strip() for tag in raw_tags.replace(",", " ").split() if tag.strip()
        )
        targets.append((url.strip(), tags))
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="pages to sweep")
    parser.add_argument("--targets", type=Path, help="file of URLs, one per line")
    parser.add_argument(
        "--lint", action="store_true", help="parse standards and compile every regex"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run every check against its own examples (no network)",
    )
    parser.add_argument(
        "--tag",
        nargs="+",
        default=[],
        help="tags to apply to URLs given on the command line",
    )
    parser.add_argument("--json", type=Path, help="also write findings as JSON")
    args = parser.parse_args()

    try:
        standards = load_standards()
    except StandardError as exc:
        print(f"standards/ is malformed: {exc}")
        return 2

    if args.lint or args.self_test:
        checks = sum(len(s.checks) for s in standards)
        print(f"Parsed {len(standards)} standard(s), {checks} check(s).")
        for standard in standards:
            mark = f"{len(standard.checks)} check(s)" if standard.checks else "judgement"
            print(f"  - {standard.slug} [{standard.severity}] {mark}")
        if args.lint and not args.self_test:
            return 0

        problems = self_test(standards)
        if problems:
            print()
            print(f"Self-test FAILED — {len(problems)} problem(s):")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print()
        print("Self-test passed: every check flags its violating samples and clears "
              "its clean ones.")
        return 0

    cli_tags = tuple(args.tag)
    targets: list[Target] = [(url, cli_tags) for url in args.urls]
    if args.targets:
        targets += read_targets(args.targets)
    if not targets:
        parser.error("give at least one URL, or --targets, or --lint/--self-test")

    findings, failures, skipped = sweep(targets, standards)
    report(targets, standards, findings, failures, skipped)

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "targets": [{"url": u, "tags": list(g)} for u, g in targets],
                    "findings": [asdict(f) for f in findings],
                    "not_swept": failures,
                    "not_applied": skipped,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nJSON written to {args.json}")

    if failures:
        return 2
    return 1 if any(f.blocking for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
