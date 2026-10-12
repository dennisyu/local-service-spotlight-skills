"""Synthetic, temporary test packet. Never a client audit or visual certificate."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject, ArrayObject, FloatObject, TextStringObject
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from personal_brand_acceptance import input_binding


def make_fixture(base: Path, repo: Path):
    def put(name, data):
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        (base / name).write_bytes(data)
        return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}

    revision = "a" * 40
    install = "https://localservicespotlight.com/install/"
    kit_url = "https://example.org/synthetic-kit"
    m = {"schema_version": 1, "subject_id": "SYNTHETIC-SUBJECT", "author_context": "synthetic-author",
         "source_revision": revision, "guide_hashes": {}, "sources": [], "evidence": [], "claims": [],
         "visuals": [], "pages": [], "actions": [], "lifecycle_claims": [],
         "source_counts": {"unit": "distinct_supporting_urls", "reported": 10, "underlying_records": 10,
                           "citation_occurrences": 50, "engagement_target": None,
                           "target_basis": "Synthetic brief has no numeric source quota"},
         "coverage_crosswalk": {str(n): [n] for n in range(1, 21)}}
    for name in ("SKILL.md", "references/20-page-pdf-blueprint.md", "references/evidence-ledger.md",
                 "references/intake-and-authority-boundary.md", "references/brand-authority-rubric.md",
                 "references/acceptance-tests.md"):
        m["guide_hashes"][name] = hashlib.sha256((repo / "skills/personal-brand-audit" / name).read_bytes()).hexdigest()
    for name in ("ledger", "action_register", "visual_brief"):
        m[name] = put(name + ".txt", "SYNTHETIC testing stand-in; no real evidence or review. " + name)
    supplied_goal = "More qualified consultations in 90 days."
    opening_text = "Avery Sample wants more qualified consultations in 90 days. This audit ranks existing proof for that decision."
    m["brief"] = put("brief.json", {"subject_id": m["subject_id"], "kit_required": True,
                                  "promised_skills": ["evidence-verification"], "source_target": None,
                                  "goal": {"state":"SUPPLIED", "text":supplied_goal,
                                           "capture":put('goal-source.txt',supplied_goal)}})
    m['opening'] = {'page':1,'text':opening_text}
    for i in range(1, 11):
        extract = f"Synthetic source {i} states a test observation."
        m["sources"].append({"id": f"S{i}", "url": f"https://example.org/source/{i}",
                             "final_url": f"https://example.org/source/{i}", "title": f"Synthetic source {i}",
                             "publisher": "Synthetic publisher", "source_class": "first-party",
                             "origin_id": f"moment-{i}", "captured_at": "2026-10-13T00:00:00Z",
                             "capture": put(f"source-{i}.txt", extract)})
        m["evidence"].append({"id": f"E{i}", "source_id": f"S{i}", "finding_type": "OBSERVED",
                              "evidence_state": "OBSERVED", "extract": extract})
    for i in range(1, 51):
        m["claims"].append({"id": f"C{i}", "page": (i - 1) % 20 + 1,
                           "text": f"Synthetic claim {i}.", "evidence_ids": [f"E{(i - 1) % 10 + 1}"]})
    writer = PdfWriter()
    for n in range(1, 21):
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                 NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        text = " ".join(c["text"] for c in m["claims"] if c["page"] == n)
        if n == 1: text = opening_text + " " + text
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 36 700 Td (SYNTHETIC page {n}. {text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
        if n == 17:
            page[NameObject("/Annots")] = ArrayObject([
                DictionaryObject({NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Link"),
                                  NameObject("/Rect"): ArrayObject([FloatObject(v) for v in [36, 600, 300, 620]]),
                                  NameObject("/A"): DictionaryObject({NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject(url)})})
                for url in (install, kit_url)])
    pdf = io.BytesIO(); writer.write(pdf)
    m["pdf"] = put("synthetic.pdf", pdf.getvalue())
    permission = put("synthetic-permission.txt", "SYNTHETIC approval declaration for test only.")
    m["visuals"] = [{"id": "V1", "kind": "photo", "asset": put("synthetic-asset.txt", "Test image stand-in"),
                     "evidence_ids": ["E1"], "caption": "Synthetic caption", "purpose": "Exercise declared photo gate",
                     "reuse_status": "APPROVED", "reuse_receipt": permission, "identity_status": "RESOLVED",
                     "identity_basis": "Synthetic two attributes", "photo_role": "subject", "original_source": "S1"}]
    review = {"pdf_sha256": m["pdf"]["sha256"], "reviewer_context": "synthetic-reviewer", "pages": {}, "gates": {}}
    for gate in ("source_truth", "claim_inventory_complete", "visual_brief", "normal_size_readability", "strategy",
                 "privacy", "cover_identity_provenance", "bespoke_kit", "proof_inventory"):
        review["gates"][gate] = {"status": "PASS", "basis": "Synthetic reviewer declaration; no real acceptance."}
    review['gates']['supplied_goal_fidelity'] = {'status':'PASS','basis':'Synthetic fidelity review',
        'supplied_goal_quote':supplied_goal,'opening_quote':opening_text}
    for n in range(1, 21):
        render = put(f"page-{n}.txt", f"Synthetic page render stand-in {n}")
        m["pages"].append({"page": n, "takeaway": f"Synthetic decision {n}", "layout_family": "test-only",
                            "visual_ids": ["V1"], "body_min_pt": 11, "label_min_pt": 9, "render": render})
        review["pages"][str(n)] = {"render_sha256": render["sha256"], "status": "PASS", "basis": "Synthetic test declaration"}
    m["actions"] = [{"id": "A1", "evidence_ids": ["E1", "E2"], "observation": "Sources say test observations",
                     "consequence": "Test consequence", "next_step": "Inspect exact source", "function": "research",
                     "skill": "evidence-verification", "input": "S1", "destination": "private facts file",
                     "due": "day 7", "human_gate": "No publish/send authority", "acceptance_test": "Source extract matched",
                     "state": "STAGED", "handoff": "Research to content with evidence IDs"}]
    m['proof_inventory'] = []
    for i, values in enumerate(((6,4,8),(5,3,4)),start=1):
        m['proof_inventory'].append({'id':f'P{i}','rank':i,'category':'synthetic appearance',
            'evidence_ids':[f'E{i}'],'claim_ids':[f'C{i}'],'what_source_establishes':f'Synthetic source {i} statement',
            'goal_relevance':'Relevant proof for the fictional consultation buyer; no business result measured',
            'limitations':'Synthetic first-party source; outcome and reuse scope need checking',
            'reuse_permission':'Private synthetic test only','next_action_ids':['A1'],
            'score':{'kind':'ASSET_ANALYST_RATING','rubric':'WHO-WHERE-WHAT-30',
                'dimensions':dict(zip(('who','where','what'),values)),
                'rationale':{k:'Synthetic analyst rationale; no real rating' for k in ('who','where','what')},
                'total':sum(values)}})
    def qr(url, name):
        crop = put(name + "-crop.txt", "Synthetic QR crop " + name)
        return {"printed_url": url, "rendered_crop": crop,
                "decode_receipt": put(name + "-decode.json", {"pdf_sha256": m["pdf"]["sha256"],
                    "crop_sha256": crop["sha256"], "decoded_value": url, "decoder": "synthetic-test",
                    "checked_at": "2026-10-13T00:00:00Z"})}
    m["install_qr"] = qr(install, "install")
    market = json.loads((repo / '.claude-plugin/marketplace.json').read_text())
    manifest_url = 'https://github.com/dennisyu/local-service-spotlight-skills/blob/main/.claude-plugin/marketplace.json'
    m["install_check"] = put("install-check.json", {"guide_url": install, "status": "PASS", "access": "anonymous",
         "checked_at": "2026-10-13T00:00:00Z", "repository": "https://github.com/dennisyu/local-service-spotlight-skills",
         "bundle": "lss-everything", "manifest_commit": revision, "linked_manifest_verified": True,
         "guide_capture": put('install-guide.txt', 'SYNTHETIC guide links to ' + manifest_url),
         "manifest_capture": put('marketplace.json', market), "manifest_url": manifest_url,
         "resolved_manifest_url": manifest_url.replace('/main/', '/' + revision + '/'),
         "manifest_version": market['metadata']['version'],
         "master_skill_count": len(next(p for p in market['plugins'] if p['name']=='lss-everything')['skills'])})
    roles = ("start_here", "subject_facts", "source_map", "instructions", "first_task", "output_example",
             "permission_gates", "receipt_template")
    files = {r + ".md": ("SYNTHETIC-SUBJECT test-only content: " + r).encode() for r in roles}
    kit_manifest = {"subject_id": m["subject_id"], "version": "synthetic-1", "source_revision": revision,
                    "skills": [{"id": "evidence-verification", "canonical_route": "evidence-verification",
                                "instruction_path": "instructions.md", "output_example_path": "output_example.md",
                                "input": "E1", "output": "proof card",
                                "cadence": "first task", "human_gate": "no publish", "handoff": "research to content",
                                "receipt": "dated source/output"}], "files": [
                        {"path": r + ".md", "role": r, "sha256": hashlib.sha256(files[r + ".md"]).hexdigest()} for r in roles]}
    delivered_manifest = {"subject_id": m["subject_id"], "version": "synthetic-1", "source_revision": revision,
                          "files": kit_manifest['files']}
    files['manifest.json'] = json.dumps(delivered_manifest).encode()
    kit_manifest['delivered_manifest'] = {'path':'manifest.json','sha256':hashlib.sha256(files['manifest.json']).hexdigest(),
                                          'version_path':['version']}
    def write_package(contents=kit_manifest, data=files):
        package = io.BytesIO()
        with zipfile.ZipFile(package, "w") as z:
            for path, value in data.items(): z.writestr(path, value)
        return put("synthetic-kit.zip", package.getvalue())
    package = write_package()
    review["kit_sha256"] = package["sha256"]
    m["kit"] = {"required": True, "basis": "Synthetic engagement promise", "url": kit_url, "package": package,
                "contents_manifest": put("kit-projection.json", kit_manifest),
                "promised_skills": ["evidence-verification"], "qr": qr(kit_url, "kit"),
                "access_check": put("kit-access.json", {"status": "PASS", "access": "anonymous", "subject_id": m["subject_id"],
                    "final_url": kit_url, "downloaded_sha256": package["sha256"], "contents_opened": True,
                    "checked_at": "2026-10-13T00:00:00Z"})}
    review['input_binding_sha256'] = input_binding(m)
    m["editorial_review"] = put("review.json", review)
    return m, put, review, kit_manifest, files, write_package
