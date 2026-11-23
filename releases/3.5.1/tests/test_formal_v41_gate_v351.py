import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from formal_v41_gate_v351 import validate_formal_v41
class FormalV41WiringTests(unittest.TestCase):
 def setUp(self):
  self.batch={"scripts":[{"script_id":"A1"}]};self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"batch.json"
  self.path.write_text(json.dumps(self.batch,ensure_ascii=False),encoding="utf-8")
  self.review={"batch_sha256":hashlib.sha256(self.path.read_bytes()).hexdigest()};self.called=[]
  def validator(batch,review):
   self.called.append(review.get("batch_sha256_payload"))
   return {"status":"VALIDATION_PENDING","items":[{"script_id":"A1","validation_pending":["human_voice_test","blind_test"]}],"errors":[]}
  self.validator=validator
 def tearDown(self):self.tmp.cleanup()
 def test_formal_validator_called_and_payload_bound(self):
  errors,result=validate_formal_v41(self.batch,self.review,self.path,self.validator)
  self.assertEqual(errors,[]);self.assertEqual(result["status"],"VALIDATION_PENDING");self.assertEqual(len(self.called),1);self.assertTrue(self.called[0])
 def test_missing_independent_reviewer_blocks(self):
  def validator(batch,review):return {"status":"VALIDATION_PENDING","items":[{"script_id":"A1","validation_pending":["independent_review"]}],"errors":[]}
  errors,_=validate_formal_v41(self.batch,self.review,self.path,validator)
  self.assertTrue(any("AI_VIDEO_INDEPENDENT_REVIEW_MISSING" in x for x in errors))
 def test_incomplete_routing_blocks(self):
  def validator(batch,review):return {"status":"VALIDATION_PENDING","items":[{"script_id":"A1","validation_pending":["review_role:deep_review"]}],"errors":[]}
  errors,_=validate_formal_v41(self.batch,self.review,self.path,validator)
  self.assertTrue(any("AI_VIDEO_REVIEW_ROUTING_INCOMPLETE" in x for x in errors))
 def test_full_flag_requires_pass(self):
  errors,_=validate_formal_v41(self.batch,self.review,self.path,self.validator,True)
  self.assertTrue(any("AI_VIDEO_FULL_VALIDATION_REQUIRED:VALIDATION_PENDING" in x for x in errors))
 def test_wrong_hash_blocks_before_review(self):
  self.review["batch_sha256"]="0"*64
  errors,_=validate_formal_v41(self.batch,self.review,self.path,self.validator)
  self.assertEqual(errors,["AI_VIDEO_V4_1_REVIEW_NOT_BOUND_TO_BATCH_BYTES"]);self.assertEqual(self.called,[])
if __name__=="__main__":unittest.main(verbosity=2)
