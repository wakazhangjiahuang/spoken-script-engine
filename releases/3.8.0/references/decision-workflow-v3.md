# V3 运行合同

结构化字段见 [V3 Schema](../schemas/decision-workflow-v3.schema.json)。运行时还核对不同文件间的哈希、原文、权限和引用。

## M00–M03 原件、路由、检索

- 把本轮 Prompt、原件和授权冻结到运行目录。按产品、平台和篇数拆解，记录客户角色、时长、交付、锁定字句。新任务默认 A；直接成稿依据本轮明确授权，复审留原运行。
- 可选 `product_advantage_evidence` 接收已有产品属性、替代方案、体验、验收、服务与授权原件。台账定位至少到页/段/表格单元格/时间码。登记日期、哈希、读状态、事实范围、授权、证据结论、反证和有效期。无权素材只保留待补位置。
- `--run-context` 交接 `run_id`、`execution_mode`（proposal/direct/revision）、`offer`、`commercial_goal`、`production_mode`（none/04/05/04+05）、`route`、`knowledge` 和可选 `project_scope`。route 含 primary_adapter_id、adapter_version、business_model、route_reason、overlay_adapter_ids、route_confidence。主适配器按收费产品选择。覆盖层描述行业，项目资产仍按本客户授权检索。陌生业务用临时画像、通用方法和用户原件。
- AI 视频分别判定业务线（编辑/口播/数字人）、制作方式、商业产品和平台。插画把选题工作台作为客户任务参考，先读真实 Brief、设计稿、应用和商业凭证。温泉走本地体验，温泉行业覆盖层为候选，长寿桥项目事实仅限批准的项目资料。
- 核验知识仓身份、registry commit、资产提交、manifest SHA、条目及定位。已验条目的 `knowledge.assets` 至少含 id、locator、use、citation。明确记录暂无权限、无匹配、版本冲突及哈希失败。A/B 的来源快照和已用条目保持一致。

## M04–M07 决策与提案

`proposal --input TOPICS.json` 输入 `topics`，沿用 proposal-production 的 topic、copy、locks。新运行的每篇有 `decision_v3`。其结构见 `tests/v3_fixtures.py` 的数据示例。示例只用于识别数据形状。

- **customer。** 关联具体身份、使用与购买角色、场景、当前任务、根本需求、触发、损失/风险、替代、顾虑、决策标准和实际收益。若不同篇给同一客户决定同一答案，合并或改题。
- **evidence、category、purchase。** 第一轮比较品类/现状/延迟。第二轮比较具体服务、同类方案或买方标准。比较优势要求同口径的对象、场景、规格、时间和分母，以及已核验原件。适配理由可使用支持适用条件的属性、服务或 Demo。缺证时返回 PROJECT_CHOICE_PROOF_INSUFFICIENT 或改为 INFO_ONLY。授权无效或事实冲突进入 PUBLISH_HOLD。用户原话仍标 USER_PROVIDED；体验限定于样本，服务限定于履约范围。授权模拟须明确披露。
- **entries、value_map、claims。** 逐篇从真实顾虑、期望、风险或信息缺口等提出至少三个入口，保留写出来的候选及选择/否决理由。比较客户需求、点击理由、信息、收益、证据、平台与商业承接。胜出入口把事实→能力→差异或适配→收益→证据→购买理由→表达逐步对应。每项可公开主张引用证据 ID 和范围。
- **confirmation。** 用户看确认板，获知根本需求、项目理由状态、利益与证据、所选入口、承诺、平台任务、单一行动、评论任务与风险。可以给短正文示范。A 不交成稿和执行文件。用户确认后 `select` 封存所选 ID、原件哈希和知识快照。直接成稿同轮封存，原文保存授权。

## M08–M09 九字段逐层兑现

在 B 的每个 selected plan row 和 script 内填写 `v3_handoff_sha256`，值为 A 篇目的 decision_v3 规范哈希，可调用既有 `execution_contract.canonical`。script 的 `v3_content_entry` 为已选入口的客户问题，`v3_claims` 保存 claim_id、field 和实际稿件原文 quote。

| 字段 | 审查的问题 | 失败回退 |
| --- | --- | --- |
| audience | 谁在什么场景下决定什么，有没有买方角色？ | M04 |
| content_entry | 是否对应实际顾虑或决策，能否说明为什么胜出？ | M06.1 |
| cover_main | 对方有何明确点击理由，承诺能否兑现？ | M08.1 或 M05.1 |
| cover_sub | 给出哪条新增对象、场景、证据或范围？ | M08.1 |
| hook_0_3 | 哪个真实问题值得停下，是否推进了封面？ | M08.1 或 M06.1 |
| bridge_3_8 | 有什么新判断、证据或继续观看回报？ | M08.1 |
| body | 用什么方法和证据回答问题、兑现承诺和说明条件？ | M01/M05.1/M08.1 |
| calling | 能做哪一个动作，为什么，对用户有什么实际回报？ | M08.1 |
| comment | 如何从评论进一步识别同一需求或促成同一个选择？ | M08.1 |

三平台用同一事实底稿，分别核搜索/发现、推荐观看及社交传播的实际任务和账号功能。3 秒和 8 秒是脚本编辑节点。叙事可用真实商业案例、方法论、风险诊断、机会判断或流程拆解，选择与证据吻合的一种。评论默认独立发布。文案锁提供 EXACT/PREFIX；原始证据由摄取哈希保护，受影响的上游改动开新 A revision。

## M10–M11 制作与交付

模式由任务决定。输入 `review.v3_production` 时，按 `scripts/production_v3.py` 的字段绑定 Script_ID、Segment_ID、Shot_ID、原素材来源和权利。真人卡逐段给景别、机位、人物/产品/屏幕、动作、切点、声音、字幕、素材和验收。H3 逐镜加持续时间、背景、光线、表情、动作、运镜、Selection、生成提示、负面约束、验收。P01 身份、P02 场景、P03 局部、A01 声音、R 真实后插素材各注明授权和来源定位。真实产品、UI、测试和客户证据用真实素材后插。模型参数按实际生成当日核验。

六项制作门禁为内容、事实、分镜、素材、H3 和成片。尚未生成或实测标 NOT_RUN，视频失败可局部返工并复验。既有领域工作簿从 Canonical Script 生成。新的 04/05 卡从同一稿绑定逐字台词、时长与素材，重新打开 XLSX 比对字段与台词。XLSX 通过回读后生成同名 `.delivery.json`，附文件 SHA、篇目映射和状态。

## M12–M13 验收与回流

结构、事实与权利、专业语义、外部验证逐层放行。独立评审读取真实稿、证据和必要任务边界，隐藏生成者评分。逐篇给 `review.v3_acceptance`，绑定 batch_sha256 与 reviewer_id，含九字段各自的实际 quote、结论与理由，以及三道关口的字段列表、结论和理由。三关任一失败或未做即不能放行。保留原 15 项和各领域评分，并按失败字段退回相应模块。技能运行不替代真人试读、3–5 名目标客户盲读、权利审核或真实发布。未取得外部证据保留 VALIDATION_PENDING。

获得真实发布证据后用 `record-outcome` 保存平台、账号、帖子、时间窗口、指标定义与分母、对照基线、归因限制、原始数据文件及 SHA。未发布记 NOT_RUN。曝光、问询、预约、核销、成交和复购分别记录。只有有授权的编辑审批才晋升知识资产。
