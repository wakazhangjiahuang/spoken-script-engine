# 选题确认门禁｜Topic Gate 1.0

每个候选明确目标受众、受众当前处境/问题、“关我什么事”、利他回报、故事推进、证据基础、Calling理由、平台表达差异和与其他候选的实质差异。不同候选不能换标题凑数。

内部做结构化反方审查：创作者主张、受众反问、证据复核、修订/淘汰决定。不得输出隐藏思维链，只向用户展示结论、证据状态、风险和修订结果。关键维度失败或缺证的事实主张不得放行。

用户确认前只交付《选题确认板》，不生成完整稿件或XLSX。用户明确锁定主题时标记USER_LOCKED，但仍需审查。确认后将用户原话写入decision.json.topic_gate.confirmation_text，每篇selected绑定已批准topic_candidate_id。topic_gate_contract.py阻止未确认任务进入Draft。