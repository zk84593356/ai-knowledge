# 使用示例（补充）

安装方法、三步上手、玩法、建立品牌人物和内容工作台都在 [README](../README.md)，提示词可以直接复制。这里只补充 README 没写的细节。

## 默认值

不说明时：中文、面向有基础编程常识的初学者、standard 深度、配封面和 2–4 张解释图，有内容工作台时写到 `我的项目/公众号写作/<YYYYMMDD>-<topic-slug>/`，没有时写到当前项目的 `docs/knowledge/<topic-slug>/`。提示词都是自然语言，不需要记命令语法。用户指定的语言、读者、篇幅、平台和输出位置优先。

配图品牌不自动挑：工作台 `品牌资产/` 里有已确认的品牌时，助手在确认角度时问这篇用哪个，答案记进需求卡；没有品牌就用通用图解。没有生图工具时做程序化图解，需要人物插画的位置记为待制作项写进 review.md。所有图片先是 draft，你确认后才记为 approved。

## 指定配置，不用默认位置

```text
$ai-knowledge 使用我指定的 [写作规则文件] 写这篇文章，不用工作台里的写作规则。
$ai-knowledge 用我指定的 Brand Kit 目录 [目录路径] 为文章配图，不用工作台里的品牌。
$ai-knowledge 这篇用工作台 [D:\另一个工作台]，不用默认的那个。
```

工作台里的写作规则缺失、空白或只有候选条目时，自动回退公共规则。指定的文件或工作台读不到时，助手会说明并暂用公共规则，不会悄悄换成默认位置。

## 只分析，不改风格

```text
$ai-knowledge 分析 [final.md] 的写作特点，只生成学习报告，不更新风格文件。
$ai-knowledge 分析我指定目录里的三篇 Markdown，提炼句子、用词、过渡和表达姿态，记录证据和例外。只做风格档案，不写文章。
```

要求"更新个人风格"时，助手写回本次实际使用的工作台的 `风格参考/`；找不到工作台时，会询问或只交付建议。安装包始终只读。

## 示例索引

| 内容 | 位置 |
| --- | --- |
| 讲解示范文章 | [concept-sso](../examples/concept-sso/article.md)，[核验记录](../examples/concept-sso/review.md) |
| 功能复盘示范文章（分析本仓库的原创演示工程） | [feature-oidc-demo](../examples/feature-oidc-demo/article.md)，[核验记录](../examples/feature-oidc-demo/review.md) |
| 故障复盘验收用例 | [problem-cf-pages](../tests/cases/problem-cf-pages.md) |
| 风格档案演示 | [style-profile](../examples/style-profile/writing-profile.md) |
| 修改复盘演示 | [style-reflection](../examples/style-reflection/report.md) |
| 工作台格式 | [演示工作台](../tests/fixtures/workspace-demo/) |
| 平台改编要点 | [发布合同](../skills/ai-knowledge/references/流程/发布合同.md#平台改编) |

## 可选的检查命令

不需要 Python 也能使用 Skill。装有 Python 3.10+ 时，可以检查主题目录的结构和图片台账（替换实际路径）：

```powershell
python <skill-root>/scripts/visual_assets.py bundle <topic-directory>
python <skill-root>/scripts/visual_assets.py list
python <skill-root>/scripts/visual_assets.py context --visual --brand-id <brand-id>
python <skill-root>/scripts/visual_assets.py context --visual --no-brand
```

在本仓库内还可以运行 `python tests/validate.py --bundle <topic-directory>` 检查两份文件的合同。这些检查只证明结构一致，不能证明事实正确或内容可以公开。
