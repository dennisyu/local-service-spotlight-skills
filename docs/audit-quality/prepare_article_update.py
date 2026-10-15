"""Prepare a content-only WP payload from a fresh authenticated preimage.

No network or publication. The accepted publisher supplies current context=edit
JSON and the independently captured public REST baseline. Never use rendered
HTML as the editable preimage. Reconcile source drift before trying again.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-preimage", required=True)
    p.add_argument("--public-baseline", required=True)
    p.add_argument("--addition", required=True)
    p.add_argument("--replace-existing-block", help="Exact reviewed native Custom HTML block; never a rendered snapshot")
    p.add_argument("--output-dir", required=True)
    a=p.parse_args()
    current=json.loads(Path(a.native_preimage).read_text())
    baseline=json.loads(Path(a.public_baseline).read_text())
    for k in ["id", "slug", "status", "author", "modified_gmt", "link"]:
        require(current[k] == baseline[k], "Source drift in "+k)
    for k in ["title", "date", "categories", "tags", "featured_media", "excerpt"]:
        if k in current or k in baseline:
            native_value=current.get(k)
            public_value=baseline.get(k)
            if k in ["title", "excerpt"]:
                for value in [native_value,public_value]:
                    require(isinstance(value,str) or (isinstance(value,dict) and isinstance(value.get("rendered"),str)), "Missing rendered metadata in "+k)
                native_value=native_value["rendered"] if isinstance(native_value,dict) else native_value
                public_value=public_value["rendered"] if isinstance(public_value,dict) else public_value
            require(native_value == public_value, "Metadata drift in "+k)
    require(current["id"] == 112500 and current["slug"] == "how-we-audit" and current["status"] == "publish", "Wrong post identity or publication state")
    require(current["link"] == "https://blitzmetrics.com/how-we-audit/", "Wrong destination")
    # WordPress adds this loading hint only in the anonymous view. Normalize
    # that exact image attribute; source, text and all other markup stay guarded.
    def comparable_rendered(value):
        require(isinstance(value,str), "Missing rendered content")
        return re.sub(r'(<img\b[^>]*?) fetchpriority="high"(?=[ >])', r"\1", value)
    require(comparable_rendered(current["content"]["rendered"]) == comparable_rendered(baseline["content"]["rendered"]), "Rendered source drift")
    raw=current["content"]["raw"]
    addition=Path(a.addition).read_text()
    marker='id="universal-audit-quality-gate"'
    require(addition.count(marker) == 1, "Addition marker missing or duplicated")
    if a.replace_existing_block:
        previous=Path(a.replace_existing_block).read_text()
        require(previous.startswith("<!-- wp:html -->") and previous.rstrip().endswith("<!-- /wp:html -->"), "Replacement preimage must be a complete native Custom HTML block")
        require(previous.count(marker) == 1 and raw.count(marker) == 1, "Existing marker missing or duplicated")
        require(raw.count(previous) == 1, "Reviewed native block drifted or duplicated")
        candidate=raw.replace(previous, addition, 1)
    else:
        require(marker not in raw, "Addition already exists; reconcile instead of appending")
        candidate=raw+"\n"+addition
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    require(not any((out/f).exists() for f in ["content-only-payload.json","rollback-payload.json","guard.json"]), "Output exists; inspect rather than overwrite")
    with (out/"content-only-payload.json").open("x") as f: f.write(json.dumps({"content":candidate},ensure_ascii=False))
    with (out/"rollback-payload.json").open("x") as f: f.write(json.dumps({"content":raw},ensure_ascii=False))
    guard={"post_id":112500,"preimage_sha256":sha(raw),"candidate_sha256":sha(candidate),"addition_sha256":sha(addition),"metadata":{k:current[k] for k in ["slug","status","author","modified_gmt","title","link","date","categories","tags","featured_media","excerpt"] if k in current},"write":"NOT_ATTEMPTED","next":"Publisher must re-read exact raw source/metadata immediately before content-only write; stop on drift. Require rendered-design acceptance and all applicable authority gates first. Rollback only if current content/metadata match this deployment; preserve later edits."}
    with (out/"guard.json").open("x") as f: f.write(json.dumps(guard,indent=2))
    print(json.dumps({"status":"PAYLOAD_PREPARED_NOT_PUBLISHED","preimage_sha256":sha(raw),"candidate_sha256":sha(candidate)}))


if __name__ == "__main__":main()
