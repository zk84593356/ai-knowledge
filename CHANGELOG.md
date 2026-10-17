# 更新记录

## 0.8.0 — 2026-10-17

个人配置并入内容工作台，上手改为三步：初始化工作台 → 可选建品牌资产 → 复制提示词开始写。

- 工作台初始化：新增 references/流程/工作台初始化.md。`create_project.py init` 把 `templates/内容工作台/` 整套复制进工作台（默认人设、工作台说明、风格参考、写作技巧、规范指南、品牌资产说明），已有文件不覆盖并逐个列出；建好 `我的项目/` 和 `品牌资产/`；把位置写进 `~/.ai-knowledge/settings.json`（已记了别的位置时不改，`--set-default` 切换，`--no-remember` 不写）。找不到工作台时先问作者要不要建，不建就写到 `docs/knowledge/` 并用 Skill 自带的默认文件。
- 默认内容：写作技巧（内容写作技巧、金字塔原理写作技巧、偏航句用法）和规范指南（自媒体防限流指南、口播引导话术、自媒体动画、运营沉淀）从 references 移到 `templates/内容工作台/`，作为作者可以改的默认版本；新增默认 用户人设.md（状态：默认，按中性作者写）、风格参考/如何用 Grok Bot 做内容.md（公开文章的原创写法拆解，只有少量摘录和原文链接；初始化时可选把原文抓到作者本地）、写作规则/档案/改稿学习日志的空架子。
- 个人风格：写作规则、档案、学习日志改为工作台 `风格参考/我的写作规则.md`、`我的写作档案.md`、`改稿学习日志.md`；工作台的 `写作技巧/内容写作技巧.md` 覆盖 Skill 自带版本。`AI_KNOWLEDGE_PERSONAL` 和 `~/.ai-knowledge/personal/` 不再读取，迁移方法见安装说明。
- 视觉品牌：品牌放在工作台 `品牌资产/<brand-id>/`，可以有多个，目录名必须等于 `brandId`。去掉"默认品牌"：写文章时列出已确认的品牌，在确认角度时问作者用哪个，答案写进需求卡新增的"配图品牌"字段；草稿品牌只在点名时使用。新增 `create_project.py brand <brand-id> [--name]` 建品牌骨架。
- 脚本：style_learning.py `context`、visual_assets.py `context` 与 `list` 新增 `--workspace`；`visual_assets.py context --visual` 不带品牌名时只返回 `available`（已确认品牌列表）。
- 目录：references 分为 流程/、调研/、写作/、风格/、视觉/ 子目录（用户人设-快速参考.md 改名为 流程/用户人设.md）；模板分为 templates/文章/ 和 templates/品牌/（原 templates/brand/）。
- 测试：夹具 tests/fixtures/personal-demo 改为 workspace-demo（风格参考/、品牌资产/demo-brand、品牌资产/demo-draft）；validate.py 检查新路径、默认文件清单和默认文件内的链接不越界；test_workspace.py 覆盖 init 逐字节复制、不覆盖、settings.json 记录与切换、brand 命令；style/visual 测试改为工作台查找顺序并覆盖 `--workspace`。
- 文档：README 改为三步上手和"内容工作台里有什么"；安装说明新增 v0.7 → v0.8 升级；架构说明、使用示例、content-workflow.md、tests/README.md、AGENTS.md 同步。

## 0.7.0 — 2026-10-17

从"写一篇技术文章"扩展为一套内容创作流程，按 docs/content-workflow.md（v0.2）实现。

- 内容类型：讲解 `explainer`、复盘 `retrospective`、测评 `evaluation`、观点 `opinion` 四种，取代 concept/feature/problem。新增证据类型"公开资料""实测记录"。旧稿的模式值不自动转换，升级方法见安装说明。
- 流程：SKILL.md 改为 11 步（接需求 → 调研 → 选角度 → 备素材 → 搭结构 → 写初稿 → 打磨四遍 → 配图 → 平台改编 → 发布归档 → 复盘学习），三种协作强度（快速、标准、深度），各有固定停点。
- 内容工作台：可选的外部目录（用户人设、风格参考、写作技巧、规范指南、我的项目下按平台分稿件、历史存档），查找顺序为请求路径 → `AI_KNOWLEDGE_WORKSPACE` → 个人配置 `settings.json` 的 `workspace`；没有时仍写到 `docs/knowledge/<slug>/`。新增 scripts/create_project.py（init/new，不覆盖已有文件，同名加 `-02`）和 scripts/save_article.py（把已发布项目移到历史存档，支持 dry-run）。
- 目录：references 全部改为中文文件名（如 publishing.md → 发布合同.md、editing.md → 打磨与核验.md、writing-craft.md → 内容写作技巧.md）；assets/templates/ 移到 templates/，文件名加 `-template`。新增 skills/ai-knowledge/README.md，说明每个文件对应流程的哪一步。
- 新参考文档 13 份：调研-测评、调研-观点、调研-资料卡、用户人设-快速参考、选题与角度、写作技巧-金字塔原理、偏航句用法、降AI味指南、自媒体防限流指南、平台改编、口播引导话术、自媒体动画、运营沉淀。平台规则、法规和研究数字都注明来源与访问日期，查不到出处的标为经验值或未核实。
- 旧参考文档：发布合同加入工作台布局、四种模式和发布状态字段；打磨与核验由三遍改为四遍（事实、读者、文字含降 AI 味与防限流、独立复查），新增"未披露利益关系"阻断项；内容写作技巧加入手机阅读排版和各类型主线；协作文档与真实经历重写。
- 模板：重写 article 与 review 模板；新增 brief、协作文档、口播稿、资料卡、用户人设模板。
- 测试：validate.py 适配新文件名、四种模式和新证据类型；新增 tests/test_workspace.py；新增用例 tests/cases/workflow-gates.md、evaluation-opinion.md 和模拟夹具 tests/fixtures/evaluation-demo/；边界用例补充工作台路径、没有人设、降重与过检测、限流传言和推广测评的利益披露。两篇示范的模式改为 explainer / retrospective，目录名不变。
- 文档：README、架构说明、安装说明（v0.6.0 → v0.7.0）、AGENTS.md、content-workflow.md 同步。

## 文档更新 — 2026-10-17

只改 README，Skill 本身仍是 0.6.0。

- README 改为使用指南：5 分钟上手（安装、更新、手动复制）；九个玩法，每个都附可以直接复制的提示词（功能、知识、踩坑三种模式，读者/深度/语言/配图选项，发表前把关，一稿多发，更新旧文章，风格学习，品牌配图）；打造品牌人物的第 0–5 步（含生成原创人物的提示词、四图测试和登记风格样板）；个人配置目录的结构、生效规则和多台电脑共用的方法。
- docs/usage-examples.md 精简为补充页：只留默认值、指定配置、只分析不改风格、示例索引和可选检查命令，其余以 README 为准。

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
