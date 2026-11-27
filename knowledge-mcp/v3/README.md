# 口播知识库 V3 检索

仓库以 Registry commit 固定登记，再以资产 commit 读取 Manifest、适配器注册表、分片和目录。摘要、SHA-256、记录数、ID 和分片定位逐项校验。旧入口留在上一层目录。候选发布验证通过前使用明确的候选 SHA。正式发布后默认使用版本化登记路径。

## ChatGPT 与 GitHub

连接有权限的 GitHub 账号，先核对仓库 ID、owner 与 Private 可见性，再用完整提交读取 Registry。用其中的 asset_ref 回读并校验 Manifest 与资产。检索先用匹配的业务 adapter，通用方法另查 shared。按 scope 使用项目资料。只有授权的独立项目资产来源才可加载。旧样例明确历史状态后查找。

## 本地 MCP

在有访问权的私有 Git checkout 上启动 stdio 服务。安装上一层目录 requirements.txt。传入 SPOKEN_KB_CHECKOUT、可选 SPOKEN_KB_REGISTRY_REF 和 SPOKEN_KB_REGISTRY_PATH。多用户场景为项目权限不同的调用方使用独立进程及访问凭证。只有受信部署侧可选择 SPOKEN_KB_AUTHORIZED_PROJECTS，用户的搜索参数没有授权效果。

- `knowledge_status` 返回 Registry、资产版本、Manifest SHA 和可读证据统计。
- `search_knowledge` 支持 adapter、domain、platform、kind、status、industry、business model、buyer role、content goal 和 project scope。候选适配器缺资料时返回 KB_NO_MATCH。
- `read_knowledge` 按 ID、偏移和项目权限分页。返回 GitHub 固定提交和行号、原件定位与证据状态。历史资产明确开启 include_history。
