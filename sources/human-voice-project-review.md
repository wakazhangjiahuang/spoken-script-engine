# 去 AI 味与口播自然表达｜GitHub 项目研究记录

核验日期：2026-11-04。以下固定到本次读取的 commit 与文件 blob，避免后续 main 更新改变研究依据。

## 1. MrGeDiao/shuorenhua
- Repository: https://github.com/MrGeDiao/shuorenhua
- Main commit: 0a001940bf1fc70f29f29a46c3587749d5badb45
- SKILL.md blob: 0dec98237e38c1b41b24704ca8e88ab94a2043d4
- references/editing-guide.md blob: 53c631390cb91f0f1b9aa284221fd6d75038a468
- references/examples.md blob: 447033c4f11cb8a3b619da51df6bbb7e7effd093
- License: MIT（仓库 LICENSE，Copyright 2026 MrGeDiao）

### 吸收的设计原则
- 先理解原文，再做最小必要修改；正常表达可以不改。
- 保护事实、数字、条件、否定、情态、责任主体、作者判断和原有语气。
- 词语命中不等于错误；术语、引语、作者有意表达必须按语境判断。
- 区分内容准确性与语言风格；不把“缺来源”擅自改成事实，也不替作者补证据。
- 只在确有编辑收益时修改，不为满足某个“激进程度”强行改词。

### 不直接移植
不复制其 SKILL、编辑边界、示例或评测原文；本仓库只记录上述方法摘要并独立编写口播规则。

## 2. liuhaisi2026212-maker/taishang-laojun
- Repository: https://github.com/liuhaisi2026212-maker/taishang-laojun
- Main commit: 8386b618836ed4ecd0cd90d726141d1c7807f018（README标注版本0.7.2）
- deai-rulebook.md blob: 2a879c0c9b66f56c0d3e08b44da7ea1eb53b03ba
- ai_tell_linter.py blob: 3f8f8243913932e5ed4bb10b365139e080e856f2
- edit-six-cuts.md blob: 5f02c4629b6860f2361af5e6d59a9101d1250ab4
- License: CC BY-NC 4.0（仓库根目录 LICENSE）；其 THIRD-PARTY-NOTICES 另列 Humanizer、Humanizer-zh 等 MIT 上游来源。

### 吸收的设计原则
- “念出来”检查：是否像这个人对目标对象自然说出的话。
- “盖住原稿再说”检查：从真实事件、说话动机、听众、可展示材料和观众疑问重新组织，而不是替换几个同义词。
- 把语言质感检查与留人结构检查分开；两者可以衔接，但不能混成一个万能改稿动作。
- 识别假对比、伪深度路标、旁白腔、硬凑三点、假口语、无源权威和虚构第一人称。
- 先冻结事实，再检查具体性、创作者口吻和朗读顺畅度。
- 机械 lint 只能提供软提醒/硬提示；命中不等于必须删，未命中也不代表没有问题。

### 许可边界
该项目本体为 CC BY-NC 4.0。为避免商业用途和衍生分发产生许可风险，本仓库不复制其规则文本、代码、句式示例、案例或个人素材；只保留研究链接、版本定位和高层方法摘要。此说明不是法律意见。

## 3. Ethantrump/director-perspective-script-workflow
- Repository: https://github.com/Ethantrump/director-perspective-script-workflow
- Main commit: d0811a74475714cd68073dcc27c50b8bb1ad2ccf
- SKILL.md blob: c59a4c514aeb91c0c4e833780289cd2177e50dfc
- references/ai-free-writing.md blob: 67c80fd0911b5baaade37f73ea0988efcbfcd4e3
- references/director-deck.md blob: d83d74ae2534844ce5e990f0714a2f5b3cc75f57
- License: MIT（仓库 LICENSE）；其 NOTICE 说明 ai-free-writing 的部分概念来自 avoid-ai-writing（MIT）。

### 吸收的设计原则
- 写稿前先做导演决策：结构、开场、重点段、画面和收尾。
- 结构与句式需要变化，防止同一账号连续稿件出现同样开场和收尾。
- 交付前执行 Detect → Rewrite → Review。
- 把可信度错误、明显模板表达和节奏润色分层处理。
- 真实演示、真实数据、真实第一人称是硬约束；不因“更像人”而添加虚构细节。

### 不直接移植
不复制其脚本、段落示例、句式变体库或固定时长/字数阈值。具体时长必须按用户要求、口播速度和信息复杂度决定。

## 综合结论
三个项目的能力互补，但不可直接合并为一个词表：
- shuorenhua：保真与最小编辑边界；
- taishang-laojun：口播朗读测试、盖稿复述、假对比和真人声音；
- director-perspective：先做导演决策、结构变体、交付前检测与防重复。

本 Skill 的独立实现是：事实冻结 → 创作者声音识别 → 导演决策 → 初稿 → 念稿/盖稿复述 → 语境化模式检查 → 事实回查。未导入上述项目的代码、完整规则或示例。
