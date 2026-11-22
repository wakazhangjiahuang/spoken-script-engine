import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
 def test_workbook_contract(self):
  s=json.loads((ROOT/'schemas/illustration-workbook.schema.json').read_text(encoding='utf-8'))
  self.assertEqual(len(s['properties']['sheets']['const']),6)
  self.assertEqual(s['properties']['shooting_segments']['const']['total'],108)
  self.assertEqual(s['properties']['locked_fields']['const']['cells'],72)
 def test_review_contract_has_no_benchmark_class(self):
  s=json.loads((ROOT/'schemas/illustration-review.schema.json').read_text(encoding='utf-8'))
  item=s['properties']['items']['items']['properties']
  self.assertEqual(item['sample_class']['const'],'DERIVED_SCRIPT')
 def test_production_contract_has_dynamic_h3(self):
  s=json.loads((ROOT/'schemas/illustration-production.schema.json').read_text(encoding='utf-8'))
  self.assertIn('h3_shots',s['required'])
if __name__=='__main__': unittest.main()
