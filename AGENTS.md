# ai-knowledge 维护约定

本仓库交付可独立安装的 Agent Skill，不开发业务应用。用户项目默认只读。

- 唯一入口是 `skills/ai-knowledge/SKILL.md`；不要在根目录或 `.agents/skills` 维护副本。
- 安装包内的运行时引用只能落在 `skills/ai-knowledge/`，使用相对 Markdown 链接。外层文档与测试不参与运行。
- 默认简体中文；保持讲解 `explainer`、复盘 `retrospective`、测评 `evaluation`、观点 `opinion` 四种内容类型，以及 `article.md`、`review.md`、`assets/manifest.json` 的稳定文件名与元数据（合同见 `skills/ai-knowledge/references/发布合同.md`）。
- 参考文档中的平台规则、法规和研究结论必须注明来源与访问日期；查不到出处的数值标为经验值，二手转述标为未核实。不把传言写成平台规则。
- article.md 只放要发表的正文，生产信息（状态、核验、审批）一律进 review.md。写稿者自己整理的结论只能标"未核验"。
- 先核实事实，再改善教学表达。公开示例只用原创、公开或明确模拟的材料，不提交私人代码、密钥、内部地址。
- 个人写作规则与视觉品牌属于使用者私有，放在 Skill 之外的个人配置目录（`AI_KNOWLEDGE_PERSONAL` 或 `~/.ai-knowledge/personal/`），不放进本仓库的任何位置。测试只用 `tests/fixtures/personal-demo/` 的合成配置，不读取真实主目录。
- 不把建议写成历史事实，不把模拟案例写成真实事故，不把静态验证写成真实登录或部署成功。
- 修改通用规则后重跑 `tests/cases/` 中受影响的内容类型案例（讲解、复盘、测评、观点）、流程停点案例及边界案例，并用 `python tests/validate.py --bundle <目录>` 检查两篇示范；测试只证明所覆盖的行为，不声称覆盖所有 Agent。
- 使用 Python 3.10+ 执行 `python -m unittest discover -s tests -v` 和 `python tests/validate.py`。开发依赖见 `tests/requirements.txt`，运行 Skill 无需 Python。
- 可选 Mermaid 实际渲染：`node tests/check-mermaid.mjs`（只检查 docs 等开发文档；article.md 不允许 Mermaid），依赖安装说明见 `tests/README.md`。缺失工具记为未验证。
- 变更后更新 `CHANGELOG.md` 与 `tests/RESULTS.md`，后者写明实际命令、结果与限制。
- 不自动全局安装、不发布文章、不部署、不推送 GitHub。安装示例中的 owner 是待用户替换的参数。

新增资源必须有明确用途；不引入生成服务、数据库或运行框架。修复规则应针对可复现问题，避免为单个案例硬编码。
