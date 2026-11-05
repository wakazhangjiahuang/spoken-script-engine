# 独立编辑复审 v2.0

唯一六项量规rubrics/quality.json：黄金三秒15、3–8秒悬念15、正文专业25、高级审美15、利他15、Calling15；每维0–4、至少3，加权至少80。不能使用旧八项评分或样稿旧总分。

只接收原始请求/原件、brief、decision、asset-pack、batch与量规；不看生产者评分。逐维写segment_id、quote、score、reason。hook_strength只引用hook；suspense只引用suspense；professional_judgment引用judgment；aesthetic_expression与buyer_value引用judgment/value；cta_persuasion引用calling。引用相同句子不等于同一判断，应分别解释。

- 先找反证：原件是否真支持客户、时间、数量、事件、结果？历史案例及样例不是本次事实。
- 封面/首句/首镜指同一问题吗？第二句新增什么？首个判断是否兑现？3秒和8秒估算可读吗？
- 专业判断是否包含选择、理由、证据、边界？工具/步骤/颜色清单最多2分。
- 审美是具体取舍与信息秩序，不是华丽词；非视觉行业同样检查层级、克制、统一、节奏。
- 利他价值须在台词中可复述、可迁移；制作备注不能补正文。Calling须符合目的，咨询稿不能只有投票。
- 同平台任两稿在子问题、利益、证据组织至少两项不同；跨平台检查推理/证据出场差异。不能仅比较字符串。
- asset_checks核验机制真的参与创作；ID存在与哈希一致只证明引用。commercial_checks检查价值兑现和行动承接。
- 七项P0门禁facts/promise_payoff/proof/platform/marketing/human_voice/direction逐项带原句和理由；issues只列阻断问题，非阻断提醒写notes。

复审绑定版本稿、方案、资产包SHA256。修改后新版本重审，最多两轮返修；不为导出倒推分数。结构测试合成review只作程序测试，不能报为独立质量评审。无独立环境则待审，不能编身份。

## 外部验证
匿名目标用户复述任务、判据和行动；同行核专业正确性；新手试拍记录额外解释/缺素材/重拍；真实后台对照记录窗口、样本、分母、基线。未做NOT_RUN。总分不能认证平台效果或从业年限。正式发布就绪还需真人试读证据、当次平台核验与现有关键素材；编辑合格可先交付。
