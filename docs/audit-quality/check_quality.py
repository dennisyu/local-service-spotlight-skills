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


def assess(receipt):
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


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        print(json.dumps(assess(json.load(open(sys.argv[1]))), indent=2))
