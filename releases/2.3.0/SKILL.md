---
name: spoken-script-engine
description: 为小红书、抖音、微信视频号创作、改写和诊断跨行业口播；先审受众观看理由，再交封面主副标题、黄金三秒、3–8秒、正文、Calling、逐段分镜和评论钩子。独立内容审阅与源式核对分开；按要求交付XLSX或完整TXT，支持单篇与批量。
---

# 口播稿引擎 v2.3.0

把用户认可的通用手册转为可执行判断，把三平台18篇样例作为有条件的编辑参照；“已认可”不等于所有任务适配或已验证爆款。方法通用，案例有行业；不得把插画ABC、客户国别、时间、旧评分或未测效果迁移成新任务事实。默认所选平台各3篇，未选平台默认三平台；明确篇数优先，1篇就做1篇、每平台6篇就做18篇。明确“总计N篇”时先给出合理平台分配，不误解为每平台N篇。保留锁定主题、真实创业团队口吻和有效专业判断。

## 起点与质量合同

先从原请求确定受众的直接业务利益与信息来源，再读[从资产到台词](references/source-to-speech.md)，再读[逐环节合同](references/stage-contract.md)，再按[执行字段](references/execution-v1.6.md)整理需求。写清：“谁在做什么，卡在哪个决定，听完能判断什么”。一篇一个主要受众、决策和业务目的。任务轴为诊断/纠偏/教程/案例/比较/异议/规划/留存；平台轴决定入口、证据、节奏与行动，不把平台等同固定受众。

原始请求与本轮最新原件优先；用户明确陈述的本人项目按provided写，不能一律降为假设，未读取原证不能升级为verified。事实、推断、示例、待核验分开；缺证据收小主张或明确示例，不编客户冲突、返工、评价、成交和收益。先决定首镜和证据可如何拍，再写台词。

唯一评分来源：assets/kb-snapshot/rubrics/quality.json。六项权重依次为15/15/25/15/15/15；每项0–4用于辅助定位，单项不足须修；不以加权总分作达标阈值；事实、开场兑现、证据、平台、营销、口语、可拍七项门禁不能用总分抵消。这是辅助编辑记录。实际首屏与八项交付否决先于总分；模型校对不能认证用户认可、高点击或内容达标。

插画/印花任务必须读[插画信息价值](references/illustration-value.md)及检索返回的1118 Word、delivery-standard和来源冲突审计，填写audience_information；优先真实项目、市场/商品、渠道和原创应用信息。只有明确技术需求且有可见测试，DIY笔刷才做独立教程。其他行业不加载此分支。

## 五阶段生产，十二环节交接

使用技能目录中的 scripts/run_pipeline.py；RUN是本次新目录。先读schemas，不猜字段。内部JSON不要求用户填写，不额外交付繁杂审计表。

1. **Intake｜需求、事实与检索**：保存原始请求request.txt，运行 `intake --run RUN --input brief.json --request request.txt`，每份附件追加`--source 路径`。按[知识协议](references/github-and-memory.md)获取固定版本；可传`--kb 已校验缓存`，RUN复制并绑定该知识版本。检索依次判断内容任务、业务目的、证据可用性，再按主题排序。读取must_read_guidance的用户利益、口吻原文，以及选用的标题原行、完整口播机制、正文公式、Calling、平台策略与完整样例。按同观众/同问题/同证据联动配套，不能分别按热词拼接。先决定本条交付的外部信息或具体判断，再选公式；插画分支返回当前1118标准/原文/冲突处理，明确case_ids或event_family才加载案例及对应完整H列样稿；原先V0.2及approved开头是历史参照，不能带旧认可状态放行。approved-examples是已认可编辑样稿；real_cases是可核验业务案例；published_scripts是已发布内容，三个数量分开。没有匹配就如实报告，不强塞异业故事。
2. **Plan｜首屏先审、比较与封存**：读asset-pack.json。插画任务先写同案同受众的两种不同机制opening_candidates（id/plan_id/platform/mechanism_id/cover_main/cover_sub/hook/suspense/first_shot/proof_fact_ids），用scripts/prepare_openings.py --brief RUN/brief.json --candidates candidates.json --output opening-panel.json生成只含实际首屏的包。独立上下文先复述看点及继续理由，逐候选给opening_review；只允许推荐为RECOMMEND_FOR_DRAFT的候选进入selected.opening_candidate_id，不得先写正文再补理由。把opening_candidates/opening_review一并保存进decision。随后每平台选N个方案及至少1个弃选。按selection.json对受众相关、证据适配、平台适配、行动适配逐项0–4评分并写具体理由；选中每项≥3、总分≥80。记录买家决定、真实张力、取舍、证据、兑现和行动；填写audience_contract/source_recipe/proof_basis，对照原式与样例说明迁移和不迁移内容。样例受众不一致就标结构参照，不能冒充精确样例命中。asset_refs绑定真实ID/哈希及本次用法，标题公式不冒充口播机制；不适配的AI标题可no_fit明确弃用，不能为填字段冒充精确业务匹配。插画分支另封存information_contract与opening_reference。执行 `plan --run RUN --input decision.json` 成功后才写成稿。改目标/事实/机制须新RUN。已封存首屏的主副标题、前两句或首镜visual变更，也须新RUN重做首屏审与plan，不能在原RUN更改decision。
3. **Draft｜六项创作与导演**：生成engine_version=2.3.0的batch。每稿按hook、suspense、context、judgment、value、calling组织，正文可分多个判断段。第一段≤3秒，前两段累计≤8秒；按可读字速和静默操作留时核算，不挤长句冒充黄金三秒。批量先在本次任务内完成1–2篇不同路线的试稿与复核，再扩写。各稿明确交付cover_main、cover_sub、0–3秒、3–8秒、正文、Calling、全段分镜和comment_hook；title只作发布标题。comment_hook包含line/viewer_reason/input/next_step/intent/placement，结尾复用或置顶，与Calling同一目的。首个判断及时兑现开场，接单入口不能只兑现线条教程；插画首句痛点/直接利益优先，第二段交付新增具体事实，information_delivery逐项引用台词与当前事实。正文说明选什么、为什么、放弃什么、证据在哪里、何时适用；将能力翻译成观众能用的判据。审美表达落在层级、具体、克制和一致，非视觉行业不套颜色/笔刷词。Calling只留一个主动作，给观众一个具体行动理由，延续已证明价值；不默认关键词评论，不把价值拖到下一条。composition逐项绑定原式变量、正文节点与实际台词；正文payoff/takeaway/calling均有原句，备注不代替正文。台词不能带“案例：/专业判断：/观众所得：”制作标签。逐段绑定素材、镜头动作、字幕、切点和替代；available/planned/unavailable分开。[开场](references/hook-workshop.md)、[自然口语](references/natural-voice.md)、[导演](references/director-workflow.md)。执行 `draft --run RUN --input batch.json`。
4. **Independent review｜实际成品先审、源式后审**：先用scripts/prepare_review.py --run RUN --batch RUN/batch-v1.json --output content-input.json，默认content阶段只给实际八项、用户原请求、原件和素材状态，隐藏生产者利益解释、选式理由与评分。独立上下文记录content_decisions与delivery_checks（实际八项原句＋理由＋delivery_sha256）；可判REWRITE，不能从备稿替差稿补看点。只有本版内容判断为DRAFT_FOR_USER_REVIEW后，再用同脚本--phase fidelity --content-review content-review.json生成源式输入，按[复审标准](references/decision-and-qa.md)完成原式、composition_checks、information_checks与六维辅助记录。后一步不能抬分推翻前一步否决。最多两次同方案定向返修；换事实/目的/机制重开RUN。用户认可、真人和发布测试分别未知，不把模型意见叫“达标”。
5. **Validate & export｜校验、交付与后续**：执行 `validate --run RUN --input RUN/batch-v1.json --review review.json --output validation.json`；通过后同参数改用export并将output设为XLSX。正式唯一[表格合同](references/task-contract.md)：总览＋所选平台各一表＋拍摄执行卡；三平台为5表。平台稿能分段看也能整篇复制，执行卡逐句对应。导出后逐字回读；实际看预览，未看不称视觉验收。真人试读、素材和规则不足时保留明确未完成状态；不阻止诚实编辑交付，也不宣称发布就绪。

## 后续环节与效率

- **平台核验**：[发布检查](references/platform-release-check.md)。官方条文/机制研究/创作假设/待核验分层；核对当次来源、日期、范围与账号权限，不编算法权重。小红书给可复看判据，抖音首镜与快速证据，视频号给合作适配依据，均为创作策略。跨平台保留原事件、主要受众、核心利益与目的，改变首镜、证据位置、节奏或口语表达；不能为差异化擅自换成另一种受众或教程任务。
- **真实验证**：用户盲测能否认出任务与复述判据；同行检查专业依据；新手按表试拍；平台同目标单变量测试，记录样本/分母/窗口/基线。未运行一律NOT_RUN，不用高分证明效果。
- **知识回流**：只有授权反馈才入库；事实更正、偏好、编辑采纳与实测表现分开，品牌隔离、去重、待同步与回读确认分开。新增方法须有适用条件与反例，不自动晋级官方规则。
- **控制成本**：一份简报、一份校验快照、一轮候选比较、批量生产、独立复审。只补查缺口和返修失败段；如实记录检索耗时、候选量和返修数。不以增加公式/页面/工作表充当深度。
- **边界**：收据证明记录顺序和文件绑定，不证明私下推理顺序或审稿者身份。自动校验不替代语义审阅。只在用户授权范围保存，不自动发布、不向他人发送消息。
