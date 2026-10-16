# AI Knowledge

**把一个问题研究透，写成一篇读者愿意读完、作者敢署名发表的文章。**

ai-knowledge 是一个 Agent Skill，供 Codex 等支持 Agent Skills 的助手使用。它把功能开发、源码阅读、概念学习和问题排查，写成一篇可以直接发到公众号、知乎、X 长文的中文知识文章，同时交给作者一份发布前核验记录。当前开发版本为 v0.6.0。

每个主题交付：

```text
docs/knowledge/<topic-slug>/
├── article.md   # 唯一要发表的文章：复制到平台即可使用，不夹带生产信息
├── review.md    # 只给作者看：证据表、公开安全过滤、可补充的亲身经历、配图状态、标题备选
└── assets/      # 封面 + 2–4 张解释图（PNG 与可编辑 SVG）和 manifest.json
```

## 先看成品

输入：

```text
$ai-knowledge 什么是单点登录？面向初学者讲清楚。
```

![SSO 示例封面](examples/concept-sso/assets/cover.png)

[成品文章](examples/concept-sso/article.md) 的开头：

> 早上九点，你打开公司邮箱，输了一次密码。十点打开报销系统，它没要密码，右上角直接显示了你的名字。
>
> 这两个系统由不同的团队开发，域名也不一样……浏览器的规则是：一个网站存下的 Cookie，只会发回给这个网站。报销系统看不到邮箱的 Cookie，也就无从知道你早上登录过。
>
> 那它是怎么认出你的？答案有点反直觉：报销系统其实也登录了一次，只是这一次不用你动手。

同一目录的 [核验记录](examples/concept-sso/review.md) 列出文章依据的 14 条结论、每条的类型和出处，并标出 1 条存疑；还写明作者可以在哪两处补充亲身经历。

第二个示例用 Feature 模式分析仓库里的原创 OIDC 演示代码：[《OIDC 登录能跑通，为什么还要多传三个随机值？》](examples/feature-oidc-demo/article.md)。文章引用真实的演示代码和单元测试，[核验记录](examples/feature-oidc-demo/review.md) 把每个项目事实对应到文件行号。

![OIDC 示例中的解释图：三个随机值在哪生成、在哪被检查](examples/feature-oidc-demo/assets/oidc-flow.png)

两篇示例都是本仓库实际生成并检查过的产物。核验记录里的条目都标为“未核验”：按设计，写稿者不能给自己的结论盖章，需要新会话、子 Agent 或作者本人独立复查。

## 它怎样写一篇文章

| 步骤 | 做什么 | 产物 |
| --- | --- | --- |
| 研究 | 按模式读代码、资料或排查记录，每条结论标出类型和依据 | review.md 的证据表 |
| 立意 | 一句话写出核心判断，拟三个不同取向的标题和开头 | 选定标题，备选进 review.md |
| 结构 | 每节回答读者的一个问题，一个例子贯穿全文 | 提纲（不存文件） |
| 写作 | 用写作技法和已确认的个人风格写正文 | article.md |
| 配图 | 封面 + 解释图，每张只回答一个问题，手机宽度下可读 | assets/ 与 manifest.json |
| 编辑三遍 | 事实遍、读者遍、文字遍，每遍只看一类问题 | 修订后的 article.md |
| 交付 | 报告路径、未核验条目、可补充经历的位置 | review.md 保持 draft |

三条原则贯穿全程：

- **判断可以有立场，经历必须真实。** 文章可以写“我会先补上这一步”，这类观点在证据表里记为“建议”，由作者认领。作者没讲过的经历不会被写成第一人称故事，而是在 review.md 里留出位置和建议问题。
- **不确定性写在原地。** 证据不足就把结论写窄，不在段落末尾或文末堆免责声明。
- **公开安全优先。** 公司、行业身份、内部域名和类名、日志原文、尚未修复的问题都留在 review.md；需要代码时，文章里放重写的原创演示。

## 三种模式

| 模式 | 输入 | 示例 |
| --- | --- | --- |
| Feature 功能复盘 | 当前代码、Commit、Diff、配置 | [OIDC 登录回调](examples/feature-oidc-demo/article.md) |
| Concept 知识学习 | 一个想讲清的概念 | [单点登录](examples/concept-sso/article.md) |
| Problem 问题复盘 | 报错、日志、排查记录 | 验收用例见 [tests/cases/problem-cf-pages.md](tests/cases/problem-cf-pages.md) |

## 常用说法

```text
$ai-knowledge 帮我把当前项目的 OIDC 登录功能写成一篇文章，面向 Java 初学者。
$ai-knowledge 什么是单点登录？允许查可靠资料，standard 深度。
$ai-knowledge 帮我复盘这次构建失败，只根据我提供的记录。
$ai-knowledge 什么是 SSO？不要图。
$ai-knowledge 把 docs/knowledge/sso/article.md 改编成小红书版本。
$ai-knowledge 请独立复查 docs/knowledge/sso/review.md 的事实核验。
```

更多示例见 [使用说明](docs/usage-examples.md)。平台改编按需另写文件（如 `xiaohongshu.md`），主稿不动；平台规则见 [发布合同](skills/ai-knowledge/references/publishing.md)。

## 个人风格与视觉品牌

Skill 本身不附带任何人的个人配置。你的写作规则和视觉品牌放在自己电脑上的个人配置目录里，不进 Skill、不进任何仓库：

```text
~/.ai-knowledge/personal/          # Windows：%USERPROFILE%\.ai-knowledge\personal\
├── writing-rules.md               # 个人写作规则（只有"已确认"的条目生效）
├── writing-profile.md             # 适用范围
├── learning-log.md                # 学习记录
├── visual/                        # 可选：默认视觉品牌
└── brands/<brand-id>/             # 可选：其他品牌，写文章时说"用 <brand-id> 品牌"
```

每个视觉品牌都是同一套精简结构：`brand-kit.json`（状态、配色、素材清单）、`character.md`（角色识别点、场景规则、生图提示词、验收清单）、`style.md`（定位、配色、各类图的做法）、`provenance.md`（来源与授权），再加一个 `assets/` 图片目录。

**用一张图建立品牌。** 发一张人物或角色图，并明确说"用这张图建立视觉品牌"，Skill 会问三个问题（名字、图片来源、用途），在 `brands/<brand-id>/` 生成一套草稿；如果生图工具能接收参考图，还可以生成三视图和场景候选让你挑。草稿不会被自动使用，你说"确认 `<brand-id>`"之后才生效。只发图不说要做什么，不会启动这个流程。步骤见 [建立视觉品牌](skills/ai-knowledge/references/visual-brand-setup.md)。

**一套图好看、统一、认得出。** [美术方向](skills/ai-knowledge/references/visual-art-direction.md) 把审美写成九条可执行的公式：一个材质比喻、一支笔、一个只当工具用的主色、从角色识别点提取的签名图形、固定版式标记、角色当讲解员、字少字大、生图有规矩、整组验收。每个品牌在 style.md 的"视觉语言"里写下自己的答案；建立品牌或改视觉语言时做一次四图测试（封面、流程图、数据图、插画），满意的那组登记为风格样板。一次出整套图时，用 [出图说明模板](skills/ai-knowledge/assets/templates/art-brief.md) 交给能接收参考图的生图工具。

也可以用环境变量 `AI_KNOWLEDGE_PERSONAL` 指向别的目录（比如你的私有仓库），或在请求里直接给出路径。找不到个人配置时，Skill 自动用公共写作技法和通用图解，功能完整。规则模板在 [assets/templates](skills/ai-knowledge/assets/templates/)，格式示例见测试用的 [演示配置](tests/fixtures/personal-demo/)。

风格可以学习：比较 AI 初稿和你满意的终稿，总结修改习惯；单篇观察先记为候选，经你确认才写回个人配置目录，不需要重装 Skill。见 [复盘演示](examples/style-reflection/report.md)。

## 安装

基础 Skill 没有运行依赖。可选的检查脚本需要 Python 3.10+ 标准库。

```powershell
npx skills add . --list
npx skills add . -g -a codex -s ai-knowledge
```

GitHub 发布后用 `npx skills add <owner>/ai-knowledge -g -a codex -s ai-knowledge`（替换 `<owner>`）。手动安装、刷新已有副本和兼容性说明见 [安装文档](docs/installation.md)。

## 项目结构

```text
skills/ai-knowledge/          # 唯一的 Skill 源码，安装时复制整个目录
├── SKILL.md                  # 入口：八步流程
├── references/               # 按需加载的指南
│   ├── publishing.md         # 文件合同、元数据、平台改编
│   ├── writing-craft.md      # 立意、标题、开头、结构、段落、代码、结尾
│   ├── editing.md            # 三遍编辑、公开安全过滤、独立复查
│   ├── feature-analysis.md / concept-explanation.md / problem-review.md
│   ├── visual-planning.md / visual-art-direction.md
│   ├── visual-brand-loading.md / visual-brand-setup.md
│   └── personal-experience.md / style-*.md
├── assets/templates/         # article.md、review.md 及风格档案模板
└── scripts/                  # 只读辅助：visual_assets.py、style_learning.py、analyze_style.py
examples/                     # concept-sso、feature-oidc-demo 两篇示范，及风格档案/复盘演示
tests/                        # 校验器、单元测试、验收用例与测试报告
docs/                         # 安装、使用、架构与各版本历史验收记录
```

## 开发与测试

```powershell
python -m unittest discover -s tests -v
python tests/validate.py
```

开发需要 Python 3.10+ 和 `tests/requirements.txt` 中的 PyYAML。实际执行的检查及范围见 [测试报告](tests/RESULTS.md)，重跑方法见 [测试说明](tests/README.md)，设计取舍见 [架构说明](docs/architecture.md)。

## 当前限制

- 写作质量依赖宿主 Agent、模型和可用工具；Skill 是指令包，不是独立程序。
- 校验器只检查结构、图片台账和有限的敏感模式，不能证明事实正确、内容可公开或文章好读。
- 真实业务项目的 Feature 文章、Claude Code / Cursor / OpenCode 中的完整执行尚未验收。
- 不提供自动发布、视频脚本、配音、Web UI 或数据库。

## 许可

采用 [MIT License](LICENSE)，Skill 目录内附同一许可。示范文章的配图均为程序化原创图。个人配置目录里的规则和图片归各自作者所有，不受本仓库许可约束。方法参考见 [研究记录](docs/research.md)。
