# V3 知识检索

按 `assets/connection-config.json` 的 private_knowledge 定位仓库。用认证过的 GitHub 工具读取仓库元数据，核对 owner、仓库 ID 与 Private。用配置分支的完整提交读取版本化 Registry；随后读取资产提交下的 Manifest、Adapter Registry、Asset Catalog 与命中分片。逐份核对 SHA-256。按原始来源和行号引用，长条目读完分页后才引用。

- A 通常先检索选中适配器的现行指导，再按业务、客户、商业模式、平台和目标细化。共享方法单独检索。B 继承 A 的 Registry/资产提交、Manifest 哈希、已用条目和原件定位。旧版运行继续用原来的记录。
- 领域、适配器与项目范围不可混用。样例按明确状态读取，A01 为校准参考；AI 视频六条为候选；18 篇插画稿为编辑参考。历史资产需明确指定历史类别。公开平台机制、创作假设、报道样例和真实发后数据独立记录。
- 有独立项目访问授权时使用项目的受控来源。在普通共享知识仓中，项目级记录可用受信调用方预配置的 project scope 授权，查询参数本身不授予权限。项目目录不是访问边界。
- 命中条目登记来源链接、实际用法、出处和版本。状态记录 KB_NOT_CONFIGURED、KB_ACCESS_DENIED、KB_NO_MATCH、KB_HASH_MISMATCH 或 KB_VERSION_MISMATCH。保留本轮原件，未核验内容不得当证据。旧内置包继续服务历史运行及旧生产校验，不作为 V3 现行知识来源。
- ChatGPT 端如有已配置的 V3 MCP，调用 `knowledge_status`、`search_knowledge`、`read_knowledge`。也可通过 GitHub 读取上述文件并按相同规则筛选。需要程序核验和复用时，以缓存路径 `CACHE/<full-commit>/<repository-relative-path>` 保存受权读取的原样文本，认证仓库元数据保存在 `CACHE/repository.json`，再运行 `scripts/search_verified_knowledge.py` 的 status/search/read。配置路径的缓存需含 23 个受清单校验的分片；未来新增分片按新的 manifest 读取。该缓存只用于本任务。
- WorkBuddy 的旧配置及旧 Registry 继续按原路径工作。stdio 配置见引擎仓新版本 `knowledge-mcp/v3/README.md`。
