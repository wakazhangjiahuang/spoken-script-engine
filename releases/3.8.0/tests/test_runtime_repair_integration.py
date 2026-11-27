"""Fresh-process CLI checks, with synthetic input and real bundled domain loading."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v3_fixtures import context

ROOT=Path(__file__).resolve().parents[1]

class RuntimeRepairIntegrationTests(unittest.TestCase):
    def run_intake(self, domain):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);run=base/'new-run'
            request=base/'request.txt'
            quote='合成程序测试：核对启动和原始来源归档，不认证营销内容。'
            request.write_text(quote,encoding='utf-8')
            brief={'task_id':'synthetic-intake','topic':'合成入口检查','audience':'维护人员','goal':'验证来源归档',
                'domain':domain,'platforms':['xiaohongshu'],'facts':[],
                'content_context':{'scene':'桌面','problem':'检查入口','memory_point':'原件可追溯','content_type':'诊断'},
                'voice_profile':'普通解释','objective':'education','content_task':'diagnosis',
                'input_resolution':['合成夹具，仅验证执行契约'],
                'production_resources':[{'id':'PHONE','description':'手机固定机位','status':'available'}],
                'case_policy':'prefer_real','source_inventory':{'status':'complete',
                  'selection_reason':'此处使用合成测试请求，核对程序启动、文件读取和来源归档，不认证商业事实。',
                  'checked_assets':[{'asset_id':'A1','source_file':'sources/01.txt',
                    'source_sha256':hashlib.sha256(request.read_bytes()).hexdigest(),'locator':'第1段','source_quote':quote,'read':True}],
                  'fact_evidence':[],'relevant_real_case_ids':[],'selected_real_case_ids':[],'excluded_relevant_source_ids':[]}}
            if domain=='illustration':
                brief['audience_information']={'primary_role':'维护人员','current_problem':'核对原始资料读取',
                    'direct_benefit':'确认领域资料正确加载','information_type':'behind_scenes','source_class':'original_work'}
            bp=base/'brief.json';bp.write_text(json.dumps(brief,ensure_ascii=False),encoding='utf-8')
            ctx=base/"context.json";ctx.write_text(json.dumps(context()),encoding="utf-8")
            result=subprocess.run([sys.executable,str(ROOT/'scripts/run_pipeline_v3_6_1.py'),'intake',
                '--run',str(run),'--input',str(bp),'--request',str(request),'--run-context',str(ctx)],capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,(result.stdout+result.stderr)[-3500:])
            self.assertEqual((run/'sources/01.txt').read_bytes(),request.read_bytes())
            status=json.loads((run/'v3.6.1-validation-status.json').read_text())
            self.assertEqual(status['stage'],'intake');self.assertEqual(status['status'],'PASS')
            self.assertTrue((run/'asset-path-resolution.json').is_file())
            if domain=='illustration':
                pack=json.loads((run/'asset-pack.json').read_text())
                loaded={v.get('source_asset_id') for v in pack['must_read_guidance'].values()}
                self.assertIn('ILLUSTRATION-GUIDANCE-V2.0',loaded)
            if domain=='ai_video':
                manifest=json.loads((run/'domain-asset-manifest.json').read_text())
                self.assertIn('AI-VIDEO-BUSINESS-GUIDE-V4.1',manifest['must_read_source_asset_ids'])

    def test_plain_text_request_in_fresh_directory(self):self.run_intake('general')
    def test_plain_text_request_illustration_route(self):self.run_intake('illustration')
    def test_plain_text_request_ai_video_route(self):self.run_intake('ai_video')

if __name__=='__main__':unittest.main()
