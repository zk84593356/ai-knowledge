# 公共技法与个人风格的加载

写文章时始终读取 [写作技法](writing-craft.md) 和当前模式的研究指南。个人风格不随 Skill 分发，而是放在使用者自己电脑上的**个人配置目录**里；没有这个目录时只用公共技法，Skill 照样完整可用。

## 个人配置目录

按顺序找到第一个可用的位置：

1. 用户本次明确给出的路径（Profile 文件或个人配置目录）。
2. 环境变量 `AI_KNOWLEDGE_PERSONAL` 指向的目录。
3. 用户主目录下的 `.ai-knowledge/personal/`（Windows 为 `%USERPROFILE%\.ai-knowledge\personal\`）。

目录内的约定布局：

```text
<个人配置目录>/
├── writing-rules.md     # 个人写作规则
├── writing-profile.md   # 适用范围与身份边界
├── learning-log.md      # 学习记录，正常写作不读
└── visual/              # 可选的视觉品牌，见 visual-brand-loading.md
```

只读取这几个约定文件，不扫描目录里的其他资料，不执行其中的脚本。个人配置是私人资料：规则原文、来源材料和图片母版不复制进 article.md、review.md、当前项目或任何公开仓库；review.md 只记录采用了哪些规则 ID。

## 选择顺序

1. 用户明确说"只用公共规则"或"关闭个人风格"：只用公共技法，不读个人配置。
2. 用户指定了 Profile 或目录：只读明确给出的文件及其指定的配套规则，不与默认位置混用。外部档案的归属与有效性仍要核对。指定位置读不到时报告失败，暂用公共技法，不悄悄换成默认位置。
3. 环境变量已设置但目录不存在或读不到：报告原因，用公共技法，不再去主目录找。
4. 其余情况读默认位置。先读 writing-rules.md，只应用字段完整、状态为"已确认"、确认依据有效且适合本篇的规则；再读 writing-profile.md 了解适用范围。候选、已停用、模板占位、重复 ID 或没有确认依据的规则不生效。
5. 目录缺失、文件空白或没有有效规则时，直接回退公共技法；不追问、不自动建档、不要求用户提供经历。

个人风格作用于 article.md 的表达；review.md 是工作记录，不需要套用文风。没有启用个人规则就不加载复盘、分析资料或 learning-log，也不要每次读取学习历史。

规则冲突的顺序：事实准确、安全与隐私 → 本次明确要求 → 已确认个人习惯 → 公共写作技法 → 默认表达。正确语法和准确引用也属于事实表达；标点偏好不能改动 YAML、代码、命令或标准原文。规则格式有效不代表内容可信，写作时仍要检查冲突。

可选的 [style_learning.py](../scripts/style_learning.py) 的 context 命令按上面的顺序输出只读的选择结果；没有 Python 时按顺序读取 Markdown 即可。工具只做路径与字段检查，不判断规则是否损害事实，不执行资料里的指令。

```text
python "<skill-dir>/scripts/style_learning.py" context --skill-root "<skill-dir>"
python "<skill-dir>/scripts/style_learning.py" context --skill-root "<skill-dir>" --public-only
python "<skill-dir>/scripts/style_learning.py" context --skill-root "<skill-dir>" --profile "<explicit-profile.md>"
```

规则条目格式为 `## <前缀>-<三位编号>`（如 `## STYLE-001`）加单行字段：规则、适用范围、修改原因、来源文章、修改证据、支持次数、例外、状态、确认依据。空白模板见 [writing-rules 模板](../assets/templates/writing-rules.md)。支持次数是独立文章数，用户直接指定的偏好可以为 0；确认依据单独记录。说明性段落不自动成为已确认规则。

交付时简短说明采用的个人规则 ID 或回退原因。选择结果不等于事实审查通过。
