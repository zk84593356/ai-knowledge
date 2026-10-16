# 使用示例

默认中文、面向有基础编程常识的初学者、standard 深度，并默认配封面和 2–4 张解释图。以下都是自然语言请求，不是需要记忆的命令语法。

每次生成在当前项目的 `docs/knowledge/<topic-slug>/` 下交付 article.md、review.md 和 assets/。发表时只用 article.md；review.md 是给你看的核验记录。

## Feature：把做完的功能写成文章

```text
$ai-knowledge 帮我把当前项目的 OIDC 登录功能写成一篇文章，面向 Java 初学者。
```

助手会定位当前实现，读相关代码、配置和测试，把每个项目事实对应到文件和行号。有明确历史范围时可以补充"分析某个起点提交到终点提交的变化"。私有代码不进文章，需要代码时会重写一段原创演示；公司名、内部域名和类名在 review.md 的"公开安全过滤"里记下替代写法。

示例：[《OIDC 登录能跑通，为什么还要多传三个随机值？》](../examples/feature-oidc-demo/article.md)，以及对应的 [核验记录](../examples/feature-oidc-demo/review.md)。它分析的是本仓库的原创演示工程，不代表任何真实业务系统。

## Concept：讲清一个概念

```text
$ai-knowledge 什么是单点登录（SSO）？面向初学者讲清楚。允许联网查可靠资料。
```

可以在空项目里调用。能联网时优先查标准和官方文档；不能联网时在 review.md 写明"未联网核实"，不编造引用。

示例：[《登录一次，为什么另一个网站也认得你？》](../examples/concept-sso/article.md) 和 [核验记录](../examples/concept-sso/review.md)。

非技术主题同样适用：

```text
$ai-knowledge 什么是机会成本？面向普通读者，用选择学习时间的例子解释，concise 深度，不需要代码。
$ai-knowledge Explain opportunity cost for beginners in English, concise. Put the files in ./learning/opportunity-cost.
```

## Problem：复盘一次故障

```text
$ai-knowledge 帮我复盘这次 Cloudflare Pages 构建失败。只根据我提供的日志、配置和修改记录，区分事实与推测。
```

附上必要的脱敏记录。没有最终解决也可以写阶段性复盘。日志原文只进 review.md，文章里写经过整理的现象；建议不会被写成已经执行的动作。验收用例见 [problem-cf-pages](../tests/cases/problem-cf-pages.md)。

## 调整篇幅、读者和配图

```text
$ai-knowledge 什么是 SSO？面向有两年经验的后端，deep 深度。
$ai-knowledge 什么是 SSO？不要图。
$ai-knowledge 什么是 SSO？配图关闭个人视觉，用通用图解。
$ai-knowledge 用我指定的 Brand Kit 目录为文章配图，不用默认的个人视觉配置。
```

深度只改变展开程度，不降低来源、隐私和事实要求。配图默认使用个人配置目录里的 Brand Kit（`visual/brand-kit.json`），没有就用通用图解；没有生图工具时做程序化图解，需要人物插画的位置记为待制作项写进 review.md。所有图片先是 draft，你确认后才记为 approved。

## 发表前：复查与补充经历

写稿的助手不能给自己的结论盖章，所以证据表默认全部是"未核验"。发表前建议换一个会话或子 Agent 复查：

```text
$ai-knowledge 请独立复查 docs/knowledge/sso/review.md 的事实核验，逐条对照依据，更新核验状态。
```

review.md 的"可补充的个人经历"列出了文章里最适合放亲身经历的位置和建议问题。你可以直接回答，再让助手融入：

```text
$ai-knowledge 我补充一段经历：……请把它写进 docs/knowledge/sso/article.md 第二节，其余不动。
```

助手不会替你编造经历。你确认可以发布后，说"这篇可以发布了"，review.md 的状态才会改为 ready。

## 改编到其他平台

```text
$ai-knowledge 把 docs/knowledge/sso/article.md 改编成小红书版本。
$ai-knowledge 给这篇文章写一条微博，引导读者看长文。
```

改编稿另存为同目录的 `xiaohongshu.md`、`weibo.md` 等，主稿不动。公众号、知乎、掘金和 X 长文直接使用 article.md。各平台的改编要点见 [发布合同](../skills/ai-knowledge/references/publishing.md#平台改编)；字数和封面比例以平台当前规定为准。

## 个人写作风格

正常写作默认组合公共写作技法和个人配置目录里的已确认规则。个人配置目录按顺序查找：请求里明确给出的路径 → 环境变量 `AI_KNOWLEDGE_PERSONAL` → `~/.ai-knowledge/personal/`（Windows 为 `%USERPROFILE%\.ai-knowledge\personal\`）。它不随 Skill 安装，也不进任何仓库。格式参考测试用的 [演示配置](../tests/fixtures/personal-demo/)。

想在多台电脑上用同一份配置，可以把它放进一个私有 Git 仓库，再设置环境变量指过去：

```powershell
[Environment]::SetEnvironmentVariable('AI_KNOWLEDGE_PERSONAL', 'D:\private\my-style', 'User')
```

设置后重新打开终端和 Agent 才会生效。

```text
$ai-knowledge 什么是 SSO？只使用公共写作规则。
$ai-knowledge 使用我指定的 writing-profile.md 和 writing-rules.md 写这篇文章，不使用默认的个人配置。
```

个人目录缺失、空白或只有候选条目时自动回退公共规则；指定的 Profile 读不到时会说明，暂用公共规则，不悄悄换成默认位置。

### 从参考文章分析风格

```text
$ai-knowledge 分析我指定目录里的三篇 Markdown。完整阅读后提炼句子、用词、过渡和表达姿态，记录证据和例外。只做风格档案，不写文章。
```

可以提供 ZIP 或多个 Markdown 文件。外部文章只产生可借鉴的技巧，不会被写成你的身份和习惯。完整参考资料不写入公开仓库。演示见 [风格档案](../examples/style-profile/writing-profile.md)。

### 从你的修改中学习

```text
$ai-knowledge 对比 article.md 的初稿和我改好的终稿，总结我的修改习惯，更新个人风格。
$ai-knowledge 分析 final.md 的写作特点，只生成学习报告，不更新风格文件。
```

单篇观察先记为候选，多篇重复再补证据，经你确认才生效。演示见 [复盘报告](../examples/style-reflection/report.md)。

要求"更新个人风格"时，助手写回本次实际加载的个人配置目录，下次调用直接生效，不需要重装 Skill。安装包始终只读。找不到个人配置目录时，助手会询问，或只交付可应用的建议。

## 可选的检查命令

不需要 Python 也能使用 Skill。装有 Python 3.10+ 时，可以检查主题目录的结构和图片台账（替换实际路径）：

```powershell
python <skill-root>/scripts/visual_assets.py bundle <topic-directory>
python <skill-root>/scripts/visual_assets.py context --visual
python <skill-root>/scripts/visual_assets.py context --visual --no-brand
```

在本仓库内还可以运行 `python tests/validate.py --bundle <topic-directory>` 检查两份文件的合同。这些检查只证明结构一致，不能证明事实正确或内容可以公开。

不会自动发布、Commit、Push 或全局安装。
