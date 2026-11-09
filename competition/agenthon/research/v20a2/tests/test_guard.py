import hashlib,json,tempfile,unittest
from pathlib import Path
from baseline_agent.indexer import IndexedDoc
from baseline_agent.entity_filter import load_manifest_labels,IdentityManifestError
class GuardTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.base=Path(self.t.name);(self.base/'corpus').mkdir()
 def check(self,modify=lambda x:x,doc_override=None,ref='manifest.json'):
  data={'doc_id':'A','doc_date':'2024-01-01','text':'test'}
  if doc_override:data.update(doc_override)
  raw=json.dumps(data).encode()
  (self.base/'corpus/A.json').write_bytes(raw)
  row={'role':'corpus','path':'corpus/A.json','entity_ids':['A'],'sha256':hashlib.sha256(raw).hexdigest()}
  (self.base/ref).write_text(json.dumps({'files':[modify(row)]}))
  return load_manifest_labels(self.base/'corpus',[IndexedDoc('A','test',data['doc_date'])],manifest_ref=ref)
 def test_normal_paths(self):
  self.assertIn('A',self.check())
  self.assertIn('A',self.check(ref='corpus/manifest.json'))
 def test_explicit_shared_false_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(lambda r:dict(r,shared=False))
 def test_dual_label_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(lambda r:dict(r,shared=True))
 def test_duplicate_entity_label_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(lambda r:dict(r,entity_ids=['A','A']))
 def test_unlabelled_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(lambda r:{k:v for k,v in r.items() if k!='entity_ids'})
 def test_bad_checksum_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(lambda r:dict(r,sha256='a'*64))
 def test_wrong_docid_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(doc_override={'doc_id':'B'})
 def test_bad_date_denied(self):
  with self.assertRaises(IdentityManifestError):self.check(doc_override={'doc_date':'2024-02-31'})
if __name__=='__main__':unittest.main()
