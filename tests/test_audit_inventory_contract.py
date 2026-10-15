"""Synthetic negative controls for count-unit and rendered-artifact release gates."""
import copy
import importlib.util
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('contract', Path(__file__).parents[1] / 'scripts/audit_inventory_contract.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

def fixture():
    return {'method_version':'AUDIT-METHOD-2026.10.02','scope':{'snapshot':'2026-10-06T00:00:00Z','enumerated_sources':['synthetic channel'], 'completeness':'bounded_public_census'},'counts':{'all':{'unit':'public_asset','value':7,'source':'fixture'},'regular':{'unit':'public_asset','value':5,'source':'fixture'},'shorts':{'unit':'public_asset','value':2,'source':'fixture'},'raw':{'unit':'raw_session','value':'UNKNOWN','source':'not supplied'}},'sums':[{'total':'all','members':['regular','shorts'],'disjoint_verified':True}],'reuse_yield':'UNKNOWN','confirmed_derivatives':[{'source_id':'parent-1','child_id':'clip-1','proof_kind':'publisher_parent_link','evidence':'synthetic explicit parent link'}],'pdf_acceptance':{'physical_page_count':2,'inspected_pages':[1,2],'artifact_sha256':'a'*64,'accepted_sha256':'a'*64,'geometry_status':'PASS','visual_status':'PASS','reviewer':'fixture reviewer','reviewed_utc':'2026-10-06T01:00:00Z','minimum_body_points':11,'minimum_note_points':9}}

class InventoryContractTests(unittest.TestCase):
    def reject(self, mutate):
        doc=copy.deepcopy(fixture());mutate(doc)
        with self.assertRaises((c.ContractError,KeyError,TypeError)):
            c.validate(doc)
    def test_clean_synthetic_fixture(self):
        self.assertEqual(c.validate(fixture())['status'],'PASS')
    def test_wrong_arithmetic(self):
        self.reject(lambda d:d['counts']['all'].update(value=8))
    def test_cross_unit_sum(self):
        self.reject(lambda d:d['counts']['shorts'].update(unit='published_release'))
    def test_unknown_not_zero(self):
        self.reject(lambda d:d['counts']['shorts'].update(value='UNKNOWN'))
    def test_unverified_overlap(self):
        self.reject(lambda d:d['sums'][0].update(disjoint_verified=False))
    def test_unknown_raw_yield(self):
        self.reject(lambda d:d.update(reuse_yield=3.5))
    def test_title_is_not_parent_proof(self):
        self.reject(lambda d:d['confirmed_derivatives'][0].update(proof_kind='same_guest_title'))
    def test_missing_source_boundary(self):
        self.reject(lambda d:d['scope'].update(completeness='all lifetime appearances'))
    def test_missing_physical_page(self):
        self.reject(lambda d:d['pdf_acceptance'].update(inspected_pages=[1]))
    def test_stale_pdf_revision(self):
        self.reject(lambda d:d['pdf_acceptance'].update(artifact_sha256='b'*64))
    def test_geometry_is_not_visual_review(self):
        self.reject(lambda d:d['pdf_acceptance'].update(visual_status='PENDING'))
    def test_tiny_note(self):
        self.reject(lambda d:d['pdf_acceptance'].update(minimum_note_points=8))
    def test_unknown_rubric_version(self):
        self.reject(lambda d:d.update(method_version='unverified'))
    def test_boolean_is_not_count(self):
        self.reject(lambda d:d['counts']['all'].update(value=True))

if __name__ == '__main__':
    unittest.main()
