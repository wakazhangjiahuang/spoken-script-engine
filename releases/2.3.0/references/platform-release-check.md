# 平台、营销与发布状态

规则核验与内容策略分开。不得把完播、点赞、搜索等单项当作平台的唯一排名公式，不提供未经官方公开的权重、阈值、流量池周期。运营观察、模型推断与账号实测分别注明。检索中小程序/直播/广告投放规则只作用于对应范围，不能扩成全平台禁令。

每次任务为所选平台记录 `review.platform_checks[]`：platform、status(VERIFIED/PARTIAL)、source_urls、checked_at(YYYY-MM-DD)、scope、restrictions、publish_ready。VERIFIED仅指与本稿相关条文已核验，不指官方审核批准。没有读到官方原文就 PARTIAL；不能凭搜索日期宣称生效日期。交易/广告/站外导流、行业资质、生成合成内容标识和账号功能需单独核验，未确认不写成可用渠道。生成脚本不自动触发AI音视频标识判断，实际使用合成音画时按当次规则核验。

截至2026-11-04的可用入口：

| 平台 | 官方来源与范围 | 本次证据边界 |
|---|---|---|
| 抖音 | 社区自律公约：https://sf3-cdn-tos.douyinstatic.com/obj/ies-hotsoon-draft/douyin_agreement/b94d5a1e-c676-4e99-92b5-2d5e26d2568b.html?enter_from=user_agreement ；算法透明：https://trust.douyin.com/transparency | 已读取公约和官方算法说明入口；不采用固定流量权重。 |
| 小红书 | https://school.xiaohongshu.com/rule/detail/10127 （商家/买手带货）；https://school.xiaohongshu.com/rule/detail/2581 （交易笔记）；https://ad.xiaohongshu.com/next_help/docs/69c1a398db68750fe77e40c026386649 （专业号/KOS） | 搜索获得官方索引正文，直读页面无可读文本；标 PARTIAL，不冒称核验全部普通用户规则。关注题文一致、真实体验与身份、虚假营销。 |
| 微信视频号 | https://weixin.qq.com/cgi-bin/readtemplate?t=weixin_agreement&s=video ；营销规则线索：https://support.weixin.qq.com/cgi-bin/mmsupportacctnodeweb-bin/pages/pf0txLmOJiPSy87m | 官方运营规范本轮未能打开，PARTIAL；二手转载只作核验线索，不替代官方全文。 |

这些入口不是永久白名单，每次仅重查会影响本稿的动态条文。联网失败保留上次日期/范围，使用保守内容方案，不拦住无需交易功能的知识稿；文件标「已完成独立编辑复审；发布规则/账号条件待核验」。

## 发布与表达四项门（另加事实、兑现、证据三项，合计七项）

- platform：无伪造算法事实；标题、封面、台词、字幕、画面、Calling语义一致；本稿适用规范及缺口记录清楚。
- marketing：受众→任务阻力→具体价值→证明→阶段行动可追溯；不过度承诺，不强行成交；资料领取必须真实存在，评论不是获取核心答案的交换条件。
- human_voice：原意和完成状态不变；有当前讲者声音；读起来顺；抽象空话、假对比、假亲历和AI助手残留已处理。词表和检测器分数不代替语境判断。
- direction：首镜与承诺一致、逐段画面能拍、资源与时间足够、连续性与剪辑有理由、缺素材有替代。

逐稿每项给 passed、segment_id、quote、reason，引用真实台词并解释判断；不得用「符合平台规则」「具有导演感」作为空评语。review 也要检查封面、发布文案、字幕和拍摄指令，不能只审台词。任一项未通过返修；发布状态单独为 READY_FOR_USER_REVIEW 或 NEEDS_READ_MATERIAL_OR_PLATFORM_CHECK，两者均不代表已发布或效果验证。


v2.0当次核验记录在assets/kb-snapshot/rules/current-verification.jsonl。正文来源与账号发布权限分开，不因来源域名正确就判通过。无实读证据、关键素材待拍、规则PARTIAL任一存在都不能标发布就绪。
