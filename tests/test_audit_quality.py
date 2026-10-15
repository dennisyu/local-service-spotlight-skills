"""Synthetic regression controls, never actual audit acceptance receipts."""
import copy
import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_quality', ROOT / 'docs/audit-quality/check_quality.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
BASE = json.loads((ROOT / 'tests/fixtures/audit-tier-base.json').read_text())


def bulk_fixture():
    r = copy.deepcopy(BASE)
    r['product_profile'].update(id='bulk-screening', contracted_pages=None, blueprint_ref=None)
    r['artifacts'][0].update(format='JSON', page_count=None, visual_manifest=[])
    r.update(claims=[], actions=[], claim_scope='NO_FINDINGS_SCREENING', no_findings_reason='Synthetic leads; no accepted findings.')
    r['quality'].update(ratings=[None]*6, total=None, calibration={'status':'NOT_RUN','receipt_id':None,'anchor_ids':[]})
    r['independent_review'].update(status='UNKNOWN', reviewer_id=None, fresh_context=False, artifacts=[])
    ids = ['a','b','c','d','e']
    selected = sorted(ids, key=lambda k: hashlib.sha256(('seed1\0'+k).encode()).hexdigest())[:1]
    records = []
    for i in ids:
        reviewed = i in selected or i == 'a'
        review = {'reviewer_id':'synthetic-reviewer','fresh_context':True,'artifact_sha256':'a'*64,'status':'PASS','evidence_id':'E-reproducibility'} if reviewed else None
        records.append({'id':i,'artifact_sha256':'a'*64,'identity_status':'RESOLVED','mechanical_status':'PASS','mechanical_evidence_id':'E-provenance','flagged':i=='a','label':'REVIEWED_SCREENING' if reviewed else 'SCREENING','review':review})
    r['batch'] = {'population_revision':'synthetic-population1','population_ids':ids,'records':records,'random_sample':{'method':'SHA256_SEEDED_ORDER','seed':'seed1','sample_size':1,'selected_ids':selected,'reviewed_ids':selected},'review_claim':'PIPELINE_SAMPLE_ONLY'}
    return r


def patch_path(r, path, value=None, remove=False):
    parts = path.split('/')
    node = r
    for key in parts[:-1]: node = node[int(key)] if isinstance(node,list) else node[key]
    key = int(parts[-1]) if isinstance(node,list) else parts[-1]
    if remove: del node[key]
    else: node[key] = value


class AuditQualityTests(unittest.TestCase):
    def hold(self, r, reason=None):
        result = checker.assess(r)
        self.assertEqual(result['decision'], 'HOLD', result)
        if reason: self.assertTrue(any(reason in x for x in result['reasons']), result)

    def test_original_22_cases(self):
        with redirect_stdout(io.StringIO()) as out: checker.self_test()
        self.assertEqual(json.loads(out.getvalue())['synthetic_cases_passed'],22)

    def test_free_positive(self):
        result = checker.assess(copy.deepcopy(BASE))
        self.assertEqual(result['decision'],'RELEASE_READY',result)
        self.assertEqual(result['total'],'90.00')
        self.assertTrue(result['synthetic'])

    def test_paid_twenty_page_contract(self):
        r = copy.deepcopy(BASE)
        r['product_profile'].update(id='paid-full',contracted_pages=20,blueprint_ref='20-page-pdf-blueprint.md')
        a = r['artifacts'][0]; a['page_count']=20
        a['visual_manifest']=[dict(a['visual_manifest'][0],page=i) for i in range(1,21)]
        for e in r['evidence']:
            if e['kind']=='RENDER_REVIEW': e['covered_pages']=list(range(1,21))
        self.assertEqual(checker.assess(r)['decision'],'RELEASE_READY')
        a['page_count']=19; self.hold(r,'contracted page')

    def test_bulk_positive_stays_screening(self):
        r=bulk_fixture(); result=checker.assess(r)
        self.assertEqual(result['decision'],'SCREENING',result)
        self.assertIsNone(result['total'])
        self.assertTrue(any(x['label']=='SCREENING' for x in r['batch']['records']))

    def test_missing_fields_hold(self):
        for path in ['claims','author_id','evidence/0/locator','claims/0/requires_content_inspection','actions/0/done_when','checks/0','independent_review/candidate_sha256','identity']:
            with self.subTest(path=path):
                r=copy.deepcopy(BASE); patch_path(r,path,remove=True); self.hold(r)

    def test_fail_closed_negative_mutations(self):
        cases=[
            ('claims',[]), ('claims/0/type','BANANA'),
            ('claims/0/evidence_state','NOT_CHECKED'), ('evidence/0/inspection','METADATA_ONLY'),
            ('checks/0/status','OK'), ('checks/0/required',False), ('checks/4/evidence_ids',['S1']),
            ('independent_review/artifacts/0/sha256','b'*64),
            ('independent_review/candidate_sha256','b'*64),
            ('independent_review/artifacts/0/coverage','BATCH_SAMPLE'),
            ('independent_review/reviewer_id',BASE['author_id']),
            ('identity/status','AMBIGUOUS'), ('quality/calibration/status','NOT_RUN'),
            ('quality/calibration/receipt_id',None), ('quality/total',99),
            ('quality/weights',[25,20,20,15,10,10]), ('quality/ratings/2',None),
            ('quality/ratings/2',True), ('quality/ratings/2',3.5),
            ('allowance/state','EXHAUSTED'), ('routing/0/source_access','MISSING'),
            ('routing/0/capability_evidence_id','S1'), ('schema_version','BANANA'),
            ('timing/agent_runtime/value',180), ('claims/0/evidence_ids',[]),
        ]
        for path,value in cases:
            with self.subTest(path=path,value=value):
                r=copy.deepcopy(BASE); patch_path(r,path,value); self.hold(r)

    def test_metadata_cannot_bypass_false_media_flag(self):
        r=copy.deepcopy(BASE); r['claims'][0]['requires_content_inspection']=False
        r['evidence'][0]['inspection']='METADATA_ONLY'; self.hold(r,'metadata/uninspected')

    def test_visual_page_coverage(self):
        r=copy.deepcopy(BASE); r['artifacts'][0]['visual_manifest'].pop(); self.hold(r,'every human-facing page')
        r=copy.deepcopy(BASE)
        next(e for e in r['evidence'] if e['id']=='E-usability')['covered_pages']=[1]
        self.hold(r,'visual render review')

    def test_defect_types_and_closure(self):
        d={'id':'D1','severity':'CRITICAL','closed':False,'closure_review_receipt':None,'disposition':dict.fromkeys(['accepted_by','risk_reason','owner','deadline','completion_test'])}
        r=copy.deepcopy(BASE); r['defects']=[d]; self.hold(r,'unknown enum')
        d.update(severity='S1',closed=True,closure_review_receipt='E-identity'); self.hold(r,'closure review')

    def test_all_final_artifacts_need_review(self):
        r=copy.deepcopy(BASE);r['artifacts'].append(dict(r['artifacts'][0],id='companion'))
        r['product_profile']['required_outputs'].append('companion');self.hold(r,'every required final artifact')

    def test_link_receipt_separates_media_and_access(self):
        r=copy.deepcopy(BASE)
        s={'status':'PASS','method':'TRANSCRIPT_AT_CITED_LOCATION','evidence_id':'S1','observed_at':'2026-10-16T00:00:00Z','reason':None}
        r['links']=[{'id':'L1','url':'https://example.invalid/synthetic','material':True,'is_media':True,**{k:copy.deepcopy(s) for k in ['reachable','expected_content','recipient_access','media_inspected']}}]
        self.assertEqual(checker.assess(r)['decision'],'RELEASE_READY')
        r['links'][0]['media_inspected']['method']='OEMBED'; self.hold(r,'metadata is not media')
        r['links'][0]['media_inspected']=copy.deepcopy(s);r['links'][0]['recipient_access']['status']='BLOCKED';self.hold(r,'recipient blocked')

    def test_batch_population_and_sampling(self):
        for path,value in [('batch/review_claim','ALL_RECORDS_REVIEWED'),('batch/records/0/mechanical_status','UNKNOWN'),('batch/records/0/review',None),('batch/random_sample/selected_ids',['absent']),('batch/random_sample/reviewed_ids',[])]:
            with self.subTest(path=path):
                r=bulk_fixture();patch_path(r,path,value);self.hold(r)
        r=bulk_fixture();next(x for x in r['batch']['records'] if not x['review'])['label']='REVIEWED_SCREENING';self.hold(r,'mislabeled')
        r=bulk_fixture();next(x for x in r['batch']['records'] if not x['flagged'])['identity_status']='AMBIGUOUS';self.hold(r,'must be flagged')
        r=bulk_fixture();r['quality'].update(ratings=[4,3,4,4,3,3],total=90);self.hold(r,'screening cannot claim')
        r=bulk_fixture();r['batch']['records'].pop();self.hold(r,'frozen population manifest')

    def test_no_findings_profile_is_screening_only(self):
        r=copy.deepcopy(BASE);r.update(claim_scope='NO_FINDINGS_SCREENING',claims=[],actions=[],no_findings_reason='No findings');self.hold(r,'only for explicit no-findings screening')

    def test_incomplete_template_holds(self):
        r=json.loads((ROOT/'docs/audit-quality/tier-run-template.json').read_text())
        self.hold(r)

    def test_corrected_reference_packet_additional_attacks(self):
        for path,value in [('evidence/0/source_date','2026-99-99'),('evidence/0/inspection','NOT_CHECKED'),('evidence/0/retrieved_at','not-a-date'),('quality/calibration/status',True),('independent_review/receipt_id','E-identity')]:
            with self.subTest(path=path):
                r=copy.deepcopy(BASE);patch_path(r,path,value);self.hold(r)
        r=copy.deepcopy(BASE)
        r['claims'][0].update(type='UNKNOWN',evidence_state='UNKNOWN',limitation='Not established',evidence_ids=[],next_verification=None)
        self.hold(r,'next verification')
        for path in ['evidence/0/source_date','evidence/0/scope']:
            r=copy.deepcopy(BASE);patch_path(r,path,remove=True);self.hold(r)
        r=copy.deepcopy(BASE)
        r['defects']=[{'id':'D1','severity':'S2','closed':True,'closure_review_receipt':None,'disposition':dict.fromkeys(['accepted_by','risk_reason','owner','deadline','completion_test'])}]
        self.hold(r,'closure review')
        r=copy.deepcopy(BASE);r['release'].update(attempted=True,candidate_sha256='a'*64,readback=[{'name':n,'status':'PASS','evidence':'S1'} for n in ['recipient_access','final_bytes']])
        self.hold(r,'readback lacks typed')


if __name__=='__main__': unittest.main()
