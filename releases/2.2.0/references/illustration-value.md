# 插画：先交付观众值得看的信息

本分支依据用户V0.2业务规范；只在插画/印花/设计服务任务加载。沿用五阶段，不额外建设独立Skill。具体标准原文随asset-pack.must_read_guidance返回，不能只读本摘要。

1. 先选唯一首要受众：同行、初学者、品牌/工厂、外贸商。记录他当前的业务问题、首句可得的直接利益、来源类型，再选事件/题材。作品与DIY笔刷是解决任务的依据，默认不从技术目录生成选题。
2. 首句优先交代实际客户买什么、可核市场信息或业务阻碍；3–8秒必须给新的国家/品牌/商品/brief/渠道/结果。反转与向往不能挤掉直接利益。数字本身不等于利益，过程好奇不等于业务痛点。
3. 本人项目(user_project)、官网商品(official_product)、原始研究(research)、本人原稿(original_work)、历史样例(historical_example)、假设(hypothetical)分别使用。用户明确陈述的本人项目可直接以本人叙事写，状态provided；不一律降为假设，也不说成已核实付款。历史样例不借身份、收益和日期；用户本轮资料明确更正的事实优先。
4. 正文讲这件事里的需求、关键选择和依据，再交一个能用的决定。具体采购方向/产品用途/询盘渠道/原创应用条件必须在台词里；不能靠备注把绘画步骤包装成接单价值。未提供的Brief、客户选择原因、逐日冲突和销量不补写。
5. Calling承接已经给出的信息：目标国家+品类、产品+市场或一项真实设计问题。说明交流范围，不默认关键词，不承诺必定接单、免费无限审稿或站外入口。

## 当前输入/方案/稿件/复审交接

brief.audience_information = {primary_role,current_problem,direct_benefit,information_type,source_class}。角色为designer/beginner/brand_factory/trader；信息类别与来源类别见profile。facts逐项写evidence_class，可给anchor_terms用来核对第二句出现的真实字段。显式技术教程才设explicit_technical_tutorial=true；还需可见测试素材，不能用“会调工具”冒充实测。

用户明确选用项目时，brief.case_ids列对应项目ID；本轮本人美国浴巾案例为ILL:PROJECT:US-BABY-TOWEL-300，默认不注入新任务事实。这个库只有用户陈述，不认证客户身份或付款；官网和趋势示例只是写作参照，需要另读一手来源。

selected.information_contract = {primary_role,opening_benefit,new_fact,viewer_use,information_type,source_class,tool_position}。tool_position为support或explicit_tutorial。source_recipe.opening_reference固定对应domain开头参照的asset_id/record_sha256/source_quote/adaptation；源类型要相容。完整正文仍选已读公式与完整样稿，说明迁移边界。

script.information_delivery = {primary_role,source_class,tool_position,opening_benefit,new_fact,viewer_use,opening_fact_ids,new_fact_ids}。三个内容字段均为segment_id/quote；opening_benefit必须是首段台词，new_fact必须是第二段，viewer_use必须在Calling前正文。new_fact_ids中至少一项未在开头使用；有anchor_terms时须在第二句原文出现。这只校对字段，真实新信息和是否有用由独立编辑判断。

review.information_checks逐稿包含opening_value/new_fact/story_decision/viewer_use/calling_input，每项passed/segment_id/quote/reason，引用相应实际台词。先按V0.2反例否决，再评分；没有新信息、只念流程或把商业价值放在备注里，不得为交付提高分数。

## 拒绝不适配资产

原始标题库中的AI标题不等于插画市场样板。候选不适配时，source_recipe.title可以status=no_fit，列checked_title_ids和reason；转用本领域开头参照与口播机制。adapted只说明保留了标题机制，不称精确业务匹配。五类开头参照只覆盖开头和价值方向，不伪装为已验证爆款或完整真实客户故事。

原始核验、真人试读、目标受众盲读和发布数据分别记录；本轮模型复审不能代替这些。按用户要求可交TXT审阅稿；run_pipeline.export仍只原生导出XLSX，TXT由宿主在同一校验版本上逐字投影，不能假报原生TXT导出。

若资料只有项目流程而缺少承诺所需的具体需求、关键选择或可见成稿，不拿抽象“专业能力”补空。先收小承诺；若当前主题与用户文档允许，可转向文档已有的官方品牌/商品研究样例，实际读取一手页面和商品，另建RUN，明确换来源，不把官方商品当作本人客户。换事件或证据需新RUN。
独立复审使用prepare_review.py输出的去评分视图；原decision含生产评分，不直接整份喂给盲评者。两者的原始SHA仍绑定，投影视图不伪称原文件字节相同。
