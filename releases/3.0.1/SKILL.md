---
name: spoken-script-engine
description: 按当前原件创作、改写与诊断跨行业三平台口播；围绕共同任务提炼观看动机，联动封面主副标题、前八秒、正文、Calling、评论和逐段分镜；独立成品审阅后核原式，交付逐字一致的XLSX或完整TXT。
---

# 口播稿引擎 v3.0.1

**发布包版本：3.0.1｜引擎/数据合同版本：3.0.0｜知识快照：20261118-evening。** `engine_version=3.0.0` 是批次数据合同标识，不代表 Skill 发布包仍停留在 3.0.0。

先读[当前通用方法](assets/kb-snapshot/standards/current-method.md)，再读[字段合同](references/execution-v1.6.md)和schemas。仅使用release-policy与Manifest允许的当前资料；18篇插画口播、108执行段及15组封面是本轮参考，不是18笔事实已核的订单或18篇效果已验证的成品。旧样例、旧资料路径和旧快照禁止回退。

## 判断起点

原始请求与当前附件优先。围绕一个共同任务、一个主要交付和一个行动目的；可以有共享任务的不同岗位。价值可以是商业应用、选择方法、整理资料、具名审美、人物经历、工艺变化、娱乐/生活任务；不能把插画业务利益套全部赛道。

从[九种注意力基因](assets/kb-snapshot/shared/attention-genes.jsonl)按材料选入口，并写清成立与失效条件。熟悉对象/起点连接观众在意的变化、答案或具体交付。营销力度来自真实内容关系与情绪，不能只报作者事件，也不能靠增加“竟然/必看/别再”装饰。工具可以连接真实商业应用或风格学习；不夸工具导致成交或同款保证收入。

封面主副与主画面共同判断；主标题可为风格、图鉴、人物、问题或结果，副标题可补方法、情绪、范围、事实或场景。未直写利益不自动否决。封面字段不等于发布标题、配文和关键词。默认新主12、副18可见字符是工作室约束，复杂emoji按完整字素计；用户明确锁定文本保留字符和标点，超长记例外，不擅改，也不扩大新稿默认。

用户明确本人项目按provided写；未读原证不升级verified，样例不作为新事实。公开商品、品牌内部开发、当前采购、本人合作、上市与收款分别核对。原文疑似漏字/反向句保留并记录冲突，不据此编造。内部核验与权利提醒放制作记录；除非本题就是风险/边界，不挤占故事和审美学习。

## 五阶段执行

RUN为新任务目录，内部JSON由宿主生成，不让用户填表。默认所选平台各3篇；明确平台/篇数/格式优先。段数按内容，不固定六镜头；平台不等于受众或句式。

1. **Intake**：保存逐字request.txt，整理brief，逐附件追加`--source`，运行`scripts/run_pipeline.py intake --run RUN --input brief.json --request request.txt`。只用[当前知识协议](references/github-and-memory.md)的固定快照。先读实际返回的通用方法、机制、基因和适用条件。插画/印花任务才加载本轮域样例；其他行业仅用通用方法及自己的原件。检索按共同任务、交付、证据类型匹配，不按热词拼凑；明确无匹配不编历史案例。
2. **Plan**：围绕当前任务生成至少两个不同机制的实际首屏：封面主副、首句、次句、首镜与来源；显式锁定字段原样保留。用`prepare_openings.py --brief RUN/brief.json --candidates candidates.json --output opening-panel.json`投影，不给作者理由、偏好与分数。独立上下文审实际表达：对象/价值可认领、内容有增量、继续理由具体、封面与开场一致、事实范围成立；情绪/风格/资料可为价值。推荐进入写作不等于用户认可或高点击。decision封存opening_candidates、opening_review及selected.opening_candidate_id；填写audience_contract、source_recipe（含当前gene资产/哈希/迁移与不迁移）、proof_basis与asset_refs。选题评分可选，仅诊断，不设80分放行；每平台记录至少一个弃选及具体理由。运行`plan --run RUN --input decision.json`后才写整篇。
3. **Draft**：生成engine_version=3.0.0的batch。至少区分hook/suspense、正文与calling（最少4个功能段）；正文可多段，按所选入口组织：商业案例讲关键选择，图鉴/选型交足分类与判据，调查讲范围与启发，风格/工艺给可见语言与原创演示，人物及时揭示身份及合作节点。本篇给核心答案。Calling一个主动作、参与理由与实际后续；自然交流可成立，不统一强制产品/国家。评论可结尾复用、置顶、备选或本篇禁用，不把评论与私信并行强推。cover_main/sub独立；全部段落含台词、具体画面、素材、景别机位、动作、字幕、切点、声音、留时。首3/8秒是编辑目标；估读不写实测，锁定标签超时如实注明。composition逐节点绑定实际台词。运行`draft --run RUN --input batch.json`。
4. **Independent review**：用`prepare_review.py --run RUN --batch RUN/batch-v1.json --output content-input.json`先给实际八项、原请求/原件/素材状态；不让plan、作者利益翻译或分数代答。逐项引用实际内容给content_decisions与delivery_checks，允许REWRITE。内容成立后才用`--phase fidelity --content-review content-review.json`核原式、基因、来源及composition_checks。数值分可选，只诊断，不认证吸引力；硬门禁、内容兑现和实际八项失败先返修。最多同RUN初稿加两次返修；封存后改主副/前两句/首镜visual或核心事实/机制/目标须新RUN、新首屏审和新plan。
5. **Validate & export**：运行`validate --run RUN --input RUN/batch-v1.json --review review.json --output validation.json`，通过后export。按[表格合同](references/task-contract.md)从同一segments源生成分段稿、连续全文和执行卡：逐字、顺序、ID一致。新封面定稿覆盖同ID旧表D/E；15封面与18口播不混数，未列3条不补回封面选集。原样参考不静默纠错，成品不复制其矛盾：XHS I/Q、假约稿、未证上市、TOP5缺项、身份反转与工艺事实须具体处理。导出后回读所有子表、全文和台词；实际预览未做就不称视觉验收。用户要求TXT先完整TXT，不强行生成全表。

## 行业与交付边界

插画任务按[领域适配](references/illustration-value.md)与样例逐字段冲突注释判断。最新6源完整原件与1229格去向在`standards/20261118/`；原文锁定、表达示范、事实已核、真人时长、发布表现是不同状态。其他行业不能自动出现笔刷、海外母婴、角色/SKU；把共同任务、价值、证据和行动换成本行业内容。

平台主要改变实际展示位置/裁切、熟悉程度、证据出场与节奏；三平台都可有强点击与专业价值，不规定抖音必须冲突、视频号只能B端、小红书只写搜索词。官方规则须当次核验；不编权重或词式保证。

程序检查字段、来源、锁定、字数、承诺项数、台词/执行卡一致和版本；不能判真观看意愿、私下阅读顺序或审稿身份。独立模型、真人试读、同行、目标观众和后台数据分别记；未做NOT_RUN。只在有同口径分母时算点击率，不以播放量冒充封面点击效果。用户授权内保存，不自动发布、不对外发消息。
