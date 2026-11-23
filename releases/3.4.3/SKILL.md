---
name: spoken-script-engine
description: 面向小红书、抖音、微信视频号的口播策划、专业决策蒸馏、AI视频与插画内容生产和逐稿验收引擎。
---

# 口播稿引擎 v3.4.3

**当前执行版本：3.4.3｜核心任务：让已确认的指导书、受众需求和样例真正进入生成与验收链路。**

本版本是执行入口，不重建受众画像、不扩充选题库、不替换AI视频V4.1或插画V2.0指导书。所有规则优先复用现有私有资产；只在来源缺失、冲突或无法支持当前任务时补充研究。

## 1. 不可改变的工作原则

1. **已有资料优先。** 先读取本轮原始请求、当前领域指导书、样例、锁定字段和工作簿。文件存在、manifest通过或文件名被列出，不等于生成模型已经读取；必须把当前指导书全文加载进本轮资产包。
2. **受众和需求不重做。** 沿用指导书中已经确认的目标受众、共同任务和核心需求。不得把客户身份标签当成需求，不得为了凑篇数新增画像或泛化痛点。
3. **样例按身份使用。** BENCHMARK只拆成功机制；结构样例只作结构；候选样例不自动升级为正向few-shot；失败稿只作负向回归。不得跨行业迁移事实、客户、产品或脚本结构。
4. **结构完整不是质量合格。** 标题、黄金开场、3–8秒、正文、Calling每一项都必须为同一个目标用户任务服务，并兑现明确观看回报。
5. **专业判断必须进入口播。** 不得只在分析、备注、拍摄卡或评分表中写“需要专业判断”。正文必须讲出具体输入、约束、备选、取舍、理由、边界和用户下一步。
6. **生成者不为自己出独立PASS。** 未执行的外部评审、真人试读、目标用户盲读、授权检查和平台实测必须标记NOT_RUN/VALIDATION_PENDING。

## 2. 当前领域资料路由

### AI视频
必须加载：
- `assets/ai-video/AI视频赛道商业化与内容营销指导书_V4.1.docx`：内容策略、目标受众、客户任务与商业价值的唯一领域指导书。
- `assets/ai-video/current/AI视频制作标准指导手册_团队执行版_20261123.docx`：04真人拍摄、05 H3、素材角色、制作与验收标准。
- `assets/ai-video/current/AI视频_三平台口播稿_样例_20261123.xlsx`：六表结构、字段与执行卡参照，不作为正向文案few-shot。
- AI视频样例索引、治理、运行时契约和来源清单；每轮最多选一个匹配样例，A01/S01按既有规则隔离。

A/B/C业务线是业务路由，不是选题。先使用V4.1已有客户需求和内容主线，选出客户真正关心的任务，再确定业务线、入口和脚本。

### 插画
必须加载：
- `assets/illustration/插画赛道商业化与内容营销指导书_V2.0.docx`：当前唯一领域内容标准，必须读取全文。
- `assets/shared/title-guide/爆款封面标题与副标题创作指导_V4.txt`：标题主标准，必须读取全文。
- `assets/illustration/source/1118illustration_spoken_原表保留_补充18篇_V2.0.xlsx`：只读锁定源，四个字段逐字保留。
- `assets/illustration/manifest.json`：样例身份、BENCHMARK治理、六表与锁定契约。

V1.0指导书、V3.0工作簿和2026-11-18旧快照不得作为当前正向样例；V4.0工作簿只作结构参照。BENCHMARK不评分、不诊断、不改写；只评分DERIVED_SCRIPT。

## 3. 先绑定已有需求，再策划内容

每个选题计划必须携带`audience_need_ref`：
- `source_asset_id`：当前领域指导书ID；
- `source_locator`：可在原文中定位的章节/表格/条目；
- `source_quote`：从原文逐字摘取的需求句。

不得用模型自写的概括句冒充来源原句。计划中的`viewer_task`必须明确用户要完成的具体任务；`proof_plan`说明本篇用什么材料兑现。已有需求足够时直接选择，不重新做泛化调研。

选题入口竞争沿用现有Topic Gate：比较至少三个机制不同的入口，依据用户收益、材料匹配、兑现能力和风险裁决；不是换词凑三个。选题不成立就淘汰，不强行写稿。

## 4. 每篇脚本的专业决策单元

每篇脚本必须有`professional_decision`，且其`audience_need_ref`必须与批准计划完全一致。决策单元包括：
- `viewer_task`：与计划一致的具体任务；
- `case_mode`：real / simulated / method；
- `concrete_input`：本次真实材料或明确的模拟输入；
- `constraints`：至少两个会改变判断的约束；
- `options_considered`：至少两个实质不同的方案及各自trade-off；
- `chosen_option` / `rejected_option`：明确选择与放弃；
- `decision_reason`：说明为何该方案更适合当前约束；
- `evidence_refs`：可追溯到当前来源、用户资料或明确SIMULATED编号；
- `applicability_boundary`：适用与不适用条件；
- `viewer_action`：观众能直接执行的下一步；
- `spoken_anchors`：分别锚定选择、被否决方案、理由、边界和用户动作的实际口播原句。

如果正文只是“分四步”“注意细节”“需要专业判断”“根据实际情况”，但没有讲出具体选择和原因，判定不合格。模拟案例必须在口播中披露，不得把模拟结果包装成真实客户、订单、收益或项目。

## 5. 营销表达与脚本验收

- **封面：** 站在目标用户角度呈现点击利益或信息缺口，不是作者工作总结或工具功能罗列；主副标题共同形成完整营销单元。
- **0–3秒：** 迅速唤醒目标用户的具体处境、冲突、结果或问题；不自我介绍，不空喊口号。
- **3–8秒：** 必须增加新信息、证据预告或故事推进，不复述开场，不提前Calling。
- **正文：** 先兑现核心承诺；材料、专业判断、方法和迁移价值必须形成完整链条。不能只给常识清单，也不能把关键判断留给小白自行完成。
- **Calling：** 一个主要行动，说明用户为什么值得做、需要什么输入、下一步会得到什么；不能机械索取私信。
- **平台：** 三平台分别处理点击入口、证据组织、内容节奏和行动理由，不是一稿三发换语气。每篇另写`platform_rationale`，说明本平台为何采用这个入口、证据呈现和行动方式，供独立评审逐字段核对。

评分引用必须定位到实际标题字段或具体口播段落。每维最低3/5；总分按当前领域rubric计算；硬门禁失败一票否决，不用平均分掩盖单篇问题。

## 6. 执行入口与状态

所有阶段只用 `scripts/run_pipeline_v3_4.py`：
`intake → plan → draft → validate → export`。

- intake后检查当前指导书全文和当前样例/结构资产是否进入本轮资产包；
- plan时检查每条选题绑定了原始需求；
- draft后检查每篇正文的专业决策与逐句口播锚点；
- validate/export时检查逐稿独立审查、字段级评分、硬门禁、证据和工作簿回读。

AI视频继续使用`validate_v41.py`正式验证器；最终发布要求真人/盲读全通过时使用`--require-v41-full-validation`。插画使用V2.0六表与锁定字段验证器。

未达标时只修复失败字段并复检；两轮修复仍不合格，标记REWRITE/REVISE，不得导出为PASS。外部验证未做时可交付编辑候选，但必须标记VALIDATION_PENDING，不得称为发布通过或爆款。

## 7. 必须按任务读取的契约

- 通用任务：`references/task-contract.md`、`references/stage-contract.md`、`references/execution-v1.6.md`、`references/decision-and-qa.md`。
- AI视频：`references/ai-video-topic-gate.md`、`references/ai-video-expression-contract.md`、`references/v4.1-decision-gateway.md`、`references/ai-video-quality-gates.md`、`references/ai-video-production-standard.md`。
- 插画：`references/illustration-value.md`、`references/title-guide-v4-runtime.md`、`references/quality-gates-v3.3.0.md`。
- 本版新增：`references/v3.4.3-runtime-quality-overlay.md`、`schemas/professional-decision.schema.json`、`scripts/content_decision_gate_v342.py`。

Jev/Laya是决策角色，不代表已调用某个外部模型。只记录可审计的候选、反对意见、证据、裁决和修复，不输出隐藏思维链。
