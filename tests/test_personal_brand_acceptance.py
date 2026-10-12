import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from personal_brand_acceptance import validate, source_key, input_binding
from personal_brand_fixture import make_fixture


class PersonalBrandAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.m, self.put, self.review, self.kit_manifest, self.files, self.write_package = make_fixture(self.base, ROOT)

    def check(self, code=None):
        result = validate(self.m, self.base, ROOT)
        if code:
            self.assertEqual("HOLD", result["acceptance_status"])
            self.assertTrue(any(e.startswith(code + ":") for e in result["errors"]), result["errors"])
        return result

    def save_review(self):
        self.m["editorial_review"] = self.put("review.json", self.review)

    def rebind_review(self):
        self.review['input_binding_sha256'] = input_binding(self.m); self.save_review()

    def test_positive_control_never_certifies_acceptance(self):
        r = self.check(); self.assertEqual([], r["errors"])
        self.assertEqual("REVIEW_REQUIRED", r["acceptance_status"])
        self.assertEqual(10, r["distinct_supporting_urls"])

    def test_screenshot_only_cover(self):
        self.m["visuals"][0]["kind"] = "screenshot"; self.check("COVER_PHOTO")

    def test_wrong_person_portrait(self):
        self.m["visuals"][0]["identity_status"] = "AMBIGUOUS"; self.check("PHOTO_IDENTITY")

    def test_unknown_photo_rights(self):
        self.m["visuals"][0]["reuse_status"] = "UNKNOWN"; self.check("VISUAL_RIGHTS")

    def test_decorative_qr_is_not_page_evidence(self):
        self.m["visuals"][0]["kind"] = "qr"; self.check("MEANINGFUL_VISUAL")

    def test_repeated_memo_fails_actual_visual_brief_review(self):
        self.review["gates"]["visual_brief"] = {"status": "FAIL", "basis": "All pages repeat two text columns"}
        self.save_review(); self.check("EDITORIAL_GATE")

    def test_unreadable_source_labels(self):
        self.m["pages"][3]["label_min_pt"] = 6; self.check("READABILITY")

    def test_failed_normal_size_page_review(self):
        self.review["pages"]["4"]["status"] = "FAIL"; self.save_review(); self.check("PAGE_REVIEW")

    def test_50_citations_are_not_50_distinct_sources(self):
        self.m["source_counts"]["reported"] = 50; self.check("SOURCE_COUNT")

    def test_urls_are_not_an_independence_count(self):
        self.m["source_counts"]["unit"] = "independent_sources"; self.check("SOURCE_UNIT")

    def test_declared_target_not_met(self):
        self.m["source_counts"]["engagement_target"] = 26; self.check("SOURCE_COVERAGE")

    def test_uncited_padding_does_not_increase_count(self):
        s = copy.deepcopy(self.m["sources"][0]); s["id"] = "unused"; s["final_url"] = "https://example.org/padding"
        self.m["sources"].append(s); self.m["source_counts"]["reported"] = 11; self.check("SOURCE_COUNT")

    def test_fragments_tracking_and_meaningful_query(self):
        self.assertEqual(source_key("https://example.org/a?utm_source=x#b"), "https://example.org/a")
        self.assertNotEqual(source_key("https://example.org/a?id=1"), source_key("https://example.org/a?id=2"))

    def test_duplicate_final_urls(self):
        self.m["sources"][1]["final_url"] = self.m["sources"][0]["final_url"] + "?utm_source=x#fact"
        self.check("SOURCE_COUNT")

    def test_evidenced_mirror_does_not_pad_url_count(self):
        self.m['sources'][1].update(duplicate_of='S1',dedupe_basis='Synthetic mirror match',origin_id='moment-1')
        self.m['source_counts'].update(reported=9,underlying_records=9)
        self.rebind_review();self.assertEqual([],self.check()['errors'])

    def test_cyclic_mirror_mapping_holds(self):
        self.m['sources'][0].update(duplicate_of='S2',dedupe_basis='Synthetic match')
        self.m['sources'][1].update(duplicate_of='S1',dedupe_basis='Synthetic match')
        self.check('SOURCE_DEDUPE')

    def test_photo_original_source_must_resolve(self):
        self.m['visuals'][0]['original_source']='missing-source';self.check('PHOTO_PROVENANCE')

    def test_changed_source_capture(self):
        (self.base / "source-1.txt").write_text("Changed source"); self.check("HASH")

    def test_extract_not_in_source(self):
        self.m["evidence"][0]["extract"] = "Invented fact"; self.check("TRACE")

    def test_claim_not_in_final_pdf(self):
        self.m["claims"][0]["text"] = "Invented final claim"; self.check("PDF_CLAIM")

    def test_unknown_not_zero(self):
        self.m["evidence"][0].update(finding_type="UNKNOWN", value=0, owner="research", next_evidence="owner export")
        self.check("UNKNOWN")

    def test_missing_page_review(self):
        self.review["pages"].pop("20"); self.save_review(); self.check("PAGE_REVIEW")

    def test_same_context_not_fresh_review(self):
        self.review["reviewer_context"] = self.m["author_context"]; self.save_review(); self.check("FRESH_REVIEW")

    def test_unknown_author_cannot_establish_fresh_review(self):
        self.m['author_context']='UNKNOWN';self.rebind_review();self.check('FRESH_REVIEW')

    def test_unperformed_required_review(self):
        self.review["gates"]["strategy"]["status"] = "UNTESTED"; self.save_review(); self.check("EDITORIAL_GATE")

    def test_stale_pdf_review(self):
        self.review["pdf_sha256"] = "old"; self.save_review(); self.check("REVIEW_DRIFT")

    def test_stale_render_hash(self):
        self.review["pages"]["1"]["render_sha256"] = "old"; self.save_review(); self.check("PAGE_REVIEW")

    def test_guide_hash_drift(self):
        self.m["guide_hashes"]["SKILL.md"] = "old"; self.check("GUIDE_DRIFT")

    def test_generic_install_destination_cannot_be_bespoke_kit(self):
        self.m["kit"]["url"] = "https://localservicespotlight.com/install/"; self.check("BESPOKE_KIT")

    def test_missing_promised_starter_role(self):
        self.kit_manifest["files"] = [f for f in self.kit_manifest["files"] if f["role"] != "start_here"]
        self.m["kit"]["package"] = self.write_package()
        self.m["kit"]["contents_manifest"] = self.put('kit-projection.json',self.kit_manifest)
        self.check("KIT_CONTENTS")

    def test_missing_promised_skill(self):
        self.m["kit"]["promised_skills"].append("content-factory"); self.check("KIT_SKILL")

    def test_stale_kit_review(self):
        self.review["kit_sha256"] = "old"; self.save_review(); self.check("REVIEW_DRIFT")

    def test_owner_access_not_recipient_access(self):
        data = json.loads((self.base / "kit-access.json").read_text()); data["access"] = "owner_only"
        self.m["kit"]["access_check"] = self.put("kit-access.json", data); self.check("KIT_ACCESS")

    def test_wrong_download(self):
        data = json.loads((self.base / "kit-access.json").read_text()); data["downloaded_sha256"] = "old"
        self.m["kit"]["access_check"] = self.put("kit-access.json", data); self.check("KIT_ACCESS")

    def test_qr_decoded_from_old_pdf(self):
        data = json.loads((self.base / "kit-decode.json").read_text()); data["pdf_sha256"] = "old"
        self.m["kit"]["qr"]["decode_receipt"] = self.put("kit-decode.json", data); self.check("QR_DRIFT")

    def test_valid_zip_is_not_installation(self):
        ref = self.put("installed.json", {"state": "INSTALLED", "runtime": "synthetic-account", "source_revision": "a" * 40,
             "kind": "prepared_zip", "event_id": "synthetic", "checked_at": "2026-10-13T00:00:00Z"})
        self.m["lifecycle_claims"] = [{"state": "INSTALLED", "runtime": "synthetic-account", "source_revision": "a" * 40, "receipt": ref}]
        self.check("LIFECYCLE")

    def test_no_kit_promise_explicit_na(self):
        self.m["kit"] = {"required": False, "basis": "Synthetic brief explicitly excludes kit"}
        self.m['brief'] = self.put('brief.json',{'subject_id':self.m['subject_id'],'kit_required':False,'source_target':None})
        self.rebind_review(); self.assertEqual([],self.check()['errors'])

    def test_cannot_waive_promised_kit(self):
        self.m['kit'] = {'required':False,'basis':'Pretend kit was never promised'}; self.check('KIT_SCOPE')

    def test_updated_source_hash_invalidates_prior_review(self):
        self.m['sources'][0]['capture'] = self.put('source-1.txt','Synthetic source 1 states a test observation. Updated context.')
        self.check('REVIEW_INPUT_DRIFT')

    def test_updated_photo_hash_invalidates_prior_review(self):
        self.m['visuals'][0]['asset'] = self.put('synthetic-asset.txt','Changed photo stand-in')
        self.check('REVIEW_INPUT_DRIFT')

    def test_updated_permission_invalidates_prior_review(self):
        self.m['visuals'][0]['reuse_receipt'] = self.put('synthetic-permission.txt','Changed reuse terms')
        self.check('REVIEW_INPUT_DRIFT')

    def test_generic_file_cannot_fill_every_kit_role(self):
        for row in self.kit_manifest['files']:
            row['path']='instructions.md';row['sha256']=self.kit_manifest['files'][3]['sha256']
        self.m['kit']['contents_manifest']=self.put('kit-projection.json',self.kit_manifest)
        self.check('KIT_CONTENTS')

    def test_promised_skill_needs_instruction_file(self):
        self.kit_manifest['skills'][0]['instruction_path']='missing.md'
        self.m['kit']['contents_manifest']=self.put('kit-projection.json',self.kit_manifest)
        self.check('KIT_SKILL')

    def test_promised_skill_needs_worked_output_file(self):
        self.kit_manifest['skills'][0]['output_example_path']='missing-output.md'
        self.m['kit']['contents_manifest']=self.put('kit-projection.json',self.kit_manifest);self.check('KIT_SKILL')

    def test_delivered_manifest_version_must_match(self):
        self.kit_manifest['version']='synthetic-wrong-version'
        self.m['kit']['contents_manifest']=self.put('kit-projection.json',self.kit_manifest);self.check('KIT_MANIFEST')

    def test_missing_delivered_manifest_cli_holds(self):
        import subprocess
        self.files.pop('manifest.json');self.m['kit']['package']=self.write_package()
        path=self.base/'acceptance.json';path.write_text(json.dumps(self.m))
        r=subprocess.run([sys.executable,str(ROOT/'scripts/personal_brand_acceptance.py'),str(path)],capture_output=True,text=True)
        self.assertEqual(2,r.returncode);self.assertEqual('HOLD',json.loads(r.stdout)['acceptance_status'])

    def test_install_boolean_without_manifest_is_not_proof(self):
        data=json.loads((self.base/'install-check.json').read_text());data.pop('manifest_capture')
        self.m['install_check']=self.put('install-check.json',data);self.check('INSTALL_MANIFEST')

    def test_authorized_private_locator_count_stays_separate(self):
        self.m['sources'][0].update(url='private-record:test-1',final_url='private-record:test-1',data_classification='PRIVATE-AUTHORIZED')
        self.m['source_counts'].update(reported=9,private_record_locators=1)
        self.rebind_review();r=self.check();self.assertEqual([],r['errors']);self.assertEqual(1,r['private_record_locators'])

    def test_malformed_pdf_cli_returns_structured_hold(self):
        import subprocess
        self.m['pdf']=self.put('synthetic.pdf','not a PDF');path=self.base/'acceptance.json'
        path.write_text(json.dumps(self.m))
        r=subprocess.run([sys.executable,str(ROOT/'scripts/personal_brand_acceptance.py'),str(path)],capture_output=True,text=True)
        self.assertEqual(2,r.returncode);self.assertEqual('HOLD',json.loads(r.stdout)['acceptance_status'])
        self.assertNotIn('Traceback',r.stderr)


if __name__ == "__main__": unittest.main()
