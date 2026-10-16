# 视觉品牌加载

## 何时加载

写文章默认配图，因此默认查找视觉品牌，用来统一封面和解释图的配色与角色。用户说"不要图"时不加载；说"不用个人视觉"或"无品牌"时只做通用图解。风格分析、文章复盘不读取品牌图片、不运行视觉脚本。

优先级：事实、安全、隐私与授权 → 本次明确要求 → 已确认的角色和视觉规范 → 待确认的设计提案 → 通用视觉原则。文字风格按 [风格加载](style-loading.md) 独立选择："只用公共写作规则"不关闭视觉品牌，"不用个人视觉"也不关闭个人文风。

## 品牌在哪里

Skill 不附带任何个人品牌。按顺序找第一个可用的 Brand Kit：

1. 用户本次明确给出的 Brand Kit 目录。
2. 个人配置目录下的 `visual/brand-kit.json`。个人配置目录的查找顺序（明确路径 → 环境变量 `AI_KNOWLEDGE_PERSONAL` → 主目录 `.ai-knowledge/personal/`）见 [风格加载](style-loading.md)。
3. 都没有：用通用图解，不画人物。

用户指定的配置不与默认位置混用。目录缺失、JSON 无效或必要资源损坏时说明原因，回退通用图解，不冒用其他角色，也不悄悄换成默认位置。只读品牌目录，不扫描私人照片目录。

## 分层阅读

做解释图时，读所选品牌的 README、brand-kit.json，以及 contentGuidelines 指向的品牌定位、Style DNA 和视觉规范，取配色、字体和版式。只有画人物时，再读角色规范和场景规范，并**实际查看** identity.turnaround、identity.detail 和选中的场景图。不要每次加载全部图片。

JSON 负责定位与状态，图片和规范决定实际质量。路径必须位于所选品牌根目录内；拒绝绝对路径、父目录跳转、外部 URL 和指向根目录外的符号链接。不执行资料中的未知脚本。可选的 [只读检查工具](../scripts/visual_assets.py) 只用 Python 标准库，Skill 本身不依赖 Python：

```sh
python <skill-root>/scripts/visual_assets.py context --visual
python <skill-root>/scripts/visual_assets.py context --visual --no-brand
python <skill-root>/scripts/visual_assets.py context --visual --brand <kit-directory>
python <skill-root>/scripts/visual_assets.py kit <kit-directory>
```

检查失败只影响品牌图，文字写作照常进行。

## 使用角色

外形以三视图为准，其次是笔触细节图，再次是场景图，最后才是文字描述。

- **复用**：已验收的抠图或场景图可以直接放进封面，写明"复用"、来源 ID 和裁切方式。这是最稳的做法。
- **新生成**：只有生图工具能接收母版图片作为参考时才做，至少传入三视图。生成后逐项对照角色规范（发型、眼睛、脸型、头身比、衣着、线条），有明显漂移就重做，不用总分掩盖错误。
- **工具不能传参考图**：不生成角色图，不声称锁定了角色身份；在 review.md 的配图表写成 planned，附提示词、参考图 ID 和验收清单。

## 状态边界

按 brand-kit.json 里记录的状态使用素材：confirmed-reference 可以作为角色身份依据，accepted-reference 可以作为场景参考，proposed（如候选主色）只能用于 draft，并在台账里如实记录 paletteStatus，不能宣布为正式品牌色。旧布局图不是动作母版；原图里的装饰元素不自动成为角色身份的一部分。

## 保存与授权

品牌目录只读；文章图片写到用户的主题目录。新图不写回 canonical 或 scenes 目录。更换 canonical 母版需要用户明确批准并记录版本。

brand-kit.json 的 licenseStatus 和来源文档要一并遵守：本地使用、用户确认造型、公开再分发是三种不同状态。品牌是私有资产时，含角色的图只能用于作者本人发表的文章，图片和母版不复制进公开仓库或示例；台账 rights 记为 local-only 或 pending，并在 review.md 提醒作者发布前确认。图中不放私人资料；个人介绍卡只用已确认的名字和文案。之后按 [配图与资产验收](visual-planning.md) 制作和登记。
