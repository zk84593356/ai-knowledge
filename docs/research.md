# 规范与方法论研究记录

核实日期：2026-10-14。下列为当日访问的公开资料，未复制第三方实现或模板。方法借鉴独立落地；没有引入第三方运行代码。测试工具另有自己的许可证，不随 Skill 分发。

| 资料 | 实际检查范围 | 借鉴与落地 | 未引入 |
| --- | --- | --- | --- |
| [Agent Skills 规范](https://agentskills.io/specification) | Frontmatter、目录、渐进加载、文件引用 | 唯一入口，name/description/license/metadata，资源随包 | 宿主专属工具权限声明 |
| [skills CLI](https://github.com/vercel-labs/skills) | README、package.json | skills 子目录发现、指定名称/Agent/范围安装 | 自动全局安装 |
| [Codex skills](https://developers.openai.com/codex/skills/) | 官方完整页面 | 区分安装路径和调用项目；本地资源自包含 | 宿主强绑定的执行 API |
| [PocketFlow](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge) | README 与 docs/design.md | 核心抽象、关系、教学顺序映射到 Feature 证据表及提纲 | 整仓抓取和 LLM 编排框架 |
| [Codebase Tutorial](https://github.com/rowlando/codebase-tutorial) | README 与 SKILL.md | Essence First；核心问题先讲，源码后映射 | 固定章节数量和多份中间 JSON |
| [ELI AgentSkills](https://github.com/jakerains/AgentSkills#eli) | README 的 ELI 专节；单独原始 SKILL 页面抓取失败 | 读者背景、学习目的、解释深度映射到教学地图 | SVG 页面与交互界面 |
| [Obsidian LLM Wiki](https://github.com/0xminion/obsidian-llm-wiki) | README 的结构、元数据与关系设计 | 稳定 Frontmatter、少量有意义链接、知识可维护 | 数据库、RAG、自动 Vault 改写 |

这些研究是文档审阅，不代表运行了参考项目。README 的宣传数字不作为本项目验证依据。

## 安装依据及时间敏感项

官方 Agent Skills 要求名称与目录相同、有效 YAML、非空描述（最多 1024 字符）；入口建议控制在 500 行以内。当前项目没有把 examples/tests/docs 放进运行时依赖。

[skills CLI package.json](https://github.com/vercel-labs/skills/blob/main/package.json) 当日主分支标记 1.7.2，Node engines 为 >=22.20.0；这不自动证明 npm 发布包与主分支完全同步。安装与验证须记录实际 CLI 版本。README 已列出 `update [skills]`、`-g`、`ls` 和本地 `add --list`；因此本项目使用选择单个 Skill 的更新命令，不将其改成全部更新。

Codex 官方页面列出用户级 `~/.agents/skills` 与项目级 `.agents/skills`。不同 CLI/宿主版本可能使用兼容路径；以安装器实际输出和技能发现结果为准，不同时维护两份源码。

## 测试知识来源

- [OpenID Connect Core 1.0，errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)：身份层、ID Token、授权码流程及验证，重点 §1、§2、§3.1。
- [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)：OAuth 2.0 的授权目标与角色，重点 §1、§1.1。
- [Cloudflare Pages build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)：构建命令、根目录、输出目录；只用来核对配置概念，不作为模拟事故发生的证据。

可复用规则来自方法比较；案例事实分别来自已访问标准、本仓库原创代码和明确模拟的固定记录。
