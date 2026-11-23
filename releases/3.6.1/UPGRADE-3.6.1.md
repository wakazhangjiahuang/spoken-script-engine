# spoken-script-engine v3.6.1｜四层执行与证据闭环修复

本版在v3.6.0上进行定点升级，不重建原有业务链路，不移除AI视频V4.1、插画V2.0、双标杆、三平台知识库、样例、工作簿或历史兼容。

## 本次新增

1. **理解层：原始证据可追溯。** 原始文件、source-manifest、SHA256、精确原文位置、事实ID、口播主张和引用建立机器可核验关系；非文本材料要求提取证据。
2. **决策层：三个以上真实差异入口。** 强制比较用户需求、点击理由、承诺收益、证据、交付、商业价值、风险和反证；所有未选方案必须记录否决理由。
3. **生成层：15项标准映射成品。** 封面、0–3秒、3–8秒、正文模式、承诺兑现、能力放大、痒点升维、Calling、证据及平台表达均绑定实际台词。
4. **验证层：独立凭证与外部证据。** 评审者/生成者身份和会话、盲审包、评审证据、批次/决策/来源哈希绑定；真人试读、逐稿用户盲读、权利授权、平台数据与效果回流分开验收。
5. **非补偿门禁。** 每篇15项逐条验收；任一失败即BLOCKED；外部验证未完成保持VALIDATION_PENDING；平均分不能放行。
6. **唯一新入口。** `scripts/run_pipeline_v3_6_1.py` 在保留v3.6.0及领域正式验证器的基础上，增加intake/plan/draft/validate/export阶段门禁。

## 兼容与边界

- 保留v3.5.0内容兑现、六篇负向回归；v3.5.1 AI视频V4.1正式审查；v3.6.0来源优先、内容模式和双标杆治理。
- 插画V2.0的18篇稿件、锁定字段、六表工作簿和AI执行卡仍由原领域验证器验收。
- AI视频与插画的样例、事实、评分和专用工作流继续隔离。
- 单元测试、代码门禁和CI成功不代表市场效果。未实际完成的真人试读、用户盲读、授权和发布数据必须保持待验证。

## 正式入口

```bash
python scripts/run_pipeline_v3_6_1.py intake --run RUN --request request.txt --source attachment.docx
python scripts/run_pipeline_v3_6_1.py plan --run RUN --input decision.json
python scripts/run_pipeline_v3_6_1.py draft --run RUN --input batch.json
python scripts/run_pipeline_v3_6_1.py validate --run RUN --input batch-v1.json --review review.json --v41-review v41-review.json
python scripts/run_pipeline_v3_6_1.py export --run RUN --input batch-v1.json --review review.json --v41-review v41-review.json --output deliverable.xlsx
```

AI视频继续提供`--v41-review`；通用/插画评审仍按领域原路径保存。评审文件需额外包含`reviewer_attestation`、`delivery_acceptance`和`external_validation`。未完成外部验证的稿件可导出审稿版，但状态不得高于`VALIDATION_PENDING`。
