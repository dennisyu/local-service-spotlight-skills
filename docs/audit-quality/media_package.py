"""Integrity/relationship checks for asserted media packages, never source truth."""

import hashlib
import json

def review_scope(asset, evidence):
    """Bind semantic judgment to asset declarations and exact source receipt."""
    payload = {'asset': asset, 'source': evidence.get(asset.get('source_evidence_id'))}
    return asset.get('id', 'MISSING') + '#' + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def package_scope(package, evidence, actions):
    payload = {'package': package, 'sources': [evidence.get(a['source_evidence_id']) for a in package['assets']],
               'actions': [actions.get(h['action_id']) for h in package['greatest_hits']]}
    return package['artifact_id'] + '#' + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def hit_scope(hit, asset, evidence, actions):
    payload = {'hit': hit, 'asset': asset, 'source': evidence.get(hit['source_evidence_id']), 'action': actions.get(hit['action_id'])}
    return hit['id'] + '#' + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def validate(r, evidence, artifacts, actions, receipt):
    errors = []
    def need(ok, reason):
        if not ok:
            errors.append('media package: ' + reason)
    packages = r['media_package']
    if r['product_profile']['id'] == 'bulk-screening':
        need(not packages, 'SCREENING cannot claim accepted human report package')
        return errors
    required = {a['id'] for a in artifacts.values() if a['required'] and a['role'] == 'HUMAN_REPORT'}
    need(artifacts.get(r['primary_artifact_id'], {}).get('role') == 'HUMAN_REPORT', 'primary audit must be a human report')
    need(all(a['role'] == 'HUMAN_REPORT' or a['format'] in {'JSON','OTHER'} for a in artifacts.values()), 'PDF/HTML/Markdown cannot use machine-companion waiver')
    ids = [p['artifact_id'] for p in packages]
    need(len(ids) == len(set(ids)) and set(ids) == required, 'every required report needs one complete package; no N/A waiver')
    links = {x['id']: x for x in r['links']}
    def review(eid, target, sha, page=None):
        e = evidence.get(eid, {})
        return bool(receipt(eid, 'MEDIA_PACKAGE_REVIEW', 'media_package', sha=sha,
                            reviewer=r['independent_review']['reviewer_id'])
                    and e.get('reviewer_id') != r['author_id'] and e.get('scope') == target
                    and (page is None or page in e.get('covered_pages', [])))
    for p in packages:
        a = artifacts.get(p['artifact_id'], {})
        digest = a.get('sha256')
        need(p['artifact_sha256'] == digest, 'stale artifact binding')
        need(review(p['review_evidence_id'], package_scope(p, evidence, actions), digest), 'independent semantic package review missing/stale')
        assets = {x['id']: x for x in p['assets']}
        need(len(assets) == len(p['assets']), 'duplicate media ID')
        kinds = {x['kind'] for x in assets.values()}
        need({'AUTHENTIC_PHOTO','REAL_VIDEO','ORIGINAL_THUMBNAIL'} <= kinds, 'authentic photo, real video and original thumbnail all required')
        for x in assets.values():
            src = evidence.get(x['source_evidence_id'], {})
            rights = evidence.get(x['rights_evidence_id'], {})
            need(src.get('kind') == 'SOURCE' and src.get('inspection') == 'CONTENT_INSPECTED'
                 and x['source_date'] == src.get('source_date'), 'source/date/content mismatch: ' + x['id'])
            need(rights.get('kind') in {'SOURCE','AUTHORITY'} and rights.get('inspection') == 'CONTENT_INSPECTED', 'rights evidence missing')
            need(review(x['review_evidence_id'], review_scope(x, evidence), digest, x['page']), 'independent exact-page/source semantic review missing: ' + x['id'])
            need(a.get('page_count') is None or x['page'] <= a['page_count'], 'media page outside final artifact')
            link = links.get(x['link_id'], {})
            need(link.get('material') and link.get('url') == src.get('scope')
                 and all(link.get(k, {}).get('status') == 'PASS' for k in ['reachable','expected_content','recipient_access']), 'exact usable source/recipient link required')
            need(x['tested_target'] == link.get('url'), 'final click/print test must resolve exact source')
            if a.get('format') == 'PDF':
                need(x['navigation_test'] in {'CLICK_AND_QR_DECODED','CLICK_AND_PRINT_URL_READBACK'} and bool(x['print_locator']), 'PDF needs both tested click and usable print URL/decoded QR source')
            if x['kind'] == 'REAL_VIDEO':
                need(x['content_review_method'] in {'FRAMES_AND_TRANSCRIPT','RECORDING_VIEWED_MUTED'} or (x['content_review_method'] == 'VIDEO_IDENTITY_AND_POSTER' and x['claim_basis'] == 'PUBLISHER_DESCRIPTION_ATTRIBUTED'), 'metadata is not recording-content review for derived lessons')
                need(link.get('is_media') and link.get('media_inspected', {}).get('status') == 'PASS'
                     and link.get('media_inspected', {}).get('method') in ({'VIDEO_AT_CITED_LOCATION', 'VIDEO_IDENTITY_AND_POSTER'} if x['claim_basis'] == 'PUBLISHER_DESCRIPTION_ATTRIBUTED' else {'VIDEO_AT_CITED_LOCATION'}), 'real video inspection required; audio/transcript alone cannot replace video')
                need(any(t['kind'] == 'ORIGINAL_THUMBNAIL' and t['video_id'] == x['id'] for t in assets.values()), 'video lacks its original thumbnail')
            else:
                need(x['content_review_method'] == 'IMAGE_INSPECTED', 'actual photo/thumbnail image review required')
            if x['kind'] == 'ORIGINAL_THUMBNAIL':
                need(assets.get(x['video_id'], {}).get('kind') == 'REAL_VIDEO', 'thumbnail points to wrong/missing video ID')
            else:
                need(x['video_id'] is None, 'only thumbnail may declare video parent')
        hits = p['greatest_hits']
        need(bool(hits) and len({h['id'] for h in hits}) == len(hits), 'curated greatest hits required')
        for h in hits:
            x = assets.get(h['asset_id'], {})
            action = actions.get(h['action_id'], {})
            need(x.get('kind') in {'AUTHENTIC_PHOTO','REAL_VIDEO'}
                 and h['source_evidence_id'] == x.get('source_evidence_id') and h['source_date'] == x.get('source_date'), 'greatest hit must resolve exact dated authentic asset')
            need(h['source_evidence_id'] in action.get('evidence_ids', []) and bool(action.get('finding_ids')), 'greatest hit must drive a related evidence-linked action')
            need(review(h['review_evidence_id'], hit_scope(h, x, evidence, actions), digest, x.get('page')), 'greatest-hit/action usefulness requires independent semantic review')
    return errors
