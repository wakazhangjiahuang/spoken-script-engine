"""Behavioral regression of routing, gates, frozen sources and export. Synthetic scores only."""
import copy,json,tempfile,unittest,subprocess,sys
from pathlib import Path
from test_pipeline import fixture,prepare_run,PipelineTest
from retrieve_assets import ROOT,pack
from execution_contract import read,digest,check_plan
from validate_batch import validate,publication_ready
from export_xlsx import build
class V2Tests(unittest.TestCase):
 def setup_run(self,p,plats=('douyin',),count=1):
  b,r=fixture(plats,count);f=prepare_run(p,b);r.update(batch_sha256=digest(f),decision_sha256=digest(p/'decision.json'),asset_pack_sha256=digest(p/'asset-pack.json'));return b,r,f
 def test_six_weights(self):
  d=read(ROOT/'assets/kb-snapshot/rubrics/quality.json')['dimensions'];self.assertEqual([x['weight'] for x in d],[15,15,25,15,15,15])
 def test_objection_retrieves_f06(self):
  b,_=fixture();b['brief']['content_task']='objection';o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertIn('SHARED:F06',[x['asset_id'] for x in o['assets']])
 def test_case_requires_proof(self):
  b,_=fixture();b['brief']['content_task']='case';o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertNotIn('SHARED:F13',[x['asset_id'] for x in o['assets']]);self.assertIn('SHARED:F13',[x['asset_id'] for x in o['excluded_candidates']])
 def test_locked_formula_is_reachable(self):
  b,_=fixture();b['brief']['formula_lock']='SHARED:F06';o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertEqual([x['asset_id'] for x in o['assets'] if x['source_path']=='shared/formulas.jsonl'],['SHARED:F06'])
 def test_locked_case_without_proof_fails(self):
  b,_=fixture();b['brief']['formula_lock']='SHARED:F13'
  with self.assertRaises(ValueError):pack(ROOT/'assets/kb-snapshot',b['brief'])
 def test_case_with_proof_available(self):
  b,_=fixture();b['brief'].update(content_task='case',formula_lock='SHARED:F13');b['brief']['production_resources'].append({'id':'DEMO','description':'本次原件','status':'available','evidence_role':'proof'});self.assertIn('SHARED:F13',[x['asset_id'] for x in pack(ROOT/'assets/kb-snapshot',b['brief'])['assets']])
 def test_approved_not_real_cases(self):
  b,_=fixture();b['brief']['topic']='母婴印花';o=pack(ROOT/'assets/kb-snapshot',b['brief']);c=o['coverage']['douyin'];self.assertEqual(c['current_editorial_examples_available'],6);self.assertEqual(c['current_editorial_examples_selected'],2);self.assertEqual(c['approved_editorial_examples_selected'],0);self.assertEqual(c['real_cases'],0);self.assertEqual(c['published_scripts'],0)
 def test_ai_does_not_reuse_design_samples(self):
  b,_=fixture();b['brief']['topic']='企业知识库系统';o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertEqual(o['coverage']['douyin']['approved_editorial_examples_selected'],0)
 def test_low_plan_score_is_optional_diagnostic(self):
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');plan=read(f.parent/'decision.json');plan['selected'][0]['selection_scores']['evidence_fit']['score']=2;self.assertEqual(check_plan(plan,b['brief'],read(f.parent/'asset-pack.json')),[])
 def test_wrong_score_block(self):
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');r['items'][0]['scores']['suspense'].update(segment_id='S0',quote=b['scripts'][0]['segments'][0]['text']);self.assertIn('wrong scoring block suspense',str(validate(b,r,digest(f),run_dir=f.parent)))
 def test_old_dimensions_cannot_pass(self):
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');r['items'][0]['scores']['narrative_progression']=r['items'][0]['scores'].pop('suspense');self.assertFalse(validate(b,r,digest(f),run_dir=f.parent)['passed'])
 def test_fact_gate_fails(self):
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');r['items'][0]['gate_checks']['facts']['passed']=False;self.assertFalse(validate(b,r,digest(f),run_dir=f.parent)['passed'])
 def test_missing_reading_not_ready(self):
  b,r=fixture();r['platform_checks'][0].update(status='VERIFIED',publish_ready=True);self.assertFalse(publication_ready(b,r))
 def test_measurement_needs_record(self):
  b,r=fixture();r['platform_checks'][0].update(status='VERIFIED',publish_ready=True);b['scripts'][0]['read_test']={'status':'MEASURED','seconds':40};self.assertFalse(publication_ready(b,r))
 def test_real_duration_and_material_ready(self):
  b,r=fixture();r['platform_checks'][0].update(status='VERIFIED',publish_ready=True);b['scripts'][0]['read_test']={'status':'MEASURED','seconds':40,'evidence':'synthetic fixture record'};self.assertTrue(publication_ready(b,r));b['brief']['production_resources'][0]['status']='planned';self.assertFalse(publication_ready(b,r))
 def test_export_single_and_18(self):
  for plats,n in [(('douyin',),1),(('xiaohongshu','douyin','channels'),6)]:
   with tempfile.TemporaryDirectory() as d:
    b,r,f=self.setup_run(Path(d)/'run',plats,n);v=validate(b,r,digest(f),run_dir=f.parent);self.assertTrue(v['passed'],v);o=build(b,r,str(Path(d)/'out.xlsx'),ROOT/'assets/kb-snapshot',v);self.assertEqual(o['sheets'],len(plats)+2);self.assertEqual(o['scripts'],len(plats)*n);self.assertEqual(o['shot_rows'],len(plats)*n*6)
 def test_original_request_required_cli(self):
  with tempfile.TemporaryDirectory() as d:
   b,r=fixture();p=Path(d);(p/'brief.json').write_text(json.dumps(b['brief']));v=subprocess.run([sys.executable,str(ROOT/'scripts/run_pipeline.py'),'intake','--run',str(p/'run'),'--input',str(p/'brief.json')],capture_output=True,text=True);self.assertNotEqual(v.returncode,0);self.assertIn('original request',v.stderr)
 def test_trust_duplicates_do_not_bypass_evidence(self):
  for task in ('diagnosis','case','planning'):
   b,_=fixture();b['brief'].update(objective='trust',content_task=task);o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertNotIn('SHARED:F16',[a['asset_id'] for a in o['assets']])
 def test_empty_receipt_bindings_rejected(self):
  from execution_contract import provenance
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');e=read(f.parent/'event-001.json');e['files']={};(f.parent/'event-001.json').write_text(json.dumps(e));self.assertIn('missing required receipt binding intake',provenance(f.parent,f))
 def test_missing_source_manifest_rejected(self):
  from execution_contract import provenance
  with tempfile.TemporaryDirectory() as d:
   b,r,f=self.setup_run(Path(d)/'run');(f.parent/'source-manifest.json').unlink();self.assertIn('modified stage artifact source-manifest.json',provenance(f.parent,f))
if __name__=='__main__':unittest.main(verbosity=2)
