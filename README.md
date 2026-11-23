# 口播稿引擎 3.5.1

**当前私有插件包：3.5.1｜更新日期：2026-11-23**

3.5.1保留v3.5.0的受众与需求复用、三入口内容契约、worked example、前8秒推进、Calling价值交换、六篇负向回归和非补偿评分；定点修复AI视频正式V4.1独立审查未接入唯一执行入口的问题。

## 发布结构
- 基础包：releases/3.1.1/
- 历史补丁：releases/3.1.3/
- V4.1决策与QA覆盖层：releases/3.2.0/
- AI视频样例与检索治理覆盖层：releases/3.2.1/
- 当前运行质量与插画V2.0覆盖层：releases/3.3.0/
- 内容决策与来源引用初版：releases/3.4.0/
- 当前源资料绑定与质量门禁：releases/3.4.3/
- 内容兑现与专业演示门禁：releases/3.5.0/
- AI视频正式独立审查接线修复：releases/3.5.1/

## 3.5.1核心修复
- AI视频validate/export正式调用validate_v41.validate(batch, review)，不再只依赖轻量review检查。
- Review绑定精确batch文件SHA或规范化payload SHA，错配阻断。
- 至少一名独立评审者身份区分通过，fast_screen/deep_review/critic路由未完成时阻断编辑放行。
- --require-v41-full-validation真实生效，必须V4.1状态PASS。
- 插画继续沿用V2.0独立审查、事实/权利门禁和六表XLSX校验。

## 验证边界
新增5项正式验证接线回归测试。自动化测试只证明代码路径与门禁有效；真人试读、3–5名目标用户盲读、素材授权和真实发布效果仍须实际执行，未完成不得标记PASS。
