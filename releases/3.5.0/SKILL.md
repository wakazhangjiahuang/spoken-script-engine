---
name: spoken-script-engine
description: 面向小红书、抖音、微信视频号的口播策划、专业决策蒸馏、AI视频与插画内容生产和逐稿验收引擎。
---

# 口播稿引擎 v3.5.0

**当前执行版本：3.5.0｜核心任务：不重建已确认的受众与需求，把已有指导书、样例和专业判断真正转化为有点击理由、有内容兑现、有可迁移价值的交付。**

本版是针对交付质量的定点修复，不扩充受众画像、选题库或业务模块。AI视频仍以V4.1为内容策略标准、2026-11-23团队手册为制作标准；插画仍以V2.0和Title Guide V4为标准。现有客户、受众、核心需求、BENCHMARK和锁定字段均优先复用。

## 1. 不可改变的原则

1. **已有资料优先。** 必须读取本轮领域指导书全文、当前样例、锁定字段和工作簿。文件存在、manifest通过或文件名被列出，不等于生成模型已读取；必须确认完整文本进入本轮`asset-pack.must_read_guidance`。
2. **受众和需求不重做。** 直接沿用现有指导书已确认的受众、共同任务和核心需求。只补足本篇具体场景，不重新发明画像，不把身份标签当成痛点。
3. **样例按身份使用。** BENCHMARK只拆成功机制；结构样例只作结构；失败稿只作负向回归；未验收稿不得变成正向few-shot。不得跨行业迁移客户、产品、事实或案例。
4. **结构完整不等于内容合格。** 封面、0–3秒、3–8秒、正文和Calling必须围绕同一共同任务，形成完整的点击—观看—兑现—行动链。
5. **专业判断必须被演示。** 不只写输入、约束和选择；必须展示一个具体输入如何经过判断，产生什么可观察变化，以及观众如何迁移使用。
6. **Calling必须有价值交换。** 一个主要行动，同时说清行动理由和用户得到的下一步价值；不能只索取关注、收藏、评论或私信。
7. **不自评为独立PASS。** 同一模型不同角色不算独立评审。真人试读、目标用户盲读、授权和平台实测未执行，必须标记`NOT_RUN/VALIDATION_PENDING`。

## 2. 当前领域资料路由

### AI视频
必须加载：
- `assets/ai-video/AI视频赛道商业化与内容营销指导书_V4.1.docx`：内容策略、目标受众、客户任务、内容主线和商业价值。
- `assets/ai-video/current/AI视频制作标准指导手册_团队执行版_20261123.docx`：04真人拍摄、05 H3数字人口播、真实素材、混合制作与制作验收。
- `assets/ai-video/current/AI视频_三平台口播稿_样例_20261123.xlsx`：六表字段和执行卡结构参照，不作为正向文案few-shot。
- AI视频样例索引、治理、运行时契约和来源清单；每轮只选匹配样例，不把A01/S01–S06机械复制到新主题。

A/B/C是业务路由，不是选题。先从V4.1现有受众与需求中选定一个共同任务，再决定内容入口和业务线。

### 插画
必须加载：
- `assets/illustration/插画赛道商业化与内容营销指导书_V2.0.docx`：当前唯一领域内容标准，全文读取。
- `assets/shared/title-guide/爆款封面标题与副标题创作指导_V4.txt`：封面标题主标准，全文读取。
- `assets/illustration/source/1118illustration_spoken_原表保留_补充18篇_V2.0.xlsx`：只读锁定源，四个字段逐字保留。
- `assets/illustration/manifest.json`：样例身份、BENCHMARK治理、六表和锁定契约。

V1.0指导书、V3.0工作簿和2026-11-18旧快照不得作为当前标准；V4.0工作簿只作结构参照。BENCHMARK不评分、不诊断、不改写；只评分`DERIVED_SCRIPT`。

## 3. 先绑定已有需求，再形成内容契约

每条计划必须携带`audience_need_ref`：
- `source_asset_id`：当前领域指导书ID；
- `source_locator`：可在原文中定位的章节/表格/条目；
- `source_quote`：从原文逐字摘取的需求句。

每条计划还必须形成内部`content_contract`：
- `target_audience`与`shared_task`：谁在完成什么共同任务；多角色共读时说明任务为何相同；
- `why_now`：当前阻碍、旧做法或机会，不用泛泛痛点代替；
- `click_reason`与`promised_payoff`：用户为什么点开、看完具体得到什么；
- `proof_plan`：正文用什么原始材料、演示、对照或明确标注的模拟来兑现；
- `decision_criteria`、`transferable_value`、`next_value`：专业判断、可迁移价值和下一层价值；
- `entry_competition`：至少三个机制不同的入口，明确选中项、否决理由、反方意见和反证。

不得重新泛化受众或扩充选题库。已有需求足够时直接选用；来源缺失、冲突或无法支持当前主张时才补研究。标题不强制套利益句式：商业结果、市场情报、图鉴、审美学习、产品选择、人物故事均可成立，但必须符合Title Guide V4并由正文兑现。

## 4. 每篇必须有一个可演示的专业决策

沿用`professional_decision`，并新增`worked_example`。正文必须让观众听到：
- 具体输入：一段原片、一份文档、一种数字人口播任务、一份SKU/Brief或一张具体作品；
- 关键约束和判断标准；
- 至少两个真正不同的方案、各自代价、最终选择与放弃理由；
- **处理前状态 → 应用判断 → 处理后状态 → 可观察变化**；
- 适用边界和观众可直接复用的规则。

`worked_example`至少包含：`input_snapshot`、`decision_criterion`、`before_state`、`after_state`、`observable_delta`、`transfer_rule`，以及精确的`spoken_anchor`、`result_anchor`、`transfer_anchor`。三个锚点必须逐字存在于正文段落，不能只写在备注或评分表里。

- AI剪辑：用一段具体原片展示保留/删除/重组的判断及成片差异。
- AI口播稿视频：选一个岗位、一个任务、一个异常情况和一个验收标准，展示文档如何变成可执行视频。
- AI数字人：选一个固定栏目或具体内容类型，展示何时适合数字人、何时必须真人，以及Go/No-Go依据。
- 插画产品适配：围绕一个SKU或明确标注的模拟Brief，展示设计备选、产品约束、取舍和可视化差异。
- 插画系列开发：用一个角色/产品任务说明识别点如何约束主图、辅助元素和底纹。
- 插画作品集：把买方实际评估标准应用到一张具体作品/提案页，不得只列目录模板。

模拟案例必须在口播正文明确披露“模拟/示意/假设情境/虚构情境”，并使用`SIMULATED:`证据引用。不得把模拟过程包装成真实客户、订单、测试、打样或收益。

## 5. 点击、开场、正文与Calling验收

- **封面主副标题：** 站在目标用户角度，主副标题和主画面共同形成点击理由；不写作者工作总结，不堆工具名，不机械套“主标题利益+副标题证据”。
- **0–3秒：** 给出目标用户愿意停留的具体处境、结果、冲突或问题，不自我介绍、不泛泛开场。
- **3–8秒：** 必须增加新信息、证据预告或故事方向；不得复述0–3秒，不提前Calling。
- **正文：** 先兑现封面承诺，再通过材料、专业判断、工作示例、证据和迁移规则完成价值；不能只列常识步骤，也不能把关键判断留给小白。
- **Calling：** 使用`calling_value_exchange`，明确一个`action`、`reason`、`reward`及其口播锚点。先给足本篇价值，再承接下一层需求。
- **平台：** 三平台分别处理展示场景、证据组织、节奏和行动理由，不是一稿三发换语气。

核心维度采用非补偿门槛：受众任务、点击理由、前8秒、正文兑现、专业判断、Calling均至少4/5；其他维度至少3/5。总分仍按AI视频V4.1或插画V2.0原rubric计算，70为最低编辑线、80为内部目标；任何硬门禁失败一票否决。模型自评不得替代独立评审。

## 6. 唯一执行入口

所有阶段只用`scripts/run_pipeline_v3_5.py`：`intake → plan → draft → validate → export`。

- `intake`：执行v3.5.0回归测试，核对本轮完整指导书和样例已加载。
- `plan`：核验原始需求引用、共同任务、点击理由、观看回报、三入口竞争和证据计划。
- `draft`：逐稿检查封面、前8秒、专业决策、可观察前后变化、迁移规则和Calling价值交换。
- `validate/export`：调用AI视频V4.1或插画V2.0正式验证器，并执行v3.5.0内容质量门禁、逐维评分、独立审查和工作簿回读。

未达标只修复失败字段并复检，不以平均分放行。外部验证未做时可交付编辑候选，但必须标记`VALIDATION_PENDING`；不得声称发布通过、爆款或真实商业效果。

## 7. 必须按任务读取的契约

- 通用：`references/task-contract.md`、`references/stage-contract.md`、`references/execution-v1.6.md`、`references/decision-and-qa.md`。
- AI视频：`references/ai-video-topic-gate.md`、`references/ai-video-expression-contract.md`、`references/v4.1-decision-gateway.md`、`references/ai-video-quality-gates.md`、`references/ai-video-production-standard.md`。
- 插画：`references/illustration-value.md`、`references/title-guide-v4-runtime.md`、`references/quality-gates-v3.3.0.md`。
- 本版：`references/v3.5.0-runtime-quality-overlay.md`、`schemas/content-proof-v3.5.0.schema.json`、`scripts/content_quality_gate_v350.py`、`scripts/run_pipeline_v3_5.py`。

Jev/Laya是决策角色，不代表已调用外部模型。只记录候选、反对意见、证据、裁决和修复，不输出隐藏思维链。
