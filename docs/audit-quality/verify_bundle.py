"""Bind UAQG receipts to actual local files. Offline; never sends or publishes.

Receipt assertions still require independent source/privacy/design judgment.
Default production mode rejects synthetic fixtures. Exercise mode cannot mint a
production acceptance. Read only a bounded, explicitly supplied bundle directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import check_quality

VERSION = 'UAQG-BUNDLE-1.0.0'
HASH = re.compile(r'[a-f0-9]{64}')
ACCEPTABLE = {'RELEASE_READY', 'PRIVATE_DELIVERED_VERIFIED', 'PUBLISHED_VERIFIED', 'SCREENING'}
BOUND_FILES = ['verify_bundle.py', 'check_quality.py', 'tier-receipt.schema.json', 'product-profiles.json']


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('nonfinite JSON value: ' + value)
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique, parse_constant=nonfinite)


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def safe_file(root, relative):
    if type(relative) is not str or not relative.strip():
        raise ValueError('missing bundle-relative path')
    name = Path(relative)
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('file must stay within bundle')
    current = root
    for part in name.parts:
        current /= part
        if current.is_symlink():
            raise ValueError('symlinks are not bundle snapshots')
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('not a regular bundle file')
    return resolved


def aliases(path, protected):
    return any(path.samefile(other) for other in protected)


def verify(root, manifest_name, mode='production'):
    errors = []
    result = {'schema_version': VERSION, 'mode': mode, 'decision': 'HOLD',
              'scope': 'File integrity and asserted receipt consistency only; no semantic certification or send authority',
              'reasons': errors}
    try:
        if mode not in {'production', 'exercise'}:
            raise ValueError('unknown mode')
        root = Path(root).resolve(strict=True)
        manifest_path = safe_file(root, manifest_name)
        manifest = read_json(manifest_path)
        if type(manifest) is not dict or set(manifest) != {'schema_version', 'receipt', 'artifacts', 'evidence'} or manifest['schema_version'] != VERSION:
            raise ValueError('unknown bundle manifest schema or fields')
        def checked(entry):
            if type(entry) is not dict or set(entry) != {'path', 'sha256'} or type(entry['sha256']) is not str or not HASH.fullmatch(entry['sha256']):
                raise ValueError('file entry needs path and lowercase SHA256')
            path = safe_file(root, entry['path'])
            actual = sha(path)
            if actual != entry['sha256']:
                raise ValueError('changed file: ' + entry['path'])
            return path, actual
        receipt_path, receipt_hash = checked(manifest['receipt'])
        receipt = read_json(receipt_path)
        if receipt.get('schema_version') != 'UAQG-TIER-RECEIPT-1.0.0':
            raise ValueError('current tier receipt required; legacy/unknown receipt cannot bypass bundle checks')
        if type(receipt.get('synthetic')) is not bool:
            raise ValueError('explicit synthetic boolean required')
        if mode == 'production' and receipt['synthetic']:
            errors.append('synthetic exercise cannot establish production acceptance')
        if mode == 'exercise' and not receipt['synthetic']:
            errors.append('exercise requires synthetic=true')
        # Validate receipt structure before dereferencing artifact/evidence rows.
        schema_path = Path(__file__).with_name('tier-receipt.schema.json')
        schema = read_json(schema_path)
        structural = check_quality._schema_errors(receipt, schema, schema)
        if structural:
            raise ValueError('receipt schema: ' + '; '.join(structural))
        snapshot_rows = receipt.get('bundle_evidence', [])
        snapshot_ids = [row['id'] for row in snapshot_rows]
        if len(set(snapshot_ids)) != len(snapshot_ids) or set(snapshot_ids) != {e['id'] for e in receipt['evidence']}:
            raise ValueError('receipt must bind every evidence snapshot ID and hash')
        bound_evidence = {row['id']: {k: row[k] for k in ['path', 'sha256']} for row in snapshot_rows}
        if bound_evidence != manifest['evidence']:
            raise ValueError('evidence manifest differs from reviewed receipt commitment')
        if mode == 'production' and (receipt['run_id'].upper().startswith('SYNTHETIC')
                                     or receipt['source_revision'].lower().startswith('synthetic-')):
            errors.append('known synthetic fixture cannot establish production acceptance')
        if type(manifest['artifacts']) is not dict or type(manifest['evidence']) is not dict:
            raise ValueError('artifact/evidence manifests must be ID-keyed objects')
        artifact_paths = {safe_file(root, e['path']) for e in manifest['artifacts'].values()}
        for field in ['artifacts', 'evidence']:
            rows = receipt[field]
            ids = [row['id'] for row in rows]
            if len(set(ids)) != len(ids) or set(manifest[field]) != set(ids):
                raise ValueError(field + ' snapshot IDs differ from receipt')
            for row in rows:
                path, digest = checked(manifest[field][row['id']])
                if aliases(path, {manifest_path, receipt_path}):
                    raise ValueError('receipt/manifest cannot stand in for artifact or evidence')
                if field == 'artifacts':
                    if digest != row['sha256'] or Path(row['path']).as_posix() != manifest[field][row['id']]['path']:
                        raise ValueError('artifact snapshot differs from reviewed receipt: ' + row['id'])
                else:
                    if aliases(path, artifact_paths):
                        raise ValueError('final artifact cannot replace evidence capture')
                    snapshot = read_json(path)
                    if type(snapshot) is not dict or set(snapshot) != {'schema_version', 'synthetic', 'evidence_id', 'original_locator', 'capture'}:
                        raise ValueError('evidence snapshot envelope required')
                    if snapshot['schema_version'] != 'UAQG-EVIDENCE-SNAPSHOT-1.0.0' or type(snapshot['synthetic']) is not bool:
                        raise ValueError('evidence snapshot schema/origin invalid')
                    if snapshot['evidence_id'] != row['id'] or snapshot['original_locator'] != row['locator']:
                        raise ValueError('evidence snapshot target differs')
                    if snapshot['synthetic'] != receipt['synthetic']:
                        raise ValueError('evidence origin differs from receipt; separate synthetic exercises')
                    if mode == 'production' and row['locator'].lower().startswith('synthetic-fixture:'):
                        raise ValueError('known synthetic evidence locator')
                    capture_path, _ = checked(snapshot['capture'])
                    if aliases(capture_path, artifact_paths | {manifest_path, receipt_path, path}):
                        raise ValueError('capture must be a separate source/review record')
        assessment = check_quality.assess(receipt)
        result['receipt_decision'] = assessment['decision']
        errors.extend(assessment.get('reasons', []))
        if assessment['decision'] not in ACCEPTABLE:
            errors.append('receipt is not ready for the asserted stage')
        result.update(run_id=receipt['run_id'], receipt_sha256=receipt_hash,
                      manifest_sha256=sha(manifest_path), artifact_count=len(receipt['artifacts']),
                      evidence_count=len(receipt['evidence']), synthetic=receipt['synthetic'],
                      checker_sha256={name: sha(Path(__file__).with_name(name)) for name in BOUND_FILES})
        if not errors:
            result['decision'] = 'EXERCISE_PASS' if mode == 'exercise' else 'BUNDLE_CONSISTENT'
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as error:
        errors.append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='private bundle directory')
    parser.add_argument('--manifest', default='bundle-manifest.json')
    parser.add_argument('--mode', choices=['production', 'exercise'], default='production')
    args = parser.parse_args()
    result = verify(args.root, args.manifest, args.mode)
    print(json.dumps(result, indent=2))
    return 0 if result['decision'] in {'BUNDLE_CONSISTENT', 'EXERCISE_PASS'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
