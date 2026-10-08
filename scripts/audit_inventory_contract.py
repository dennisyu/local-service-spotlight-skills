#!/usr/bin/env python3
"""Validate declared inventory units and artifact acceptance receipts, not source truth."""
import argparse
import json
import math
from pathlib import Path

class ContractError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise ContractError(message)

def integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0

def validate(doc):
    require(doc.get('method_version') == 'AUDIT-METHOD-2026.10.02', 'method version mismatch')
    scope = doc.get('scope', {})
    require(bool(scope.get('snapshot')) and bool(scope.get('enumerated_sources')), 'dated enumeration scope required')
    require(scope.get('completeness') in ('bounded_public_census', 'partial_inventory'), 'declare completeness boundary')
    counts = doc.get('counts', {})
    require(bool(counts), 'count register required')
    for name, row in counts.items():
        require(row.get('unit') in ('feed_entry', 'published_release', 'public_asset', 'site_post', 'external_appearance', 'raw_session'), f'{name}: undefined unit')
        require(integer(row.get('value')) or row.get('value') == 'UNKNOWN', f'{name}: count must be an integer or UNKNOWN')
        require(bool(row.get('source')), f'{name}: source required')
    for group in doc.get('sums', []):
        total = counts[group['total']]
        members = [counts[k] for k in group['members']]
        require(all(m['unit'] == total['unit'] for m in members), 'cannot add different units')
        require(group.get('disjoint_verified') is True, 'sum needs verified disjoint sets')
        require(all(integer(m['value']) for m in members) and integer(total['value']), 'UNKNOWN cannot become a zero in a sum')
        require(sum(m['value'] for m in members) == total['value'], 'sum arithmetic mismatch')
    raw = [c for c in counts.values() if c['unit'] == 'raw_session']
    require(bool(raw), 'raw holdings state required')
    if any(c['value'] == 'UNKNOWN' for c in raw):
        require(doc.get('reuse_yield') == 'UNKNOWN', 'published uploads cannot establish raw-source reuse yield')
    for edge in doc.get('confirmed_derivatives', []):
        require(edge.get('proof_kind') in ('publisher_parent_link', 'production_session_id'), 'title/guest match is not confirmed parentage')
        require(bool(edge.get('source_id')) and bool(edge.get('child_id')) and bool(edge.get('evidence')), 'parent edge evidence required')
    release = doc.get('pdf_acceptance', {})
    pages = release.get('physical_page_count')
    require(integer(pages) and pages > 0, 'actual PDF page count required')
    require(release.get('inspected_pages') == list(range(1, pages + 1)), 'every actual PDF page must be inspected')
    require(release.get('artifact_sha256') == release.get('accepted_sha256') and len(release.get('artifact_sha256', '')) == 64, 'accepted PDF hash differs')
    require(release.get('geometry_status') == 'PASS' and release.get('visual_status') == 'PASS', 'geometry alone does not prove visual acceptance')
    require(bool(release.get('reviewer')) and bool(release.get('reviewed_utc')), 'dated visual reviewer required')
    for field, minimum in [('minimum_body_points', 10.5), ('minimum_note_points', 9)]:
        value = release.get(field)
        require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= minimum, f'{field}: unreadable type')
    return {'status': 'PASS', 'scope': 'Declared units, sums, parentage evidence types and revision-specific PDF receipt completeness. Does not independently verify source truth or visual judgment.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(validate(json.loads(args.manifest.read_text()))))
    except (ContractError, KeyError, TypeError) as exc:
        raise SystemExit(f'HOLD: {exc}')

if __name__ == '__main__':
    main()
