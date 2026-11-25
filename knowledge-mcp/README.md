# 口播知识库接入

GitHub 保存私有知识资产。口播 Skill 在策划或成稿前按任务读取固定版本。知识库独立于引擎发行版本。每个任务记录使用的 registry commit、asset commit、知识条目 ID 和原件定位。普通检索只读。

## ChatGPT 与 GitHub MCP

1. 从获授权的私有知识仓库读取根目录 `KNOWLEDGE-REGISTRY.json`，记下本轮读取该文件的 commit。先用 GitHub 仓库元数据核对仓库身份、ID 和 Private 可见性。
2. 按登记的 `asset_ref` 读取 `manifest_path`。核对 manifest SHA-256，按 manifest 的路径和 SHA-256 读取相关分片。需要二进制原件时用 base64 读取并验证哈希。按业务任务、赛道、平台、证据状态选择记录。
3. 将命中条目及来源定位写入本轮内部来源记录。A 先查客户任务和领域指导，按所选平台核对规则。B 延续 A 的固定版本，按剧本主张选择可用证据和样稿。当前任务附件仍决定具体客户、素材、事实和文案锁定。
4. 无权限、找不到资料或哈希不符时记录不同的状态。继续用用户原件与已明确验证的资料。旧快照仅作历史复核，禁止静默改用历史规则。

GitHub 官方 MCP Server 可使用只读 `get_file_contents`，提交固定在 `sha`。ChatGPT GitHub 连接器对应工具为 `get_repo` 与 `fetch_file`。读取仓库默认分支仅用于发现登记。资产全部按完整 SHA 读取。平台规则的引用需要遵守来源与适用范围，历史样例、报道线索、用户标杆和当前业务事实的证据状态各自保留。

## 支持 stdio 的 MCP 客户端

通过已有的 GitHub 身份验证克隆私有知识仓库，安装本目录的 `requirements.txt`。配置 MCP 客户端运行 `server.py`，环境变量 `SPOKEN_KB_CHECKOUT` 指向该私有 Git checkout。可用 `SPOKEN_KB_REGISTRY_REF` 固定登记提交。省略时启动进程锁定本地 HEAD。服务从 Git 对象验证并载入 manifest 及所有检索分片，工作目录里的临时修改不会混入已固定的快照。

Codex MCP 配置示例

```toml
[mcp_servers.spoken_script_knowledge]
command = "/path/to/venv/bin/python"
args = ["/path/to/spoken-script-engine/knowledge-mcp/server.py"]
env = { SPOKEN_KB_CHECKOUT = "/path/to/private-kb-checkout" }
```

用 `knowledge_status` 检查版本。用 `search_knowledge` 按平台、赛道、类型或证据状态找资产。用 `read_knowledge` 按 ID 读取正文和来源。长条目按返回的 `next_offset` 分页。原件、历史快照由 GitHub 按 manifest 路径下载。域过滤为严格匹配，跨域共用方法可另查 `domain=shared`。
