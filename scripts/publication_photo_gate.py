#!/usr/bin/env python3
"""Bind a publisher's exact candidate to retained photo and rendered evidence.

This is evidence consistency, never reviewer authentication, source truth,
usage-rights certification or release authority. The publisher supplies its own
candidate hashes and destination URLs, calls admit(), then revalidate() at its
effect boundary. Private evidence must stay outside the published directory.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct
from types import MappingProxyType
from urllib.parse import urlsplit

try:
    from . import page_photo_proof
except ImportError:
    import page_photo_proof

MAX_BYTES = 64 * 1024 * 1024
MAX_JSON = 8 * 1024 * 1024
MAX_AGE_SECONDS = 24 * 60 * 60
HERE = Path(__file__).resolve().parent


class Hold(ValueError):
    """Required evidence is absent, changed, unsupported or inconsistent."""


def need(value, reason):
    if not value:
        raise Hold(reason)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def _read(path, cap=MAX_BYTES):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'regular bounded file required: ' + str(path))
        chunks, length = [], 0
        while chunk := os.read(fd, min(1024 * 1024, cap + 1 - length)):
            chunks.append(chunk)
            length += len(chunk)
            need(length <= cap, 'file exceeds byte limit: ' + str(path))
        after = os.fstat(fd)
        keys = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        need(all(getattr(before, k) == getattr(after, k) for k in keys) and length == before.st_size,
             'file changed while reading: ' + str(path))
        return b''.join(chunks)
    finally:
        os.close(fd)


def _json_bytes(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    need(type(body) is bytes and len(body) <= MAX_JSON, 'bounded JSON bytes required')
    return json.loads(body, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Hold('nonfinite JSON number')))


def _json(path):
    return _json_bytes(_read(path, MAX_JSON))


def _root(path):
    path = Path(path)
    need(path.is_dir() and not path.is_symlink(), 'regular directory required: ' + str(path))
    return path.resolve()


def _file(root, relative):
    need(isinstance(relative, str) and relative and not Path(relative).is_absolute() and
         '..' not in Path(relative).parts, 'relative nonescaping file path required')
    path = root
    for part in Path(relative).parts:
        path /= part
        need(not path.is_symlink(), 'symlink refused: ' + str(path))
    need(path.is_file() and path.resolve().is_relative_to(root), 'missing evidence file: ' + str(path))
    return path


def _private(path, root):
    path = Path(path)
    need(path.is_file() and not path.is_symlink(), 'private evidence file missing: ' + str(path))
    path = path.resolve()
    need(not path.is_relative_to(root), 'private evidence must be outside public root')
    return path


def _capture_file(captures_root, relative, public_root):
    path = _file(captures_root, relative)
    need(not path.resolve().is_relative_to(public_root),
         'private capture file must be outside public root')
    return path


def _url(value, https=False):
    need(isinstance(value, str), 'URL must be text')
    parsed = urlsplit(value)
    need(parsed.scheme in (('https',) if https else ('http', 'https')) and parsed.hostname and
         not parsed.username and not parsed.password and not parsed.fragment, 'unsupported URL')
    return parsed


def _fresh(value):
    need(isinstance(value, str), 'evidence timestamp missing')
    observed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(observed.tzinfo is not None, 'evidence timestamp needs timezone')
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    need(-300 <= age <= MAX_AGE_SECONDS, 'stale or future evidence timestamp')


def _number(value, minimum, maximum=None):
    return (type(value) in (int, float) and math.isfinite(value) and value >= minimum and
            (maximum is None or value <= maximum))


def _image_size(body):
    """Header dimensions only; actual image decoding remains a browser/review fact."""
    if body.startswith(b'\x89PNG\r\n\x1a\n') and len(body) >= 24 and body[12:16] == b'IHDR':
        return struct.unpack('>II', body[16:24])
    if body.startswith(b'\xff\xd8'):
        pos = 2
        while pos + 3 < len(body):
            need(body[pos] == 255, 'malformed JPEG screenshot header')
            while pos < len(body) and body[pos] == 255:
                pos += 1
            need(pos < len(body), 'truncated JPEG screenshot header')
            marker = body[pos]
            pos += 1
            if marker in (1, 0xD8) or 0xD0 <= marker <= 0xD7:
                continue
            need(pos + 2 <= len(body), 'truncated JPEG screenshot segment')
            length = int.from_bytes(body[pos:pos + 2], 'big')
            need(length >= 2 and pos + length <= len(body), 'invalid JPEG screenshot segment')
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                need(length >= 7, 'invalid JPEG screenshot dimensions')
                return int.from_bytes(body[pos + 5:pos + 7], 'big'), int.from_bytes(body[pos + 3:pos + 5], 'big')
            pos += length
    raise Hold('screenshot must retain PNG or JPEG viewport bytes')


def _policy(body):
    return _json_bytes(body.decode().split('---', 2)[1].encode())['rendered_gate']


def _tree(root):
    files = []
    for path in sorted(root.rglob('*')):
        need(not path.is_symlink(), 'symlink in public inventory')
        mode = path.stat().st_mode
        need(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'special file in public inventory')
        if stat.S_ISREG(mode):
            files.append(path)
            need(len(files) <= 10000, 'public inventory exceeds bounded gate')
    return files


@dataclass(frozen=True)
class Commitment:
    root: str
    manifest_path: str
    render_proof_path: str
    captures_root: str
    expected_pages: tuple
    files: tuple
    status: str = 'EVIDENCE_CONSISTENT'


def _admit(root, manifest_path, render_proof_path, captures_root, expected_pages):
    """Raise Hold on any missing/mismatched evidence; never dispatch a publisher."""
    root, captures_root = _root(root), _root(captures_root)
    need(not captures_root.is_relative_to(root), 'captures must be outside public root')
    manifest_path, render_proof_path = _private(manifest_path, root), _private(render_proof_path, root)
    source_files = set(_tree(root))
    code_files = {Path(__file__).resolve(), Path(page_photo_proof.__file__).resolve(),
                  HERE / 'rendered_visual_check.mjs', HERE.parent / 'standards/visuals-above-the-fold.md'}
    # All checks consume this same copied byte set. Hashing live paths before
    # and after a separate parser is insufficient: files can be swapped only
    # for the parser invocation and restored before the final hash pass.
    snapshot = MappingProxyType({path.relative_to(root).as_posix(): _read(path) for path in source_files})
    checked = {path: sha(snapshot[path.relative_to(root).as_posix()]) for path in source_files}
    private_and_code = {path: _read(path) for path in code_files | {manifest_path, render_proof_path}}
    checked.update({path: sha(body) for path, body in private_and_code.items()})
    need(isinstance(expected_pages, dict) and expected_pages, 'publisher candidate mapping required')
    expected = {}
    for name, entry in expected_pages.items():
        need(isinstance(entry, dict) and set(entry) == {'sha256', 'url'}, 'candidate needs exact hash and canonical URL')
        path = _file(root, name)
        need(path.suffix.lower() in ('.html', '.htm') and sha(snapshot[name]) == entry['sha256'], 'candidate page bytes differ: ' + str(name))
        url = _url(entry['url'], https=True)
        need(not url.query, 'canonical URL cannot contain a query')
        expected[name] = dict(entry)
    manifest = _json_bytes(private_and_code[manifest_path])
    proof = _json_bytes(private_and_code[render_proof_path])
    policy = _policy(private_and_code[HERE.parent / 'standards/visuals-above-the-fold.md'])
    pages = manifest['pages']
    need({p['path'] for p in pages} == set(expected), 'publisher candidate/HTML inventory differs')
    for page in pages:
        need(page.get('sha256') == expected[page['path']]['sha256'] == sha(snapshot[page['path']]),
             'photo manifest page differs from publisher candidate snapshot')
    for asset in manifest['assets'].values():
        key = page_photo_proof.relative_key(asset['path'])
        need(sha(snapshot[key]) == asset.get('sha256'), 'photo manifest asset differs from initial byte snapshot')
    errors = page_photo_proof.check(root, manifest, snapshot=snapshot)
    need(not errors, '; '.join(errors))
    need(isinstance(proof, dict) and proof.get('version') == 1 and proof.get('synthetic') is False,
         'real rendered evidence contract required; synthetic or missing contract holds')
    rendered = proof.get('pages')
    need(isinstance(rendered, list) and len(rendered) == len(expected) and
         all(isinstance(x, dict) for x in rendered), 'rendered page inventory missing')
    need(len({x.get('path') for x in rendered}) == len(rendered) and
         {x.get('path') for x in rendered} == set(expected), 'duplicate or omitted rendered page')
    capture_files = {manifest_path, render_proof_path}
    required = {(v['width'], v['height'], js) for v in policy['viewports'] for js in (True, False)}
    for item in rendered:
        name = item['path']
        candidate = expected[name]
        need(item.get('url') == candidate['url'] and item.get('page_sha256') == candidate['sha256'],
             'rendered evidence has wrong page or canonical destination: ' + name)
        collector = item.get('collector')
        need(collector in ('cua', 'rendered_visual_check'), 'unknown rendered collector')
        render_url = _url(item.get('render_url'))
        reference = item['receipt']
        receipt_path = _capture_file(captures_root, reference['path'], root)
        receipt_body = _read(receipt_path, MAX_JSON)
        receipt_sha = sha(receipt_body)
        need(receipt_sha == reference.get('sha256'), 'rendered receipt bytes changed')
        checked[receipt_path] = receipt_sha
        capture_files.add(receipt_path)
        receipt = _json_bytes(receipt_body)
        _fresh(receipt.get('observedAt'))
        need(receipt.get('collector') == collector and receipt.get('requestedUrl') == item['render_url'] and
             receipt.get('geometry') == 'PASS', 'rendered collector or URL mismatch / failed geometry')
        review = item.get('review', {})
        prepared = next(p['prepared_by'] for p in pages if p['path'] == name)
        need(isinstance(review, dict) and page_photo_proof.nonblank(review.get('reviewer')) and
             review['reviewer'] != prepared and review.get('result') == 'PASS' and
             review.get('page_sha256') == candidate['sha256'] and review.get('receipt_sha256') == receipt_sha and
             all(review.get(k) is True for k in ('meaningful_real_photo_checked',
                 'source_permission_and_context_checked', 'title_and_first_screen_checked')),
             'missing or stale independent rendered/source review')
        _fresh(review.get('observed_at'))
        observations, seen, screenshots = receipt.get('observations'), set(), {}
        need(isinstance(observations, list) and len(observations) == len(required), 'four required rendered observations missing')
        for observation in observations:
            viewport = observation['viewport']
            key = viewport['width'], viewport['height'], observation['javaScriptEnabled']
            need(type(key[0]) is int and type(key[1]) is int and type(key[2]) is bool and
                 key in required and key not in seen, 'duplicate, wrong or missing rendered viewport/script case')
            seen.add(key)
            if collector == 'cua' and key[2] is False:
                csp = observation.get('observedContentSecurityPolicy')
                need(observation.get('scriptAvailabilityMethod') == 'http-csp-script-src-none' and
                     observation.get('browserPreferenceChanged') is False and isinstance(csp, str) and
                     any(part.strip().split() == ['script-src', "'none'"] for part in csp.split(';')),
                     'CUA unavailable-script case needs explicit observed CSP and unchanged browser preference')
            final = _url(observation.get('finalUrl'))
            need((final.scheme, final.netloc, final.path, final.query) ==
                 (render_url.scheme, render_url.netloc, render_url.path, render_url.query),
                 'rendered destination changed')
            need(observation.get('geometry') == 'PASS' and type(observation.get('httpStatus')) is int and
                 observation['httpStatus'] == 200 and observation.get('loaded') is True and
                 observation.get('overflow') is False and page_photo_proof.nonblank(observation.get('label')),
                 'unloaded, failed or overflowing rendered content')
            visible = observation['visible']
            for field, minimum in (('width', policy['min_visible_width']), ('height', policy['min_visible_height']),
                    ('fraction', policy['min_visible_fraction']), ('viewportFraction', policy['min_viewport_fraction']),
                    ('unoccludedFraction', policy['min_unoccluded_fraction'])):
                need(_number(visible.get(field), minimum, 1 if field.endswith('raction') else None),
                     'rendered visual below canonical threshold: ' + field)
            paint = observation.get('imagePaint') or observation.get('bbox')
            need(isinstance(paint, dict) and all(_number(paint.get(k), 0.000001)
                 for k in ('width', 'height')) and all(type(paint.get(k)) in (int, float) and
                 math.isfinite(paint[k]) for k in ('x', 'y')), 'painted visual bounds missing')
            possible_width = max(0, min(key[0], paint['x'] + paint['width']) - max(0, paint['x']))
            possible_height = max(0, min(key[1], paint['y'] + paint['height']) - max(0, paint['y']))
            area = visible['width'] * visible['height']
            need(visible['width'] <= possible_width + .001 and visible['height'] <= possible_height + .001 and
                 abs(visible['fraction'] - area / (paint['width'] * paint['height'])) <= .000001 and
                 abs(visible['viewportFraction'] - area / (key[0] * key[1])) <= .000001,
                 'rendered visible-area arithmetic differs from painted bounds')
            need(any(h.get('readableLine') is True and any(
                _number(line.get('fontSize'), policy['min_heading_font_size']) and
                _number(line.get('visibleFraction'), policy['min_heading_line_visible_fraction'], 1) and
                _number(line.get('unoccludedFraction'), policy['min_unoccluded_fraction'], 1)
                for line in h.get('lines', [])) for h in observation.get('headings', [])), 'readable first-screen title missing')
            stable = observation.get('layoutStability', {})
            need(stable.get('status') == 'STABLE' and stable.get('matchingMeasurementAndScreenshot') is True,
                 'measurement and screenshot were not bound to a stable layout')
            binding = 'response_body' if collector == 'rendered_visual_check' else 'paired_http_capture'
            need(observation.get('sourceBinding') == binding, 'collector source binding mismatch')
            base = Path(reference['path']).parent
            source = observation['sourceCapture']
            source_path = _capture_file(captures_root, (base / source['path']).as_posix(), root)
            source_body = _read(source_path)
            source_sha = sha(source_body)
            need(source_sha == source.get('sha256') == observation.get('sourceSha256') == candidate['sha256'],
                 'actual captured response differs from candidate source')
            need('bytes' not in source or (type(source['bytes']) is int and
                 source['bytes'] == len(source_body)), 'captured response size differs')
            checked[source_path] = source_sha
            screenshot_path = _capture_file(captures_root, (base / observation['screenshot']).as_posix(), root)
            screenshot = _read(screenshot_path)
            need(sha(screenshot) == observation.get('screenshotSha256') and _image_size(screenshot) == key[:2],
                 'screenshot missing, changed or wrong viewport dimensions')
            need(screenshot_path.relative_to(captures_root).as_posix() not in screenshots,
                 'each rendered case needs its own screenshot capture file')
            screenshots[screenshot_path.relative_to(captures_root).as_posix()] = sha(screenshot)
            checked[screenshot_path] = sha(screenshot)
            capture_files.update((source_path, screenshot_path))
        need(seen == required and screenshots == review.get('screenshot_sha256'), 'reviewed screenshot inventory differs')
    need(set(_tree(root)) == source_files, 'public inventory changed during admission')
    files = source_files | capture_files | code_files
    frozen = tuple(sorted((str(path), sha(body := _read(path)), len(body)) for path in files))
    need(all(digest == checked[Path(path)] for path, digest, _ in frozen),
         'source or evidence changed during admission')
    # Check again after the complete read so source/proof drift cannot be hidden
    # by a successful earlier checker invocation.
    for name, entry in expected.items():
        need(sha(_read(_file(root, name))) == entry['sha256'], 'candidate changed during admission')
    return Commitment(str(root), str(manifest_path), str(render_proof_path), str(captures_root),
                      tuple(sorted((n, e['sha256'], e['url']) for n, e in expected.items())), frozen)


def admit(root, manifest_path, render_proof_path, captures_root, expected_pages):
    """Return an immutable consistency commitment or raise Hold; no native effects."""
    try:
        return _admit(root, manifest_path, render_proof_path, captures_root, expected_pages)
    except Hold:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, StopIteration, RecursionError) as exc:
        raise Hold(str(exc)) from exc


def revalidate(commitment):
    need(type(commitment) is Commitment, 'gate-created commitment required')
    current = admit(commitment.root, commitment.manifest_path, commitment.render_proof_path,
                    commitment.captures_root, {n: {'sha256': h, 'url': u} for n, h, u in commitment.expected_pages})
    need(current == commitment, 'public or private evidence changed after admission')
    return commitment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'manifest', 'render-proof', 'captures', 'expected-pages'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        value = admit(args.root, args.manifest, args.render_proof, args.captures, _json(args.expected_pages))
        revalidate(value)
        result = {'status': value.status, 'files': len(value.files), 'release_authority': 'NOT_GRANTED',
                  'limit': 'Retained-byte/declaration consistency; source truth, reviewer origin, permissions and delivery remain separate.'}
    except (OSError, ValueError, TypeError, KeyError, IndexError, StopIteration) as exc:
        result = {'status': 'HOLD', 'errors': [str(exc)], 'release_authority': 'NOT_GRANTED'}
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'HOLD' else 0


if __name__ == '__main__':
    raise SystemExit(main())
