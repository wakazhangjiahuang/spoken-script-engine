import unittest
from content_depth_gate_v344 import validate_content_depth
class GateTests(unittest.TestCase):
 def test_missing_tradeoff_anchor_blocks(self):
  s={"id":"T","segments":[{"id":"S","role":"hook","text":"hook"}],"professional_decision":{"spoken_anchors":{},"options_considered":[]}}
  errors,_=validate_content_depth({"scripts":[s]},{"items":[]},"illustration")
  self.assertTrue(any("SPOKEN_DEPTH_ANCHOR_MISSING:option_tradeoff" in x for x in errors))
 def test_missing_value_review_blocks(self):
  s={"id":"T","segments":[{"id":"S","role":"hook","text":"hook"}],"professional_decision":{"spoken_anchors":{},"options_considered":[]}}
  errors,_=validate_content_depth({"scripts":[s]},{"items":[{"script_id":"T"}]},"illustration")
  self.assertTrue(any("CONTENT_VALUE_REVIEW_MISSING" in x for x in errors))
if __name__=="__main__": unittest.main(verbosity=2)
