# 测试与验收

本项目的 Skill 由 Agent 执行，测试分为生成走查、程序检查、内容审读和真实宿主验收四层。脚本不会自动调用模型，也不会根据标题匹配就给教学质量打高分。

每个主题的产物是一篇可发表的 `article.md`、一份只给作者看的 `review.md`，以及按需的 `assets/`（PNG 图片、`manifest.json` 和可编辑 SVG 源）。合同见 [发布合同](../skills/ai-knowledge/references/publishing.md)。

## 可重复运行的自动检查

需要 Python 3.10+，开发依赖只有 PyYAML；Skill 使用者无需安装它。在可写的虚拟环境中按需执行：

```powershell
python -m pip install -r tests/requirements.txt
python -m unittest discover -s tests -v
python tests/validate.py
python tests/validate.py --bundle examples/concept-sso
python tests/validate.py --bundle examples/feature-oidc-demo --root .
python tests/validate.py --skill skills/ai-knowledge
python skills/ai-knowledge/scripts/visual_assets.py bundle examples/concept-sso
```

`--bundle` 检查一个主题目录里的 `article.md` 与 `review.md`；`--root` 是允许引用的本地范围（默认仓库根目录）。`--expected-date` 用于验证某次生成的 `updated` 日期，重跑历史案例时保留其真实生成日期；不要每天刷新样例日期制造新生成记录。检查器默认不联网、不改产物，只检查项目约定，不是 Agent Skills 官方规范的完整实现。

`article.md` 的检查：

- Frontmatter 只能有 title、topic、type（`"article"`）、mode、summary、tags、created、updated、language；summary 非空且不超过 60 字；tags 是 2–5 个非空字符串；日期为真实的 `YYYY-MM-DD` 且 updated 不早于 created；topic 是合法 slug，不是 Windows 保留名。
- 正文没有一级标题（代码围栏内除外），至少一个二级标题；没有 Mermaid 围栏、HTML 注释和模板占位符（双花括号变量、方括号 TODO 标记）。
- 图片只能是 `![非空 alt](./assets/<name>.png|.jpg|.jpeg)`，文件必须存在；SVG 只能作为台账里的可编辑源，不能嵌入文章。
- 正文（代码围栏外）不能出现生产状态用语：未核验、已核验、发布前核验、核验日期、草稿、draft、待审批、未批准、工作区。`draft-ietf-…` 这类标识符不算。

`review.md` 的检查：

- Frontmatter 只能有 title、topic、type（`"review"`）、mode、status（`draft` / `ready`）、created、updated、language；title 必须是文章标题加 `｜发布前核验`。
- 正文恰好一个一级标题，依次包含 `## 发布状态`、`## 事实核验`、`## 公开安全过滤`、`## 可补充的个人经历`、`## 配图`、`## 标题与摘要备选`，中间可以插入其他二级标题。
- `## 事实核验` 里有表头为 `| ID | 结论 | 类型 | 依据 | 核验 |` 的证据表，至少一行；每行 5 格，ID 非空且不重复；类型限项目事实、框架行为、协议原理、通用知识、推测、建议；核验限未核验、已核验、推翻、存疑、不适用；建议类必须填"不适用"。

两份文件的 topic、mode、language、created 必须一致。同目录的平台改编稿（如 `xiaohongshu.md`、`weibo.md`）不参与两份文件的合同检查；仓库级检查对它们只豁免"恰好一个一级标题"。

仓库级检查还包括：必要文件、唯一入口、运行资源闭包（references、templates、scripts、LICENSE）、内联相对链接存在与越界（行内代码里的示例链接不检查）、源码行号范围、有限敏感模式。敏感模式包括私钥、常见平台令牌、赋值形式的密钥、类 JWT 字符串、Bearer 令牌、私有 IPv4（10.x、172.16–31.x、192.168.x）、个人 Windows 路径和内部域名 URL；只报告类别，不回显匹配值。

不覆盖：外部链接实时可达性、完整 CommonMark 语法、所有密钥格式、引用是否确实支持结论、"已核验"是否真的来自独立复查、真人学习效果。引用式链接、复杂 Markdown 和标题锚点仍需人工核对。

单元测试使用临时目录里新构造的两文件主题（`bundle_fixtures.py`，含用 zlib 生成的最小 PNG），不依赖公开示例。覆盖合法主题、无图主题、缺 review.md、文章含一级标题、Mermaid、HTML 注释、占位符、状态用语、摘要超长、标签数量、类型不符、核验记录缺节或乱序、类型/核验枚举错误、建议类误标、证据表缺失或为空、标题不符、元数据不一致、文章嵌入 SVG、图片缺 alt 或缺文件、坏 YAML、重复键、无效日期、路径越界、错误源码行号与凭据模式。`test_real_package_passes_validate_skill` 复制真实安装包做闭包检查。OIDC 测试只验证原创示例的编排逻辑，不模拟成功的密码学验签。

## 可选的 Mermaid 实际渲染

需要受支持的 Node.js（脚本使用顶层 await，需 14.8 及以上）与本地浏览器。这是开发依赖，不随 Skill 安装。只在仓库忽略目录安装：

```powershell
npm install --prefix .test-tools --ignore-scripts --no-audit --no-fund mermaid@11.12.2 playwright@1.62.1 skills@1.7.2
node tests/check-mermaid.mjs
```

Windows 脚本使用已安装的 Edge；其他系统使用 Playwright Chromium，如未安装，可在用户选择后运行对应 Playwright 安装命令。缺失依赖或浏览器返回退出码 2，属于跳过而非通过。已有 Playwright 模块可通过 `AI_KNOWLEDGE_NODE_MODULES` 指向它所在的 node_modules。脚本阻断页面网络，只在本地解析并生成 SVG/PNG 到 `tests/.tmp/mermaid/`；也验证一份故意错误的语法确实被拒绝。

文章正文不再允许 Mermaid；这个脚本只检查指南和文档里仍保留的 Mermaid 示例。解析和渲染成功后仍要打开图片核对标签与箭头。图中有真实私有数据时不使用在线渲染服务。

## 三个核心生成案例

依次运行 [SSO](cases/concept-sso.md)、[OIDC](cases/feature-oidc.md)、[Pages](cases/problem-cf-pages.md)。提供 Skill、原始输入、受众与独立输出目录，让 Agent 按流程实际生成 `article.md`、`review.md` 和配图，再运行检查并审读。不要提供"标准答案"让模型抄写。

当前仓库 `examples/concept-sso/` 与 `examples/feature-oidc-demo/` 是主 Agent 实际执行 Skill 流程后落盘的产物，不是外部 Agent 的自动基准，也不是已全局安装后的端到端测试。重新验收时使用 `tests/.tmp/runs/<case>/`，不要覆盖公开示例；案例证据可用从新目录解析正确的相对路径。

## 边界验收

[边界用例](cases/boundaries.md) 覆盖离线、证据缺失、提示注入、非技术英文、自定义路径、重复生成、不要图和核验状态。内容走查与宿主实际执行必须分别记录；只有真的写入两次并比较旧文件，才能称为冲突保护行为测试。

内容审读按 [编辑与核验](../skills/ai-knowledge/references/editing.md) 的三遍编辑与阻断项进行。结论必须附依据，事实与证据真实性为硬门槛。`review.md` 里的"已核验"只能来自独立复查（新会话、子 Agent 或用户），不能由同一生成 Agent 的自评代替；真人学习效果需要用户另行阅读与回答问题。

实际结果见 [RESULTS.md](RESULTS.md)。

## 风格测试

`test_style_analysis.py` 覆盖本地导入、句段统计、引用/提示词排除、去重、空正文、ZIP 越界与符号链接、编码/容量限制、自定义词表、已有输出保护及独立安装包运行。统计不推断作者身份或自动评分文风。

公开语料可直接复跑，不依赖用户附件：

```powershell
python skills/ai-knowledge/scripts/analyze_style.py tests/fixtures/style-corpus --provenance simulated
python skills/ai-knowledge/scripts/analyze_style.py examples/concept-sso/article.md --provenance simulated
```

需要保存 JSON 时，先在被忽略的 tests/.tmp 下准备目录，再通过 `--output` 指定未存在的文件；已有文件返回失败。外部真实参考不成为公开测试依赖，复现其统计需用户自行提供相同 ZIP。输出虽默认不含摘录，仍有文件名与词频，应按私人材料管理。

Agent 行为与文风审读输入见 [风格用例](cases/style-engine.md)。人工走查不能用几个禁用词的字符串匹配替代，也不等于真人审美认可。

`test_style_learning.py` 验证个人配置根目录的查找顺序（显式 `--profile` > 环境变量 `AI_KNOWLEDGE_PERSONAL` > `~/.ai-knowledge/personal`）、环境变量指向不存在的目录时回退公共规则且不改读主目录、缺失/空白/无效回退、`--public-only`、通用规则 ID（`<大写前缀>-<三位以上数字>`）、准确 diff、仅终稿、证据去重、候选不自动确认，以及从其他工作目录运行安装副本时没有文件变化。测试使用合成的 [演示个人配置](fixtures/personal-demo/README.md) 的临时副本，并把主目录替换为空的临时目录（进程内替换 `Path.home`，子进程设置 `HOME` 与 `USERPROFILE`），不读取真实用户目录。

```powershell
python skills/ai-knowledge/scripts/style_learning.py context
$env:AI_KNOWLEDGE_PERSONAL = (Resolve-Path tests/fixtures/personal-demo).Path
python skills/ai-knowledge/scripts/style_learning.py context
Remove-Item Env:AI_KNOWLEDGE_PERSONAL
python skills/ai-knowledge/scripts/style_learning.py context --public-only
python skills/ai-knowledge/scripts/style_learning.py compare --draft tests/fixtures/style-reflection/sso-draft.md --final tests/fixtures/style-reflection/sso-final.md
python skills/ai-knowledge/scripts/style_learning.py compare --final tests/fixtures/style-reflection/sso-final.md
```

Skill 不附带任何个人配置。个人配置放在用户本地：环境变量 `AI_KNOWLEDGE_PERSONAL` 指向的目录，或 `~/.ai-knowledge/personal`；根目录下是 `writing-rules.md`、`writing-profile.md`、`learning-log.md`，品牌包在 `visual/brand-kit.json`。都没有时使用公共写作规则和通用图解。`validate.py` 要求安装包内不存在 `styles/personal`，仓库级检查还会在 `skills/` 与 `examples/` 的文件名和内容里查找原私人配置的标识，防止私人配置回流；`docs/`、`CHANGELOG.md` 与 `tests/RESULTS.md` 保留历史记录，不在此检查范围。演示配置的三份 Markdown 与 `visual/` 品牌包也由仓库级检查验证。

测试脚本不证明某次风格改写的事实一定正确，也不能代替宿主写回权限检查。事实不变、公共提案确认、源路径未知与隐私边界由 [复盘用例](cases/style-reflection.md) 记录主 Agent 的实际决策，不伪装成自动语义测试。

## 视觉检查

`test_visual_assets.py` 覆盖按需读取、品牌包查找顺序（显式 `--brand` > `$AI_KNOWLEDGE_PERSONAL/visual` > `~/.ai-knowledge/personal/visual`）、环境变量失效时不改读主目录、`--no-brand`、指定/损坏/缺失回退通用图解、图片边界与哈希、危险 SVG、草稿状态、缺图与未登记图片、文章只嵌 PNG/JPEG、无图主题不要求台账、有图或有 assets/ 时必须有台账、品牌版本一致性、迁移目录及安装包只读。

```powershell
python skills/ai-knowledge/scripts/visual_assets.py kit tests/fixtures/personal-demo/visual
python skills/ai-knowledge/scripts/visual_assets.py context --visual --brand tests/fixtures/personal-demo/visual
python skills/ai-knowledge/scripts/visual_assets.py bundle examples/concept-sso
python skills/ai-knowledge/scripts/visual_assets.py bundle examples/feature-oidc-demo
node tests/check-visuals.mjs
```

`check-visuals.mjs` 使用与 Mermaid 相同的本地 Playwright/浏览器依赖，读取 `examples/concept-sso` 和 `examples/feature-oidc-demo` 中 `article.md` 嵌入的每张图，以及台账里 generated/approved 的资产（含可编辑 SVG 源），在 720px 与 390px 下本地解码、检查 SVG 文字是否越出画布并截图，输出只写 `tests/.tmp/visuals/`。找不到任何图片时返回失败，不报告通过。

图片检查支持 PNG/JPEG 尺寸头、SVG 文本与有限安全子集、标准内联/引用式 Markdown 图片。PNG/JPEG 完整解码由浏览器渲染额外核实；不自动推断图像内容或批准角色身份。HTML img / wiki 图片要求转成标准语法。所有本地来源和图片清单也需内容审读。

复制到独立目录可复跑 CLI，不依赖外层 docs/tests。符号链接创建若受操作系统权限限制，测试报告 skip，不能声称已实际覆盖。

生成与内容审读用例见 [视觉用例](cases/visual-engine.md)。主 Agent 看图检查不是用户审美确认，也不是所有宿主兼容性证明。
