# 更新记录

## 0.6.0 — 2026-10-16

审美方法论进入公共 Skill：方法写进 Skill，每个品牌只写自己的答案。

- 美术方向：新增 references/visual-art-direction.md。内容有九条公式：一个材质比喻、一支笔、一个只当工具用的主色、从角色识别点提取签名图形、固定版式标记、角色当讲解员、字少字大、生图有规矩、整组验收。还有"谁来画什么"分工表、每张图的自检、四图测试，以及学习别人作品的边界（只学方法，不复制角色、配色组合、版式和提示词，不把别人的图当参考图）。
- 出图说明：新增 assets/templates/art-brief.md，一次出整套图时交给能接收参考图的生图工具或协作 Agent。
- 品牌模板：style.md 增加"视觉语言"（材质、线条、主色用法、签名图形、版式标记、讲解动作、固定/可变/禁止）和"风格样板"两节，删去"两种画面"和"不让生图工具写中文"。
- 建立品牌：第 3 步起草视觉语言提案；新增第 6 步"四图测试"，用户满意后可登记风格样板；以后改视觉语言也先做四图测试。原第 6、7 步顺延为第 7、8 步。
- 配图规则：生图工具可以写短标题和短标签，但必须放大逐字核对，错了重做，最多 3 次，仍不对就改为程序排字；数据图的比例必须与真实数据一致，偏差超过最大值 3 个百分点不能发布；生成图的实际尺寸按比例裁切，台账写实际尺寸；本篇配图做完后整组检查一次。
- 检查工具：品牌图片新增 `sample` 角色（`assets/samples/`），只作风格参考，不能当身份依据；图片记录可以带 `note`。
- 测试：test_brand_kit.py 增加风格样板用例；validate.py 检查新的说明文档和出图说明模板；视觉用例表增加美术方向的五个场景。
- 文档：README、架构说明、安装说明（v0.5.0 → v0.6.0，格式兼容）同步。

## 0.5.0 — 2026-10-16

视觉品牌精简为一种格式，并支持用一张人物图建立品牌。

- 品牌格式：`brand-kit.json`（`schemaVersion` 为 `"2"`）加 character.md、style.md、provenance.md 和 `assets/`。品牌有 `draft`/`confirmed` 两种状态，每张图有 `proposed`/`confirmed` 两种状态，图片角色只有 canonical、scene、layout。不再支持旧格式；旧品牌会被当作无效并回退通用图解，安装说明给出转换方法。四个模板在 `assets/templates/brand/`。
- 建立品牌：新增 references/visual-brand-setup.md。只有"人物图 + 明确要求"同时出现才启动；问名字、来源、用途三个问题，在个人配置目录的 `brands/<brand-id>/` 生成草稿，原图原样保存；可选生成三视图和场景候选（需要能接收参考图的生图工具），候选放在 `candidates/`，选中的才登记；用户确认后才改为正式，没有默认品牌时自动设为默认，已有时先询问。
- 选用品牌：写文章时可以说"用 `<brand-id>` 品牌"按名字选用；默认位置 `visual/` 只自动使用已确认的品牌。
- 检查工具：visual_assets.py 改为校验新格式，新增 `context --brand-id`、`list`（列出个人配置目录里的品牌）和 `inspect`（读出图片尺寸与 SHA-256，供登记使用，不写文件）。
- 测试：新增 test_brand_kit.py；演示配置的品牌改为新格式，新增草稿品牌夹具 `brands/demo-draft/`；validate.py 检查新增的说明文档、四个品牌模板和两套演示品牌。
- 文档：README、使用示例、安装说明（v0.4.0 → v0.5.0 升级）、架构说明同步。

## 0.4.0 — 2026-10-16

目标从"三份稿件"改为"一篇可以直接发表的文章"。

- 文件合同：每个主题交付 `article.md`（唯一要发表的文章，不含任何生产信息）、`review.md`（作者的发布前记录）和 `assets/`。新增 references/publishing.md 规定目录、两份 frontmatter、review.md 六个固定章节、证据表表头与核验枚举、平台改编和封面安全带。
- 流程：SKILL.md 改为八步，研究 → 立意（核心判断、三个标题、开头）→ 结构 → 写作 → 配图 → 编辑三遍（事实、读者、文字）→ 交付。写稿者自己整理的结论只能标"未核验"，交付时建议用新会话或子 Agent 独立复查。
- 写作与编辑：新增 writing-craft.md 和 editing.md，取代 writing-style.md、teaching-principles.md、quality-checklist.md。经历必须真实，作者没提供的经历在 review.md 里留位置和问题；不确定性写在原地，不在文末堆免责声明。
- 配图：默认封面 + 2–4 张解释图（用户说"不要图"时省略），文章只嵌 PNG/JPEG，SVG 作为可编辑源登记在 manifest。visual-planning.md 加入手机宽度、最小字号与封面比例规则，取代 diagram-guide.md 和 visual-plan 模板。
- 三种模式指南各增加"从研究到文章"一节；风格加载、风格应用与视觉规范同步到新合同。平台改编（小红书、微博等）按需另写文件，主稿不动。
- 示例：删除 concept-sso、concept-sso-style、concept-sso-visual、feature-oidc、problem-cf-pages 六组三稿示例和 visual-samples；重写 examples/concept-sso 与 examples/feature-oidc-demo 两篇示范及 7 张配图，OIDC 示范的项目事实对照演示代码与单元测试。两篇的证据表均为"未核验"，尚未独立复查。
- 工程：validate.py 改为检查两份文件合同、review.md 章节与枚举、正文生产信息字样，并增加 JWT、Bearer 令牌、私有 IPv4 模式；visual_assets.py 不再要求 visual-plan.md；测试改用 tests/bundle_fixtures.py 生成夹具；删除 render-visual-review.mjs 及其夹具。历史验收文档中指向已删除文件的链接改为纯文本路径。
- 文档：重写 README、架构说明、使用示例，安装说明增加升级提示，Java OIDC 验收方案与 AGENTS.md 同步到新合同。
- 个人配置移出 Skill：写作规则与视觉品牌改放使用者自己的个人配置目录，查找顺序为明确路径 → 环境变量 `AI_KNOWLEDGE_PERSONAL` → `~/.ai-knowledge/personal/`，都没有时用公共技法与通用图解。风格学习写回该目录，不需要重装 Skill。删除包内 styles/ 目录与相关历史文档；测试改用合成的 tests/fixtures/personal-demo；validate.py 在 skills/ 或 examples/ 出现个人配置时报错。
- 示范配图改为通用配色，封面去掉人物，全部为程序化原创图。
- 未改变：三种模式、证据类型、隐私与公开安全规则、风格学习流程。不自动安装、Commit 或 Push。

## 0.3.0 — 2026-10-15

- 按需加载视觉品牌：支持关闭、指定其他配置与缺失/损坏回退，普通文本路径不加载图片。
- 新增视觉规划指南、通用计划模板和标准库只读视觉检查器：资源闭包、路径边界、图片尺寸/哈希、SVG 自包含、图片链接、草稿审批状态。
- 新增 SSO 图文样例与视觉渲染测试；图片保持 draft，审美与素材授权单独记录。
- 后续修复：三张 SVG 入库时换行被规范化，与台账哈希不一致，已按真实字节重新入库。

## 0.2.1 — 2026-10-14

- 发布文章默认组合公共规范与有效的个人规则；缺失/空白/无有效规则回退，支持显式关闭及其他 Profile 替代。
- 新增 Style Reflection：实际差异、候选习惯、稳定 ID、证据去重、确认与停用、学习日志和公共提案审批。
- 新增只读 style_learning.py、两组模拟改稿与复盘报告及功能测试。

## 0.2.0 — 2026-10-14（本地验收候选，未发布）

- 新增按需加载的 Style Analyzer、Writing Profile、Writing Rules 与可跳过的真实经历采集。
- 事实分析优先，默认只优化发布文章；外部技巧、用户确认习惯与待确认项分开记录。
- 增加可选标准库统计工具：Markdown/ZIP 只读导入、句段统计、词项观察、原始行号抽样、正文去重和输出冲突保护。
- 保留 v0.1.0 九份原始示例，新增 SSO 风格版、主张对照及三篇原创模拟语料；用户外部原文和图片不入仓库。
- 新增 20 项功能与负向测试，修复 Windows ZIP 文件名规范化造成的反斜杠漏检；完整结果见 tests/RESULTS.md。
- v0.3.0 仅形成模块与目录设计，待 v0.2.0 用户验收后实施；没有全局安装、发布或 Git Push。

## 0.1.0 — 2026-10-14

- 首次提供 Feature、Concept、Problem 三种模式的独立 Agent Skill。
- 加入证据整理、Essence First 教学路径、三种稿件独立写作与十项质量门槛。
- 统一 Markdown / Obsidian 元数据及三个文件名，加入输出冲突和隐私规则。
- 提供 SSO 实际生成案例、OIDC 原创演示工程、Cloudflare Pages 模拟复盘。
- 提供结构检查、负向测试、Mermaid 可选渲染检查与 Windows 安装文档。
- 当前是本地初版；真实 OIDC 集成、真人学习效果及其他 Agent 宿主验收尚未完成。
