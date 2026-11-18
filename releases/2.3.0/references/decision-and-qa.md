# 独立编辑复审 v2.3

唯一六项量规rubrics/quality.json：黄金三秒15、3–8秒悬念15、正文专业25、高级审美15、利他15、Calling15；每维0–4、单项不足须修；取消总分达标阈值，不围绕80分调优文案。不能使用旧八项评分或样稿旧总分。

内容阶段只接收实际八项交付、原始请求/原件和量规；先记录内容判断。源式阶段才接brief、decision、asset-pack与batch；始终不看生产者评分。逐维写segment_id、quote、score、reason。hook_strength只引用hook；suspense只引用suspense；professional_judgment引用judgment；aesthetic_expression与buyer_value引用judgment/value；cta_persuasion引用calling。引用相同句子不等于同一判断，应分别解释。

- 先找反证：原件是否真支持客户、时间、数量、事件、结果？历史案例及样例不是本次事实。
- 封面/首句/首镜指同一问题吗？第二句新增什么？首个判断是否兑现？3秒和8秒估算可读吗？
- 专业判断是否包含选择、理由、证据、边界？工具/步骤/颜色清单最多2分。
- 审美是具体取舍与信息秩序，不是华丽词；非视觉行业同样检查层级、克制、统一、节奏。
- 利他价值须在台词中可复述、可迁移；制作备注不能补正文。Calling须符合目的，咨询稿不能只有投票。
- 同平台任两稿在子问题、利益、证据组织至少两项不同；跨平台检查推理/证据出场差异。不能仅比较字符串。先核同一事件、受众和业务目标是否保留，再看首镜、证据顺序和节奏的实际适配；不为制造不同收获而擅自换受众或改成技法教程。
- asset_checks核验机制真的参与创作；ID存在与哈希一致只证明引用。commercial_checks检查价值兑现和行动承接。
- 七项P0门禁facts/promise_payoff/proof/platform/marketing/human_voice/direction逐项带原句和理由；issues只列阻断问题，非阻断提醒写notes。

复审绑定版本稿、方案、资产包SHA256。修改后新版本重审，最多两轮返修；不为导出倒推分数。结构测试合成review只作程序测试，不能报为独立质量评审。无独立环境则待审，不能编身份。

## 外部验证
匿名目标用户复述任务、判据和行动；同行核专业正确性；新手试拍记录额外解释/缺素材/重拍；真实后台对照记录窗口、样本、分母、基线。未做NOT_RUN。总分不能认证平台效果或从业年限。正式发布就绪还需真人试读证据、当次平台核验与现有关键素材；编辑合格可先交付。

按[source-to-speech](source-to-speech.md)完成composition_checks。原式缺节点、观众问题未答、备注补台词、同正文换商业前后缀、关键词替代观众行动，均先否决；结构分或总分不能抵消。原式变量/逐节点锚点及近重复检查由程序核对，语义适配和吸引理由仍由独立编辑判断。

校准反例：开头“客户为何选我？”、承接“关键在交付哪一步？”，正文却只有“空白格先标待确认，再按来源核对”，即使锚点齐全，也没有说明客户选择的依据。应拒绝promise_payoff与audience_payoff；不能由评审者自行想象“这代表专业，所以客户会选”。原句相互存在不等于原问题被回答。

插画终审另读illustration-value.md与返回的当前1118规范原文、delivery-standard及冲突处理，逐稿完成information_checks。本人项目是provided可以直接叙述；未核原始记录不代表必须编成假设，也不代表已验证收款。只讲写作品说明/笔刷分工而没有当前承诺的市场、商品或渠道信息，应按用户业务目标而非孤立技法价值判定。

prepare_review先复查本版provenance；拒收稿即使留在RUN也不能交给审稿者。文件存在不表示本次draft命令成功；宿主必须检查返回码。

## 1118首屏优先
先按delivery-standard.md审真实首屏，再审完整八项交付。content阶段不得读生产者方案/评分/利益解释；记录content_decisions（DRAFT_FOR_USER_REVIEW或REWRITE）和八项delivery_checks后，才运行fidelity阶段读原式对照。每条delivery_checks绑定surface_contract.delivery_packet的canonical SHA并引用实际表面文字。值得看的判断失败，不能在后续用ID或高分翻盘。跨平台核对保留同一受众/事实/业务目的，再看首镜、证据节奏与口语适配，不为差异化改题。
