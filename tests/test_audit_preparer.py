"""Guarded existing-block updates must preserve all unrelated native bytes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'docs/audit-quality/prepare_article_update.py'
OLD = '<!-- wp:html -->\n<section id="universal-audit-quality-gate">old native block</section>\n<!-- /wp:html -->'
NEW = OLD.replace('old native block','reviewed candidate')


class AuditPreparerTests(unittest.TestCase):
    def run_case(self, old=OLD, public_title='Original title'):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            raw='<!-- wp:paragraph -->Keep exact original.<!-- /wp:paragraph -->\n'+OLD+'\n<!-- wp:html -->Other form source<!-- /wp:html -->'
            native={'id':112500,'slug':'how-we-audit','status':'publish','author':30,'modified_gmt':'2026-10-15T00:00:00','link':'https://blitzmetrics.com/how-we-audit/','title':'Original title','content':{'raw':raw,'rendered':'Current rendered snapshot'}}
            public=dict(native,title=public_title,content={'rendered':'Current rendered snapshot'})
            for name,value in [('native.json',native),('public.json',public)]: (root/name).write_text(json.dumps(value))
            (root/'old.html').write_text(old);(root/'new.html').write_text(NEW)
            p=subprocess.run([sys.executable,str(SCRIPT),'--native-preimage',str(root/'native.json'),'--public-baseline',str(root/'public.json'),'--addition',str(root/'new.html'),'--replace-existing-block',str(root/'old.html'),'--output-dir',str(root/'out')],capture_output=True,text=True)
            payload=json.loads((root/'out/content-only-payload.json').read_text()) if p.returncode==0 else None
            return p,payload,raw

    def test_replace_only_exact_existing_block(self):
        p,payload,raw=self.run_case()
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(set(payload),{'content'})
        self.assertEqual(payload['content'],raw.replace(OLD,NEW,1))

    def test_native_block_drift_holds(self):
        p,payload,_=self.run_case(old=OLD.replace('old native','wrong native'))
        self.assertNotEqual(p.returncode,0)
        self.assertIsNone(payload)

    def test_metadata_drift_holds(self):
        p,payload,_=self.run_case(public_title='Concurrent title edit')
        self.assertNotEqual(p.returncode,0)
        self.assertIsNone(payload)


if __name__=='__main__': unittest.main()
