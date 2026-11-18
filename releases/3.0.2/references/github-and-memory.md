# 当前知识版本与回流

## 三个版本号分别代表什么

- **Skill 发布包：3.0.2**，表示本次可安装/发布的 Skill 与插件补丁版本。
- **引擎/数据合同：3.0.0**，表示批次字段、执行阶段、Schema 与 XLSX 数据合同；本补丁不改变它。
- **知识快照：20261118-evening**，对应 KB-MANIFEST.json 的 version=3.0.0、release-policy.json 和固定的六份源文件；本补丁不重写原始知识资料。

三个版本用途不同，不得把 engine_version=3.0.0 或知识 Manifest 的 version=3.0.0 当成 Skill 包仍是旧版。

## 唯一活动版本与连接核验

仓库根目录 REPO-REGISTRY.json 是当前发布入口；assets/connection-config.json 是 Skill 内连接配置。两者的仓库名、发布版本、manifest_ref、asset_ref、base_path、manifest_path、engine_path 与 source_release 必须一致。engine_ref_policy=registry_commit 表示执行代码按注册表所指的当前提交读取；asset_ref 固定完整知识快照提交。发布后必须回读两个文件，不能只凭文件上传成功认定同步完成。

当前活动 Skill 发布目录为 releases/3.0.2/。知识快照的活动路径由注册表和连接配置共同指向；不得将历史目录或历史提交作为生产回退。包内快照仅在网络不可用时作为同版本、校验相符的离线备份。

## 知识资产与适用范围

通用方法与九基因独立于插画。当前6原件保存在 standards/20261118/originals，来源SHA与1229格逐项去向可查；current-examples仅插画域读取，每平台按共同任务/显式sample ID选择至多2稿，附全文和全部执行段及冲突。15封面来自SRC5，SRC3解释成立/失效条件；其他行业不加载这些原文。没有本行业样例用通用机制加当前事实，不找相近行业硬冒精确命中。

网络不可用可用同版本、校验相符的包内快照；旧版包不可替代。缺知识仅阻断依赖内容，不宣称在线读取。当前官方平台规则与当次账号另核，包内策略不认证算法权重。

## 记忆与回流

记忆按brand_scope隔离、去重、授权后写，反馈采纳、事实修正、编辑偏好与效果数据分开。只有回读确认才标synced；用户修改不等于实发证据。不得把本轮研究四件事写成生产模块。
