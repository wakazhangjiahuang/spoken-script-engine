---
name: spoken-script-engine
description: 面向小红书、抖音、微信视频号的口播策划、专业决策蒸馏、AI视频与插画内容生产和逐稿验收引擎。
---

# 口播稿引擎 v3.5.1

本版是v3.5.0的定点修复，不重建受众、核心需求、选题库或领域指导书。继续沿用AI视频V4.1、2026-11-23团队制作手册、插画V2.0、Title Guide V4和已确认样例；修复AI视频正式独立审查未接入唯一执行入口的问题。

## 1. 既有资料与受众规则
- AI视频读取V4.1业务指导书、2026-11-23团队制作手册、当前工作簿结构样例及样例治理资产。A/B/C只是业务路由，不是选题。
- 插画读取V2.0指导书、Title Guide V4、原始锁定工作簿及manifest。旧版V1.0/V3.0/旧快照不作为当前正向标准；V4.0只作结构参照；BENCHMARK只拆机制。
- 直接复用现有受众和核心需求，不重新泛化画像。每条计划绑定原文source_asset_id、source_locator、source_quote。

## 2. 内容策划与点击兑现
每条计划形成content_contract：目标受众、共同任务、必要时的共同任务理由、why-now、点击理由、观看回报、证据计划、专业判断标准、可迁移价值、下一层价值，以及至少三个机制不同的营销入口。保留选中入口、否决理由、反方意见和反证。
封面主副标题共同构成点击理由，不写作者工作总结或功能清单。0–3秒负责停留，3–8秒必须增加新信息或推进故事；正文先兑现封面承诺，再用材料、判断、具体示例和证据完成价值。三平台分别建立入口、证据组织、节奏和行动理由，不是一稿三发换语气。

## 3. 正文专业演示：worked example
每篇用一个具体真实或明确模拟的案例，展示具体输入、判断标准、至少两个方案及代价、处理前状态、选择后的处理、处理后状态、可观察变化和可迁移规则。
professional_decision.worked_example至少包含input_snapshot、decision_criterion、before_state、after_state、observable_delta、transfer_rule，并用spoken_anchor、result_anchor、transfer_anchor逐字绑定正文。只在备注/JSON里写专业判断、正文仍是常识清单，不合格。模拟案例必须在口播中披露。
AI剪辑展示真实片段如何保留/删除/重组；AI文档转视频演示一个岗位任务和异常/验收点；数字人给出具体栏目Go/No-Go依据；插画围绕SKU/Brief/作品展示实际设计取舍和买方判断标准。

## 4. Calling价值交换
每篇calling_value_exchange必须包含一个action、reason、reward和实际口播锚点。用户奖励必须是具体可获得的下一步价值；单纯关注、点赞、评论、收藏或私信不能作为奖励。

## 5. 非补偿性评分
继续沿用AI视频V4.1和插画V2.0原权重：核心营销/专业价值维度最低4/5，其余维度最低3/5；70分为最低编辑线、80分为内部目标。硬门禁失败不得用总分补偿。评分不预测流量、点击、收藏、转化或收入。

## 6. v3.5.1正式审查修复
AI视频validate/export必须调用validate_v41.validate(batch, review)，不能只调用轻量validate_ai_video_review()。review必须绑定当前batch的精确文件SHA或规范化payload SHA。至少一名独立评审者须通过身份/模型区分；fast_screen、deep_review、critic路由未完成时不得编辑放行。
--require-v41-full-validation必须真实生效，只有V4.1正式状态PASS才通过；真人试读、3–5名目标用户盲读未完成时保留VALIDATION_PENDING。插画仍使用V2.0独立reviewer、证据文件、评分与六表工作簿验证。

## 7. 唯一执行入口与回归
所有阶段只用scripts/run_pipeline_v3_5.py：intake → plan → draft → validate → export。它保留v3.5.0的来源绑定、内容契约、worked example、Calling、负向六稿回归和领域隔离，并在AI视频validate/export接入V4.1正式验证器。
每轮运行test_content_quality_v350.py和test_formal_v41_gate_v351.py。旧六篇30分稿固定为NEGATIVE，不得作为正向few-shot。未执行的真人试读、盲读、授权和发布验证必须标记NOT_RUN/VALIDATION_PENDING。
Jev/Laya是决策角色，不代表已调用外部模型；只记录候选、反对意见、证据、裁决和修复，不输出隐藏思维链。
