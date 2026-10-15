"""UAQG decision aid for a structured receipt; semantic review remains required.

Run: python3 check_audit_quality.py run-template.json
Synthetic tests: python3 check_audit_quality.py --self-test
This does not perform evidence, privacy, render or deployment checks.
"""
import copy
import json
import sys
from decimal import Decimal

WEIGHTS = [25, 25, 20, 15, 10, 5]
REQUIRED_CHECKS = {"authority", "privacy", "fidelity", "provenance", "usability", "reproducibility"}


def _assess_v1(receipt):
    if receipt.get("audience") not in {"PRIVATE", "PUBLIC"}:
        raise ValueError("Audience must be PRIVATE or PUBLIC")
    for finding in receipt.get("findings", []):
        if finding.get("severity") not in {"S0", "S1", "S2", "S3"}:
            raise ValueError("Unknown severity")
    quality = receipt["quality"]
    if quality["weights"] != WEIGHTS:
        raise ValueError("This checker supports only UAQG-default-1.0.0")
    ratings = quality["ratings"]
    if len(ratings) != 6:
        raise ValueError("Six ratings required")
    if any(r is not None and (isinstance(r, bool) or r not in [0, 1, 2, 3, 4]) for r in ratings):
        raise ValueError("Integer anchors 0..4 or null required")
    known = sum(Decimal(w) * Decimal(r) / 4 for w, r in zip(WEIGHTS, ratings) if r is not None)
    coverage = sum(w for w, r in zip(WEIGHTS, ratings) if r is not None)
    total = known if coverage == 100 else None
    result = {"known_subtotal": str(known), "assessed_weight": coverage, "total": None if total is None else str(total)}
    release = receipt.get("release", {})
    if release.get("attempted") and release.get("observed_harm"):
        return dict(result, decision="INCIDENT_HOLD", next_action="Notify owner and use authorized guarded containment; retain incident receipt")
    reasons = []
    authority = receipt["authority"]
    if not authority.get("verified") or authority.get("current_holds"):
        reasons.append("authority or hold")
    checks = receipt.get("checks", [])
    passed_required = {c.get("name") for c in checks if c.get("required") is True and c.get("status") == "PASS" and c.get("evidence")}
    if not REQUIRED_CHECKS.issubset(passed_required) or any(c.get("status") != "PASS" or not c.get("evidence") for c in checks if c.get("required", True)):
        reasons.append("required checks")
    for finding in receipt.get("findings", []):
        if finding.get("closed"):
            continue
        if finding["severity"] in ["S0", "S1"]:
            reasons.append("unresolved critical or major defect")
        if finding["severity"] == "S2":
            d = finding.get("disposition", {})
            if not all(d.get(k) for k in ["accepted_by", "risk_reason", "owner", "deadline", "completion_test"]):
                reasons.append("unaccepted moderate defect")
    review = receipt["independent_review"]
    candidate_hash = receipt["candidate"].get("sha256")
    if not candidate_hash or review.get("candidate_sha256") != candidate_hash or not review.get("fresh_context") or not review.get("reviewer") or review.get("content_privacy") != "PASS" or review.get("design") != "PASS":
        reasons.append("independent exact-revision review")
    if quality.get("calibration", {}).get("status") != "RECORDED":
        reasons.append("uncalibrated")
    if total is None or total < 85:
        reasons.append("incomplete or below threshold")
    if not all(quality.get("rationales_and_evidence", [])) or len(quality.get("rationales_and_evidence", [])) != 6:
        reasons.append("rating evidence")
    if reasons:
        return dict(result, decision="HOLD", reasons=reasons)
    if not release.get("attempted"):
        return dict(result, decision="RELEASE_READY")
    if release.get("candidate_sha256") != candidate_hash:
        return dict(result, decision="DELIVERY_UNVERIFIED", reasons=["released revision differs"])
    rb = release.get("readback", [])
    required = {"recipient_access", "final_bytes"} if receipt["audience"] == "PRIVATE" else {"anonymous_body", "canonical", "desktop", "mobile", "links", "downloads"}
    passed = {c["name"] for c in rb if c.get("status") == "PASS"}
    if not required.issubset(passed):
        return dict(result, decision="DELIVERY_UNVERIFIED" if receipt["audience"] == "PRIVATE" else "DEPLOYED_UNVERIFIED")
    return dict(result, decision="PRIVATE_DELIVERED_VERIFIED" if receipt["audience"] == "PRIVATE" else "PUBLISHED_VERIFIED")


def self_test():
    base = {"quality": {"weights": WEIGHTS, "ratings": [4, 3, 4, 4, 3, 3], "rationales_and_evidence": ["synthetic evidence"] * 6, "calibration": {"status": "RECORDED"}}, "authority": {"verified": True, "current_holds": []}, "checks": [{"name": n, "status": "PASS", "required": True, "evidence": "synthetic evidence"} for n in REQUIRED_CHECKS], "findings": [], "candidate": {"sha256": "synthetic-final"}, "independent_review": {"reviewer": "synthetic reviewer", "fresh_context": True, "candidate_sha256": "synthetic-final", "content_privacy": "PASS", "design": "PASS"}, "release": {"attempted": False}, "audience": "PUBLIC"}
    cases = 0
    def check(r, expected):
        nonlocal cases
        actual = assess(r)
        assert actual["decision"] == expected, actual
        cases += 1
        return actual
    assert check(base, "RELEASE_READY")["total"] == "90.00"
    r = copy.deepcopy(base); r["quality"]["ratings"][2] = None
    a = check(r, "HOLD"); assert a["total"] is None and a["assessed_weight"] == 80 and Decimal(a["known_subtotal"]) == 70
    for ratings, expected in [([4, 3, 3, 4, 3, 3], "RELEASE_READY"), ([3, 3, 4, 4, 3, 3], "HOLD"), ([3]*6, "HOLD")]:
        r=copy.deepcopy(base); r["quality"]["ratings"]=ratings;check(r,expected)
    for severity in ["S0", "S1", "S2"]:
        r=copy.deepcopy(base);r["findings"]=[{"severity":severity,"closed":False}];check(r,"HOLD")
    r["findings"][0]["disposition"]={k:"synthetic" for k in ["accepted_by","risk_reason","owner","deadline","completion_test"]};check(r,"RELEASE_READY")
    for target, field, value in [("quality", "calibration", {"status":"NOT_RUN"}), ("independent_review", "candidate_sha256", "old"), ("authority", "current_holds", ["hold"] )]:
        r=copy.deepcopy(base);r[target][field]=value;check(r,"HOLD")
    r=copy.deepcopy(base);r["release"]={"attempted":True,"candidate_sha256":"synthetic-final","readback":[]};check(r,"DEPLOYED_UNVERIFIED")
    r["release"]["observed_harm"]=True;check(r,"INCIDENT_HOLD")
    r["release"]["observed_harm"]=False;r["audience"]="PRIVATE";r["release"]["readback"]=[{"name":n,"status":"PASS"} for n in ["recipient_access","final_bytes"]];check(r,"PRIVATE_DELIVERED_VERIFIED")
    r["audience"]="PUBLIC";check(r,"DEPLOYED_UNVERIFIED")
    r["release"]["readback"]=[{"name":n,"status":"PASS"} for n in ["anonymous_body","canonical","desktop","mobile","links","downloads"]];check(r,"PUBLISHED_VERIFIED")
    for mutate in [lambda x: x.update(checks=[{"name":"optional", "status":"PASS", "required":False, "evidence":"x"}]), lambda x: x["checks"][0].update(evidence=None), lambda x: x["checks"][0].update(required=False)]:
        r=copy.deepcopy(base);mutate(r);check(r,"HOLD")
    for mutate in [lambda x: x.update(audience="TYPO"), lambda x: x.update(findings=[{"severity":"TYPO"}])]:
        r=copy.deepcopy(base);mutate(r)
        try: assess(r)
        except ValueError: cases += 1
        else: raise AssertionError("Invalid enum did not fail closed")
    print(json.dumps({"synthetic_cases_passed":cases,"scope":"Decision logic only; no semantic, render or live checks"}))


def _schema_errors(value, spec, root, path='$'):
    """Validate the closed, documented subset used by tier-receipt.schema.json.

    No dependencies. Unsupported schema assertions fail closed rather than being
    ignored. This is not a general JSON Schema implementation.
    """
    import math
    import re
    allowed = {'$schema', '$id', '$defs', 'title', '$ref', 'type', 'const', 'enum',
               'properties', 'required', 'additionalProperties', 'items', 'minItems',
               'minLength', 'pattern', 'minimum', 'maximum', 'maxItems'}
    if set(spec) - allowed:
        return [path + ': unsupported schema assertion']
    if '$ref' in spec:
        prefix = '#/$defs/'
        if not spec['$ref'].startswith(prefix):
            return [path + ': unsupported schema reference']
        return _schema_errors(value, root['$defs'][spec['$ref'][len(prefix):]], root, path)
    errors = []
    types = {'object': lambda v: type(v) is dict, 'array': lambda v: type(v) is list,
             'string': lambda v: type(v) is str, 'boolean': lambda v: type(v) is bool,
             'integer': lambda v: type(v) is int,
             'number': lambda v: type(v) in (int, float) and math.isfinite(v),
             'null': lambda v: v is None}
    wanted = spec.get('type')
    if wanted:
        wanted = [wanted] if isinstance(wanted, str) else wanted
        if not any(types[t](value) for t in wanted):
            return [path + ': invalid type']
    if 'const' in spec and (type(value) is not type(spec['const']) or value != spec['const']):
        errors.append(path + ': unexpected constant')
    if 'enum' in spec and value not in spec['enum']:
        errors.append(path + ': unknown enum')
    if type(value) is dict:
        props = spec.get('properties', {})
        errors += [path + '.' + k + ': missing required field' for k in spec.get('required', []) if k not in value]
        if spec.get('additionalProperties') is False:
            errors += [path + '.' + k + ': undeclared field' for k in value if k not in props]
        for k in value.keys() & props.keys():
            errors += _schema_errors(value[k], props[k], root, path + '.' + k)
    if type(value) is list:
        if len(value) < spec.get('minItems', 0) or len(value) > spec.get('maxItems', len(value)):
            errors.append(path + ': insufficient items')
        for i, item in enumerate(value):
            errors += _schema_errors(item, spec.get('items', {}), root, '%s[%d]' % (path, i))
    if type(value) is str:
        if len(value.strip()) < spec.get('minLength', 0):
            errors.append(path + ': blank text')
        if 'pattern' in spec and not re.fullmatch(spec['pattern'], value):
            errors.append(path + ': pattern mismatch')
    if type(value) in (int, float):
        if not math.isfinite(value):
            errors.append(path + ': nonfinite number')
        if value < spec.get('minimum', value) or value > spec.get('maximum', value):
            errors.append(path + ': outside range')
    return errors


def assess_tier(r):
    """Additional receipt assertions; never proof of the underlying observations."""
    import hashlib
    from pathlib import Path
    root = Path(__file__).parent
    schema = json.loads((root / 'tier-receipt.schema.json').read_text())
    errors = _schema_errors(r, schema, schema)
    if errors:
        return {'decision': 'HOLD', 'reasons': errors, 'scope': 'Receipt consistency only'}
    profiles = json.loads((root / 'product-profiles.json').read_text())
    def need(ok, reason):
        if not ok:
            errors.append(reason)
    def unique(rows, name):
        ids = [x[name] for x in rows]
        need(len(ids) == len(set(ids)), 'duplicate ' + name)
        return {x[name]: x for x in rows}
    evidence = unique(r['evidence'], 'id')
    from datetime import date, datetime
    for e in r['evidence']:
        try:
            date.fromisoformat(e['source_date'])
            for field in ['observed_at', 'retrieved_at']:
                dt = datetime.fromisoformat(e[field].replace('Z','+00:00'))
                need(dt.tzinfo is not None, 'source time requires timezone')
        except ValueError:
            need(False, 'invalid source date/time')
    artifacts = unique(r['artifacts'], 'id')
    unique(r['defects'], 'id')
    claims = unique(r['claims'], 'id')
    actions = unique(r['actions'], 'id')
    checks = unique(r['checks'], 'name')
    for e in r['evidence']:
        if e['kind'] in {'PRIVACY_REVIEW', 'RENDER_REVIEW', 'INDEPENDENT_REVIEW'}:
            need(bool(e['reviewer_id']) and e['reviewer_id'] != r['author_id'], 'review evidence needs independent reviewer')
    profile = r['product_profile']
    bulk = profile['id'] == 'bulk-screening'
    need(profile['agreement'] == 'AGREED', 'product scope not agreed')
    need(r['authority']['verified'] is True and not r['authority']['current_holds'], 'authority or hold')
    need(set(profile['required_outputs']) and len(profile['required_outputs']) == len(set(profile['required_outputs'])), 'duplicate/empty required outputs')
    need(set(profile['required_outputs']) == {a['id'] for a in r['artifacts'] if a['required']}, 'required artifact set differs from product contract')
    primary = artifacts.get(r['primary_artifact_id'])
    need(primary is not None and primary['required'] and primary['sha256'] == r['candidate']['sha256'], 'primary final artifact mismatch')
    final_hash = r['candidate']['sha256']
    if not bulk:
        need(r['identity']['status'] == 'RESOLVED', 'unresolved identity ambiguity')
    need(r['identity']['receipt_id'] in evidence and evidence[r['identity']['receipt_id']]['kind'] == 'IDENTITY_MAPPING', 'identity receipt missing or wrongly typed')
    def receipt(eid, kind, purpose=None, sha=final_hash, reviewer=None):
        e = evidence.get(eid)
        return bool(e and e['kind'] == kind and e['inspection'] == 'CONTENT_INSPECTED'
                    and (purpose is None or e['purpose'] == purpose)
                    and (sha is None or e['artifact_sha256'] == sha)
                    and (reviewer is None or e['reviewer_id'] == reviewer))
    for name, kind in profiles['required_checks'].items():
        c = checks.get(name)
        need(c is not None and c['status'] == 'PASS' and c['artifact_sha256'] == final_hash
             and bool(c['evidence_ids']) and all(receipt(e, kind, name) for e in c['evidence_ids']),
             'missing/failed/incorrectly typed required check: ' + name)
    need(set(checks) == set(profiles['required_checks']), 'required check manifest changed')
    allow = r['allowance']
    need(allow['state'] == 'AVAILABLE', 'allowance unknown or exhausted; authorize a new contract before resuming')
    if allow['consumed'] is not None and allow['limit'] is not None:
        need(allow['consumed'] <= allow['limit'], 'allowance exceeded')
    stages = {x['stage'] for x in r['routing']}
    need(stages == {'RETRIEVAL', 'PARSING', 'ARITHMETIC', 'IDENTITY', 'SYNTHESIS', 'LAYOUT', 'FINAL_REVIEW'}, 'routing stages missing')
    for route in r['routing']:
        need(receipt(route['capability_evidence_id'], 'CAPABILITY_TEST', 'routing'), 'missing typed routing capability evidence')
        need(route['source_access'] != 'MISSING', 'retrieve missing source; stronger model does not supply access')
    if r['claim_scope'] == 'NO_FINDINGS_SCREENING':
        need(bulk and bool(r['no_findings_reason']) and not r['claims'] and not r['actions'], 'empty claims permitted only for explicit no-findings screening')
    else:
        need(bool(r['claims']) and any(c['material'] for c in r['claims']), 'material claims missing')
    for c in r['claims']:
        need(all(e in evidence and evidence[e]['kind'] in {'SOURCE', 'AUTHORITY'} for e in c['evidence_ids']), 'unresolved or wrong-type claim evidence')
        if c['type'] == 'UNKNOWN':
            need(bool(c['limitation']) and c['evidence_state'] in {'UNKNOWN', 'NOT_CHECKED', 'BLOCKED'}, 'UNKNOWN needs visible limitation')
            need(bool(c['next_verification']), 'UNKNOWN needs next verification')
        else:
            need(c['evidence_state'] not in {'UNKNOWN', 'NOT_CHECKED', 'BLOCKED'}, 'claim has uninspected evidence state')
            if c['material']:
                need(bool(c['evidence_ids']), 'material claim has no sources')
                # Content inspection cannot be bypassed by false/omitted media flag.
                need(all(evidence.get(e, {}).get('inspection') == 'CONTENT_INSPECTED' for e in c['evidence_ids']), 'material claim supported only by metadata/uninspected source')
                need(bool(c['action_ids']) and all(a in actions for a in c['action_ids']), 'material finding missing action/test')
        if c['requires_content_inspection']:
            need(bool(c['evidence_ids']) and all(evidence.get(e, {}).get('inspection') == 'CONTENT_INSPECTED' for e in c['evidence_ids']), 'required content inspection absent')
        if c['type'] in {'PROPOSED', 'DECIDED'} or c['evidence_state'] in {'INFERRED', 'REPORTED'}:
            need(bool(c['limitation']) and bool(c['next_verification']), 'attributed/proposed/decided claim needs limitation and test')
        if c['type'] == 'DECIDED':
            need(any(evidence.get(e, {}).get('kind') == 'AUTHORITY' for e in c['evidence_ids']), 'DECIDED needs decision record')
    for a in r['actions']:
        need(all(f in claims and a['id'] in claims[f]['action_ids'] for f in a['finding_ids']), 'action/finding cross-reference mismatch')
        need(all(e in evidence for e in a['evidence_ids']), 'action evidence unresolved')
        metric = a['business_metric']
        need(metric['baseline'] is None or metric['source'] is not None, 'measured business baseline lacks source')
    for a in r['artifacts']:
        if a['format'] == 'PDF' and a['required']:
            need(a['page_count'] is not None, 'required PDF page count missing')
            pages = [v['page'] for v in a['visual_manifest']]
            need(a['page_count'] is not None and set(pages) == set(range(1, a['page_count'] + 1)) and len(pages) == len(set(pages)), 'PDF visual-function manifest must cover every human-facing page exactly once')
        if a['id'] == r['primary_artifact_id'] and profile['contracted_pages'] is not None:
            need(a['page_count'] == profile['contracted_pages'] and bool(profile['blueprint_ref']), 'contracted page count/blueprint changed')
        for v in a['visual_manifest']:
            need(all(e in evidence for e in v['source_ids']), 'visual evidence unresolved')
            need(receipt(v['render_receipt_id'], 'RENDER_REVIEW', sha=a['sha256']) and v['page'] in evidence.get(v['render_receipt_id'], {}).get('covered_pages', []), 'visual render review missing or stale')
    for link in r['links']:
        for field in ['reachable', 'expected_content', 'recipient_access', 'media_inspected']:
            state = link[field]
            need(state['evidence_id'] in evidence, 'link evidence missing: ' + field)
            if state['status'] == 'N/A':
                need(bool(state['reason']), 'N/A link check needs reason')
        if link['material']:
            need(all(link[k]['status'] == 'PASS' for k in ['reachable', 'expected_content', 'recipient_access']), 'material link unavailable/wrong content/recipient blocked')
            if link['is_media']:
                media = link['media_inspected']
                need(media['status'] == 'PASS' and media['method'] not in {'OEMBED', 'METADATA_ONLY', 'THUMBNAIL'}, 'metadata is not media inspection')
                need(evidence.get(media['evidence_id'], {}).get('inspection') == 'CONTENT_INSPECTED', 'media source not inspected')
    closures = unique(r['closure_receipts'], 'id')
    for defect in r['defects']:
        if defect['closed']:
            cr = closures.get(defect['closure_review_receipt'])
            need(bool(cr and cr['finding_id'] == defect['id'] and cr['artifact_sha256'] == final_hash
                      and cr['reviewer_id'] != r['author_id'] and cr['fresh_context']
                      and all(e in evidence for e in cr['evidence_ids'])
                      and receipt(cr['id'], 'FINDING_CLOSURE', 'closure', reviewer=cr['reviewer_id'])), 'closed defect lacks typed exact closure review')
        if defect['severity'] in {'S0', 'S1'}:
            need(defect['closed'], 'hard defect open or closure unverified')
    for name, t in r['timing'].items():
        if t['state'] == 'UNKNOWN':
            need(t['value'] is None, 'UNKNOWN timing/cost must be null: ' + name)
        else:
            need(t['value'] is not None and bool(t['method']) and t['evidence_id'] in evidence, 'timing/cost measurement lacks evidence: ' + name)
        if name == 'actual_cost' and t['value'] is not None:
            need(t['state'] == 'MEASURED' and t['unit'] != 'UNKNOWN', 'actual cost must be measured')
    review = r['independent_review']
    need(review['candidate_sha256'] == final_hash, 'top-level review covers stale hash')
    if r['release']['attempted']:
        need(r['release']['candidate_sha256'] == final_hash, 'released artifact differs')
        for rb in r['release']['readback']:
            need(receipt(rb['evidence'], 'DELIVERY_READBACK', 'delivery'), 'readback lacks typed exact-revision evidence')
    if bulk:
        batch = r['batch']
        need(batch is not None, 'bulk population/sample receipt missing')
        if batch:
            records = unique(batch['records'], 'id')
            need(len(batch['population_ids']) == len(set(batch['population_ids']))
                 and set(batch['population_ids']) == set(records), 'bulk records differ from frozen population manifest')
            sample = batch['random_sample']
            need(sample['sample_size'] <= len(records), 'sample larger than population')
            ranked = sorted(records, key=lambda k: hashlib.sha256((sample['seed'] + '\0' + k).encode()).hexdigest())
            need(sample['selected_ids'] == ranked[:sample['sample_size']], 'random sample does not match frozen population and seed')
            need(len(sample['reviewed_ids']) == len(set(sample['reviewed_ids'])) and set(sample['reviewed_ids']) == set(sample['selected_ids']), 'sample review incomplete')
            for record in batch['records']:
                need(record['mechanical_status'] == 'PASS' and record['mechanical_evidence_id'] in evidence, 'every bulk record needs mechanical validation')
                need(record['identity_status'] == 'RESOLVED' or record['flagged'], 'ambiguous/unknown identity must be flagged')
                rr = record['review']
                reviewed = bool(rr and rr['status'] == 'PASS' and rr['fresh_context'] and rr['reviewer_id'] != r['author_id']
                                and rr['artifact_sha256'] == record['artifact_sha256'] and receipt(rr['evidence_id'], 'INDEPENDENT_REVIEW', sha=record['artifact_sha256'], reviewer=rr['reviewer_id']))
                if record['flagged'] or record['id'] in sample['selected_ids']:
                    need(reviewed, 'flagged/sample record lacks exact independent review: ' + record['id'])
                need(record['label'] == ('REVIEWED_SCREENING' if reviewed else 'SCREENING'), 'batch sample mislabeled as population/individual review')
        need(all(x is None for x in r['quality']['ratings']) and r['quality']['total'] is None, 'screening cannot claim calibrated accepted report score')
        need(r['release']['attempted'] is False, 'bulk checker does not authorize or verify external delivery')
        decision = 'SCREENING'
        total = None
    else:
        need(r['batch'] is None, 'diagnostic/full cannot use batch-sample acceptance')
        need(review['status'] == 'PASS' and review['fresh_context'] is True
             and review['reviewer_id'] is not None and review['reviewer_id'] != r['author_id'], 'missing independent reviewer/author or self-review')
        by_artifact = unique(review['artifacts'], 'artifact_id')
        need(set(by_artifact) == set(profile['required_outputs']), 'review does not cover every required final artifact')
        for aid in profile['required_outputs']:
            a = artifacts.get(aid); ar = by_artifact.get(aid)
            need(bool(a and ar and ar['sha256'] == a['sha256'] and ar['coverage'] == 'EXACT_ARTIFACT'
                      and ar['content_privacy'] == 'PASS' and ar['design'] == 'PASS'
                      and receipt(ar['privacy_receipt_id'], 'PRIVACY_REVIEW', sha=a['sha256'], reviewer=review['reviewer_id'])
                      and receipt(ar['render_receipt_id'], 'RENDER_REVIEW', sha=a['sha256'], reviewer=review['reviewer_id'])), 'stale/incomplete/incorrectly typed final review: ' + aid)
        cal = r['quality']['calibration']
        need(cal['status'] == 'RECORDED' and receipt(cal['receipt_id'], 'CALIBRATION_RECORD', 'calibration', sha=None)
             and len(set(cal['anchor_ids'])) >= 3 and all(receipt(e, 'CALIBRATION_RECORD', 'calibration', sha=None) for e in cal['anchor_ids']), 'uncalibrated numeric acceptance')
        need(receipt(review['receipt_id'], 'INDEPENDENT_REVIEW', 'reproducibility', reviewer=review['reviewer_id'])
             and checks.get('reproducibility', {}).get('evidence_ids') == [review['receipt_id']], 'top review and required check receipt differ')
        original = _assess_v1({'audience':r['audience'],'quality':r['quality'],'authority':r['authority'],
                              'checks':[dict(c,evidence=','.join(c['evidence_ids'])) for c in r['checks']],
                              'findings':r['defects'],'candidate':r['candidate'],
                              'independent_review':{'reviewer':review['reviewer_id'],'fresh_context':review['fresh_context'],
                                                    'candidate_sha256': by_artifact.get(r['primary_artifact_id'],{}).get('sha256'),
                                                    'content_privacy':'PASS' if review['status']=='PASS' else 'UNKNOWN',
                                                    'design':'PASS' if review['status']=='PASS' else 'UNKNOWN'},
                              'release':r['release']})
        if original['decision'] == 'HOLD':
            errors.extend(original['reasons'])
        decision = original['decision']; total = original.get('total')
        need((total is None and r['quality']['total'] is None) or (total is not None and r['quality']['total'] is not None and Decimal(str(r['quality']['total'])) == Decimal(total)), 'wrong exact total')
    return {'decision':'HOLD' if errors else decision,'reasons':errors,'total':total,
            'synthetic':r['synthetic'],'scope':'Asserted receipt consistency only; no source, render, independence, adoption or delivery certification'}


def assess(receipt):
    if type(receipt) is not dict:
        return {'decision':'HOLD','reasons':['receipt must be an object']}
    if receipt.get('schema_version') == 'UAQG-TIER-RECEIPT-1.0.0':
        return assess_tier(receipt)
    if receipt.get('standard') == 'UAQG-1.1.0' or 'product_profile' in receipt:
        return {'decision':'HOLD','reasons':['tier receipt schema/version missing or unknown']}
    return _assess_v1(receipt)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        try:
            result = assess(json.load(open(sys.argv[1])))
        except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as error:
            print(json.dumps({"decision":"MALFORMED", "reason":str(error)}))
            sys.exit(2)
        print(json.dumps(result, indent=2))
        if result["decision"] in {"HOLD", "INCIDENT_HOLD", "DEPLOYED_UNVERIFIED", "DELIVERY_UNVERIFIED"}:
            sys.exit(1)
