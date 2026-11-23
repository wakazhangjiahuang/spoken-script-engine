import unittest
from content_depth_gate_v344 import validate_content_depth
class NegativeRegression(unittest.TestCase):
 def test_old_thin_script_is_rejected(self):
  ids=["AI-DY-A01","AI-WX-B01","AI-XHS-C01","IL-DY-B01","IL-WX-B02","IL-XHS-A01"]
  scripts=[{"id":x,"script_id":x,"segments":[{"id":"S1","role":"hook","text":"generic list"}],"professional_decision":{"spoken_anchors":{},"options_considered":[]}} for x in ids]
  for domain in ("ai_video","illustration"):
   errors,_=validate_content_depth({"scripts":scripts},{"items":[]} ,domain)
   self.assertEqual({x for x in ids if any(e.startswith(x+":") for e in errors)},set(ids))
if __name__=="__main__":unittest.main(verbosity=2)