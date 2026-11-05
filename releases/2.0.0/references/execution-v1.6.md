# 执行字段合同 v2.0（路径保留以兼容引用）

按schemas读完整字段，不复用旧batch或旧评分。先保存原始请求；--request必需。RUN在intake新建，后续阶段不能重写历史产物。

## brief
必需task_id、topic、audience、goal、platforms、facts、content_context、content_task、voice_profile、production_resources、objective、input_resolution。content_task选diagnosis/correction/tutorial/case/comparison/objection/planning/retention。objective选inquiry/trust/education/awareness/purchase/retention，与业务目标一致。content_context含scene/problem/memory_point/content_type；domain可明确行业。
facts含id/text/source/status(provided/verified/hypothetical)；旧样稿不当新事实。production_resources含id/description/status(available/planned/unavailable)，evidence_role可为production_only/proof/demonstration；相机不算证明。count_per_platform可按任务设置正整数，默认各3；不任意限制12篇。duration_limit_seconds及估速按任务。formula_lock只在用户明确锁定时使用，证据不满足先解决输入冲突，不静默换公式。

## intake
`intake --run RUN --input brief.json --request request.txt [--source 原件] [--kb 已验证缓存]`。
复制原始请求、附件和固定知识快照；source-manifest记录路径与SHA256，首次收据绑定。缺事实收窄主张，缺知识连接用明示的包内校验快照，不能声称远端在线读取。asset-pack返回候选记录/来源路径/文件与记录SHA、排序分及排除理由、来源覆盖和真实检索耗时。

## decision
顶层selected/rejected。selected每项id/platform/objective/buyer_decision/tension/stakes/intervention/proof/payoff/cta_reason/qualification/next_step必需。asset_refs含hook/body/calling/platform，每项asset_id/record_sha256/why。分别来自canonical hook、formula、CTA及对应平台路径。通用platform routing可用，但须解释实际迁移；不能硬引不相干专用公式示范。
selected与rejected都须selection_scores={audience_relevance,evidence_fit,platform_fit,action_fit}，各值{score:0..4,reason:具体依据}；权重30/30/20/20，选中每项≥3且≥80。每平台至少一个弃选，含platform/reason；若同分因制作成本或重复弃选，要说清比较依据。
`plan`通过后才生成成稿；目标、事实、机制变更重开RUN。

## batch
engine_version=2.0.0；performance_status=NOT_RUN。script.plan_id对应选中方案；formula_id/hook_id与封存一致。calling.intent=objective；qualification与next_step在结尾实际兑现；咨询可选CTA:04或09，购买CTA:10且核实供给和入口。
segments含id/role/duration_seconds/purpose/text/visual/subtitle/shot。role首hook、第二suspense、中间至少context/judgment/value、末calling，至少六段；前三秒与累计前八秒可读。body可拆多个判断段。台词不含制作标签。shot含framing/camera/action/material_id/edit_cue/sound/subtitle_focus/silent_hold_seconds，时间留给说话和操作。
asset_applications至少hook/body/calling，每项role/asset_id/segment_id/quote/transformation，引用真实原句和资产并解释迁移。read_test可选{status:NOT_RUN}或{status:MEASURED,seconds,evidence:真实记录位置}，估速不填MEASURED。
director_plan含format/visual_premise/performance_note/continuity/editing_rule/fallback/shoot_order；顺序覆盖所有段落恰一次。
`draft`封存batch-vN与事件；最多初稿加两次返修。

## review及输出
阅读review.schema.json与rubrics/quality.json。六项分数绑定段落/原句/reason；七项门禁带同样锚点；issues只填阻断项，notes放提醒。commercial_checks逐稿检查实际兑现，asset_checks逐稿检查机制实用；同/跨平台差异独立审。review_limitations写未做的真人/发布验证，不编审稿者身份。
batch_sha256、decision_sha256、asset_pack_sha256绑定确切字节，修改后重新审。validate通过后export，使用RUN/knowledge。编辑合格可以交付，发布状态还需当次官方规则核验、关键素材可用、真人试读记录。录入声明不是机器证明；人工必须回查其记录。

## 声明锚点与制作提醒
claim_links.claim必须是所指segment.text的原句子串，不能写释义。unverified_claims只装尚未解决且实际出现在台词中的事实主张；必须清空或删改主张才能编辑交付。素材待审、试读未做、发布权限未知放input_resolution、read_test、production_resources或production_limitations，不伪称事实已核验，也不作为未解决台词主张。
