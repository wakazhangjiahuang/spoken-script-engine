# v2.1 完整链路与逐环节验收

依据：sources/approved/manual-v2.html 与 examples-v4.xlsx；前者是通用方法，后者只作编辑样例。当前用户要求优先；原始业务资料高于历史稿件。机器只能检查合同与引用，语义质量仍由独立编辑判断。

|环节|选择与判断|评分/硬约束|产物与失败出口|
|---|---|---|---|
|需求解析|识别受众任务、决策阻力、目的、时长、篇数、口吻|brief schema；原始请求必留；事实来源逐条可读|brief＋source-manifest；冲突写input_resolution，缺事实收小主张|
|事实锁定|P0原件、P1官方、P2方法、P3整理分开|事实无来源/把历史样稿当当次客户经历直接否决|facts＋production_resources；示例显式标注|
|检索|内容任务×目标×证据先筛；关键词只在合格候选内排序|文件/记录哈希一致；关键角色hook/body/calling/platform齐全|asset-pack＋检索分数与排除理由；无案例实报0|
|选题/方案|高相关高证据优先；高相关低证据收小主张；双低弃选|rubrics/selection.json四维0–4，每项≥3，总分≥80；每平台至少一个弃选也评分|decision先封存；不为凑数提高分数|
|标题/开场|标题公式→心理机制→自然口播→首镜；比较另一机制|hook首段≤3秒；suspense第二段累计≤8秒；估速可读；两段各自独立评分|title/cover/hook_plan；开场不兑现退回|
|正文|按任务选择公式；每段推进一个判断；条件和取舍具体|professional_judgment 25%；aesthetic_expression 15%；buyer_value 15%|context/judgment/value台词＋claim_links；备注不能补台词价值|
|Calling|目标决定动作，渠道另核验|cta_persuasion 15%；单一主动作；inquiry须有任务输入和下一步|calling；泛投票不得冒充咨询|
|导演|首镜先确定，关键结论对齐证明；无素材给真实替代|每段角色、台词、动作、字幕、素材、剪辑、静默留时齐全；unavailable阻断|director_plan＋segments；planned标待拍|
|独立复审|原始请求/原件/封存方案/稿件/量规，不给生产评分|六项每项≥3且加权≥80；七项硬门禁均通过；样稿旧评分无效|review绑定稿件、方案、资产包；最多两次定向返修，新稿新审|
|导出|总览＋所选平台各一表＋拍摄执行卡|动态篇数；跨表ID/台词/顺序/连续稿逐字回读；不输出内部JSON|XLSX；失败只报待修，不用模板空表替代成稿|
|发布就绪|按当次账号、内容属性和官方原文检查|PARTIAL≠已核实；真人试读MEASURED且证据记录；待拍未完成则非READY|总览列出具体阻碍；不自动发布|
|测试/回流|目标用户盲测、同行评审、新手试拍、后台单变量测试|样本/窗口/分母/基线齐全才解释结果；未经验证NOT_RUN|反馈按品牌隔离、去重；明确采纳和证据才晋级|

## 六项主评分与事实门禁分开
黄金三秒15、3–8秒悬念15、正文专业25、高级审美15、利他15、Calling15。总分=sum(0–4原始分×权重/4)。0缺失，1空泛，2有缺口，3可执行，4准确取舍＋清楚边界＋有记忆点。任何项2分不能被其他高分抵消。
高级审美不是华丽形容词：插画看主次、线条、留白；AI系统看输入输出、异常与人机边界；电商看使用条件与参数优先级；知识服务看概念层级、例子和表达节奏。
七项硬门禁为facts/promise_payoff/proof/platform/marketing/human_voice/direction；事实与证据不再作为可以用其他分数抵消的维度。

## 方案评分写法
selected每项增加selection_scores：四项各为{score:0..4,reason:具体材料或条件}。rejected同样有platform、reason和selection_scores；可高分弃选，但解释资源、重复或相对优势。评分是编辑判断，不叫算法分或检索准确率。
优先遵守明确formula_lock；证据条件不满足时说明冲突并改成清晰示例/待证，不擅自换锁定公式。N篇不等于N个客户：同一案例可以有N个判断入口，不能编造客户数量。

当前新增交接按source-to-speech.md执行。检索不得以同领域替代同受众/同问题匹配；方案封存source_recipe与audience_contract，稿件逐变量/正文节点引用原句，独立review附composition_checks。允许同公式服务不同实质问题；“N个判断入口”不能用同正文换开头充数。
