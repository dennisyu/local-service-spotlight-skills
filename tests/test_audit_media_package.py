"""Declared synthetic adversarial cases; never production adoption proof."""
import copy
import json
import unittest
from tests.test_audit_quality import BASE, checker

class MediaPackageTests(unittest.TestCase):
    def hold(self, r):
        result = checker.assess(r)
        self.assertEqual('HOLD', result['decision'], result)

    def test_each_required_component_blocks_high_score(self):
        for kind in ['AUTHENTIC_PHOTO','REAL_VIDEO','ORIGINAL_THUMBNAIL']:
            r=copy.deepcopy(BASE)
            r['media_package'][0]['assets']=[a for a in r['media_package'][0]['assets'] if a['kind']!=kind]
            self.hold(r)
        for field in ['greatest_hits','assets']:
            r=copy.deepcopy(BASE);r['media_package'][0][field]=[];self.hold(r)
        r=copy.deepcopy(BASE);r['actions']=[];self.hold(r)
        r=copy.deepcopy(BASE);r['media_package']=[];self.hold(r)

    def test_no_proof_or_scope_waiver(self):
        for kind in ['DIAGRAM','STOCK','GENERATED','AUDIO','N/A']:
            r=copy.deepcopy(BASE);r['media_package'][0]['assets'][0]['kind']=kind;self.hold(r)
        r=copy.deepcopy(BASE);r['media_package'][0]['assets'][2]['video_id']='unrelated-video';self.hold(r)

    def test_exact_review_binding_and_access(self):
        for field,value in [('artifact_sha256','b'*64),('review_evidence_id','E-identity')]:
            r=copy.deepcopy(BASE);r['media_package'][0][field]=value;self.hold(r)
        for field,value in [('source_evidence_id','missing'),('identity_and_relevance','unrelated identity'),('source_date','2020-01-01'),('page',99),('review_evidence_id','E-identity'),('content_review_method','METADATA_ONLY')]:
            r=copy.deepcopy(BASE);r['media_package'][0]['assets'][1][field]=value;self.hold(r)
        for field,value in [('reviewer_id',BASE['author_id']),('artifact_sha256','b'*64),('inspection','METADATA_ONLY'),('covered_pages',[])]:
            r=copy.deepcopy(BASE);next(e for e in r['evidence'] if e['id']=='MEDIA-review-video')[field]=value;self.hold(r)
        r=copy.deepcopy(BASE);r['links'][1]['recipient_access']['status']='UNKNOWN';self.hold(r)
        r=copy.deepcopy(BASE);next(e for e in r['evidence'] if e['id']=='MEDIA-source-video')['retrieved_at']='2020-01-01T00:00:00Z';self.hold(r)

    def test_greatest_hit_must_drive_related_useful_action(self):
        for field,value in [('action_id','missing'),('asset_id','thumbnail'),('source_evidence_id','unrelated'),('why_relevant',''),('next_use','')]:
            r=copy.deepcopy(BASE);r['media_package'][0]['greatest_hits'][0][field]=value;self.hold(r)
        for field in ['first_step','owner_function','destination','done_when','due_or_timeframe','authority']:
            r=copy.deepcopy(BASE);r['actions'][0][field]='';self.hold(r)
        r=copy.deepcopy(BASE);r['actions'][0]['evidence_ids'].remove('MEDIA-source-video');self.hold(r)

    def test_print_route_and_description_only_curation(self):
        from tests.test_audit_quality import refresh_synthetic_media_reviews
        r=copy.deepcopy(BASE);r['media_package'][0]['assets'][1]['navigation_test']='CLICK_TESTED'
        refresh_synthetic_media_reviews(r);self.hold(r)
        r=copy.deepcopy(BASE);a=r['media_package'][0]['assets'][1]
        a.update(claim_basis='PUBLISHER_DESCRIPTION_ATTRIBUTED',content_review_method='VIDEO_IDENTITY_AND_POSTER',content_review_notes='Publisher describes the topic; no derived lesson or full-watch claim.')
        r['links'][1]['media_inspected']['method']='VIDEO_IDENTITY_AND_POSTER'
        refresh_synthetic_media_reviews(r)
        self.assertEqual(checker.assess(r)['decision'],'RELEASE_READY')
        a['claim_basis']='CONTENT_DERIVED';refresh_synthetic_media_reviews(r);self.hold(r)

    def test_a_family_claim_cannot_bypass_media_gate(self):
        for grade in ['A-', 'A', 'A+']:
            r=copy.deepcopy(BASE);r['media_package']=[];r['report_grade']=grade
            self.hold(r)

    def test_legacy_cannot_accept_production(self):
        r=copy.deepcopy(BASE);r['schema_version']='UAQG-TIER-RECEIPT-1.0.0';r['synthetic']=False;self.hold(r)
        r=json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'docs/audit-quality/historical-run-template.json').read_text());self.hold(r)

if __name__=='__main__':unittest.main()
