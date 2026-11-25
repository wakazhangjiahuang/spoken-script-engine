# A 选题与 B 成稿

A 的输入以本轮用户给的启动 Prompt、原始资料和授权范围为准。B 扩写已选主题。04 和 05 是 B 的制作方式。

## A 的选题判断

读运行目录中的来源清单和必读指南。按需找与受众任务相符的认可例。标杆维持当前引用治理。原件支持的事实、用户陈述、专业判断和授权模拟要分别表述。趋势报告可以帮助提出开发方向。若要陈述购买动机或销售结果，使用能直接支撑该主张的材料。

按用户要求生成候选。写出实际标题、承接和正文兑现示范再择优。候选有吸引力也要检查是否绝对合格。多篇有不同的客户决定和答案即可，允许重复素材及授权锁定的系列开场。标杆用于校准细节、利益和节奏。审查标题、前八秒和正文是否沿着同一个观看理由推进。证据和取舍决定内容。已有量规按阶段适用，人工仍可判为返修或淘汰。

A 可展示完整提案预览。正文要有供观看者判断的一处具体演示或取舍。外显字段遵守用户范围，比较和修改过程留在内部。程序检查领域、数量、证据 ID 和锁定文本，语义差异及表达质量由编辑复核。独立评审与营销验证按实际状态记录。

## 运行与数据

以下 `ENGINE` 代表 `<skill>/scripts/run_pipeline_v3_6_1.py`。原始 Brief 与附件先用既有 intake 契约保存，调用 `intake --mode A --run RUN_A --input brief.json --request request.txt`，并按需要重复 `--source 原件`。

若有本轮锁定，在 A intake 加 `--locks locks.json`。该 JSON 以选题编号为键，值为下述锁定字段表，在生成前封存，提案缺失或修改既定锁定会退回。

将实际提案写入 JSON 的 `topics` 数组。每条包含：

- `id`，稳定的选题编号。
- `platform`，与 brief 平台枚举相同。提案数量按该平台约定。
- `audience`、`buyer_decision`、`payoff`、`next_step`，即主受众、客户决定、核心回报、下一步。
- `evidence_refs`，intake 中实际可用的事实、资源或来源 ID。人工核查哪些引用支持哪个判断。
- `copy`，键为 `cover_main`、`cover_sub`、`hook`、`suspense`、`body`、`calling`、`comment`，值为该篇可审阅的实际文字。标题和实际口播不能用“后续补充”代填。
- `locks`，仅记录当前明确已锁定的字段。键与 copy 对应，值为 `{"scope":"exact","text":"原文"}` 或 `{"scope":"prefix","text":"锁定前缀"}`。可替换变量按授权完成替换，再锁定实际应保留的部分。若原文事实或时长有疑问，标记并给出可审选项，调整须以本轮授权为准。现有 brief 的全句锁定仍适用。

```bash
python3 ENGINE proposal --run RUN_A --input proposal.json --output proposal.md
python3 ENGINE select --run RUN_A --topic 02 --authorization '用户确认第 02 篇的原话' --output handoff.json
python3 ENGINE intake --mode B --handoff handoff.json --run RUN_B --input brief-b.json --request request.txt
```

用 `--topic` 明确记录每个所选编号。用户已授权直接成稿时引用原请求中的相应指令。提案修订开新 A 运行，选用对应版本的交接。B 使用同一原请求及附件字节，按所选单调整 brief 平台与篇数。保留 A 的受众、目标、主题、事实、来源清单和内容任务。B 的 `plan` 用所选编号并逐字沿用 `platform`、`buyer_decision`、`payoff`、`next_step`，每篇用 `topic_competitions` 记录自己的选择。旧的批次级记录可用于既有正式运行。B 的 `draft`、`validate`、`export` 继续走正式入口。当前脚本校验所选 ID、受众与锁定文字，完整发布证据仍按领域验收。新 B 插画任务的 XLSX 使用通用脚本表与拍摄表，按所选篇数生成。18 篇历史工作簿继续使用原六表路径。请求 H3 时，照既有执行卡契约与实际台词另交对应卡片。

## 回归判例

同一受众三条稿可分别回答选哪个试样方向、套系下一件补什么、委托前该确认什么。若三篇核心答案都是“看趋势后分主图和配花”，交回策划。若一个角色同时服务三条不同选择，可以共用。锁定首句相同的三篇先看各自承接和专业兑现。最终证据由原件、非作者编辑、目标读者或真实发布记录提供。程序结果只覆盖可观察的结构与一致性。
