"""Integrity and per-topic selection checks; no semantic-quality certification."""
import copy,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import acceptance_contract_v361 as gate
import test_acceptance_contract_v361 as fixture

class ReviewPacketIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.FourLayerAcceptanceV361Tests();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def result(self,review):
        f=self.f;return gate.validate_review(f.batch,f.decision,f.brief,review,f.run,f.batch_path)
    def rewrite_packet(self,review,transform):
        p=self.f.run/'blind-packet.json';packet=json.loads(p.read_text());transform(packet)
        p.write_text(json.dumps(packet,ensure_ascii=False),encoding='utf-8')
        review['reviewer_attestation']['blind_packet_sha256']=fixture.sha(p)

    def test_ids_and_hash_without_copy_are_blocked(self):
        review=self.f.make_review()
        self.rewrite_packet(review,lambda p:p.pop('actual_copy',None))
        r=self.result(review)
        self.assertEqual(r['status'],'BLOCKED')
        self.assertIn('BLIND_PACKET_ACTUAL_COPY_MISSING',r['errors'])

    def test_complete_matching_copy_is_accepted_as_pending(self):
        review=self.f.make_review();r=self.result(review)
        self.assertEqual(r['reviewer_attestation_status'],'PASS')
        self.assertEqual(r['status'],'VALIDATION_PENDING')
        self.assertFalse(r['passed'])

    def test_changed_body_with_recomputed_file_hash_is_blocked(self):
        review=self.f.make_review()
        self.rewrite_packet(review,lambda p:p['actual_copy'][0]['segments'][2].update(text='另一版未经审查的正文'))
        r=self.result(review);self.assertEqual(r['status'],'BLOCKED')
        self.assertTrue(any('BLIND_PACKET_COPY_MISMATCH' in e for e in r['errors']))

    def test_missing_body_segment_is_blocked(self):
        review=self.f.make_review()
        self.rewrite_packet(review,lambda p:p['actual_copy'][0]['segments'].pop(2))
        self.assertEqual(self.result(review)['status'],'BLOCKED')

    def test_author_scores_in_packet_are_blocked(self):
        review=self.f.make_review()
        self.rewrite_packet(review,lambda p:p.update(author_score=5))
        r=self.result(review);self.assertEqual(r['status'],'BLOCKED')
        self.assertIn('BLIND_PACKET_CONTAINS_REVIEWER_OR_SCORE_CUES',r['errors'])

    def test_three_plans_can_choose_three_separate_entries(self):
        f=self.f;dec=copy.deepcopy(f.decision);base=dec.pop('marketing_entry_competition')
        dec['selected']=[];dec['topic_competitions']=[]
        for i in range(1,4):
            comp=copy.deepcopy(base);chosen='C'+str(i);comp['selected_candidate_id']=chosen
            for c in comp['candidates']:
                c['selected']=c['candidate_id']==chosen
                c['selection_reason']='合成测试选择：本题单独比较自己的入口，不能继承其他题目的选择。'
                c['rejection_reason']='合成测试弃选：此入口不作为本题主入口，仍保留以便逐题核对。'
            dec['selected'].append({'id':'P'+str(i),'selected_entry_candidate_id':chosen})
            dec['topic_competitions'].append({'plan_id':'P'+str(i),'competition':comp})
        self.assertEqual(gate.validate_decision_competition(dec,f.brief,'illustration',f.run),[])

    def test_missing_topic_competition_cannot_silently_use_other_topic(self):
        f=self.f;dec=copy.deepcopy(f.decision);base=dec.pop('marketing_entry_competition')
        dec['selected'].append({'id':'P2','selected_entry_candidate_id':'C2'})
        dec['topic_competitions']=[{'plan_id':'P1','competition':base}]
        self.assertIn('TOPIC_COMPETITION_PLAN_COVERAGE_MISMATCH',gate.validate_decision_competition(dec,f.brief,'illustration',f.run))

    def test_duplicate_topic_competition_is_blocked(self):
        f=self.f;dec=copy.deepcopy(f.decision);base=dec.pop('marketing_entry_competition')
        dec['topic_competitions']=[{'plan_id':'P1','competition':base},{'plan_id':'P1','competition':copy.deepcopy(base)}]
        self.assertIn('TOPIC_COMPETITION_PLAN_IDS_DUPLICATED',gate.validate_decision_competition(dec,f.brief,'illustration',f.run))

    def test_blind_packet_preparer_emits_matching_actual_copy(self):
        import tempfile
        from test_pipeline import fixture as make_pipeline_fixture,prepare_run
        from prepare_review import prepare
        with tempfile.TemporaryDirectory() as tmp:
            batch,_=make_pipeline_fixture(platforms=('xiaohongshu',),count=1)
            run=Path(tmp)/'run';bp=prepare_run(run,batch)
            packet=prepare(run,bp,phase='blind')
            self.assertEqual(gate.validate_blind_copy(packet,batch['scripts']),[])
            self.assertEqual(packet['script_ids'],[batch['scripts'][0]['id']])

    def test_decision_schema_supports_per_topic_and_rejects_ambiguous_scope(self):
        import jsonschema
        schema=json.loads((ROOT/'schemas/decision-competition-v361.schema.json').read_text())
        dec=copy.deepcopy(self.f.decision);comp=dec.pop('marketing_entry_competition')
        dec['topic_competitions']=[{'plan_id':'P1','competition':comp}]
        jsonschema.validate(dec,schema)
        dec['marketing_entry_competition']=comp
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(dec,schema)

    def test_review_uses_the_candidate_ids_of_its_own_topic(self):
        f=self.f;comp=f.decision.pop('marketing_entry_competition')
        comp['selected_candidate_id']='OWN1'
        for i,c in enumerate(comp['candidates'],1):c['candidate_id']='OWN'+str(i)
        f.decision['selected'][0]['selected_entry_candidate_id']='OWN1'
        f.decision['topic_competitions']=[{'plan_id':'P1','competition':comp}]
        f.script['selected_entry_candidate_id']='OWN1'
        f.decision_path.write_text(json.dumps(f.decision,ensure_ascii=False),encoding='utf-8')
        f.batch_path.write_text(json.dumps(f.batch,ensure_ascii=False),encoding='utf-8')
        review=f.make_review()
        for check in review['delivery_acceptance'][0]['checks']:
            if check['criterion_id']=='topic_selection':check['evidence_refs']=['OWN1','OWN2','OWN3']
        self.assertEqual(self.result(review)['status'],'VALIDATION_PENDING')

    def test_current_guidance_is_selected_by_source_id_not_path_prefix(self):
        from prepare_review import review_guidance
        pack={'domain_asset_manifest':{'required_source_asset_ids':['GUIDE','TITLE']},
            'must_read_guidance':{'assets/private/guide.docx':{'source_asset_id':'GUIDE','text':'current guide'},
              'assets/shared/title.txt':{'source_asset_id':'TITLE','text':'current title guide'},
              'references/history.md':{'source_asset_id':'OLD','text':'retired example'}}}
        selected=review_guidance(pack)
        self.assertEqual({v['source_asset_id'] for v in selected.values()},{'GUIDE','TITLE'})

    def test_review_cannot_silently_omit_a_required_current_guide(self):
        from prepare_review import review_guidance
        pack={'domain_asset_manifest':{'must_read_source_asset_ids':['GUIDE']},'must_read_guidance':{}}
        with self.assertRaisesRegex(ValueError,'current domain guidance missing'):
            review_guidance(pack)

if __name__=='__main__':unittest.main()
