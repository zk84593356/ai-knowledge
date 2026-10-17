# ai-knowledge Skill 目录说明

本文件给维护者和想了解 Skill 内部结构的作者看，Agent 运行时从 [SKILL.md](SKILL.md) 进入，按流程节点按需加载下面的文件。

```text
ai-knowledge/
├── SKILL.md                      # 入口：11 步内容创作流程、四种内容类型、三种协作强度
├── README.md                     # 本文件
├── LICENSE
├── references/                   # 公共操作手册，按流程节点按需加载
│   ├── 流程/
│   │   ├── 工作台初始化.md         # 建工作台、可选品牌资产、旧个人配置迁移
│   │   ├── 发布合同.md            # 工作台目录、文件名、frontmatter、review.md 结构
│   │   ├── 用户人设.md            # ① 怎么读工作台的 用户人设.md
│   │   ├── 选题与角度.md          # ③ 角度方案、核心判断、选题库
│   │   ├── 协作文档与真实经历.md   # ④ 作者任务单与经历采集
│   │   └── 打磨与核验.md          # ⑦ 四遍打磨、阻断项、独立复查
│   ├── 调研/
│   │   ├── 讲解.md               # ② 讲解类调研
│   │   ├── 复盘功能.md            # ② 功能复盘调研
│   │   ├── 复盘故障.md            # ② 故障复盘调研
│   │   ├── 测评.md               # ② 测评：测试设计、记录、利益披露
│   │   ├── 观点.md               # ② 观点：事实与判断、反方、论证漏洞
│   │   └── 资料卡.md             # ② 资料卡的存放、有效期和复用
│   ├── 写作/
│   │   ├── 降AI味指南.md          # ⑦ 文字遍：AI 味模式与改法
│   │   └── 平台改编.md            # ⑨ 小红书、微博、X、短视频口播
│   ├── 风格/
│   │   ├── 加载.md               # ⑥ 公共技法与工作台风格资料的加载顺序
│   │   ├── 应用.md               # ⑥ 在事实稳定后应用个人规则
│   │   ├── 改稿复盘.md            # ⑪ 对比 AI 稿和作者发出的版本
│   │   ├── 分析.md               # ⑪ 从多篇文章分析风格
│   │   └── 写回.md               # ⑪ 把确认的习惯写回工作台
│   └── 视觉/
│       ├── 品牌加载.md            # ⑧ 列出品牌、问作者用哪个
│       ├── 美术方向.md            # ⑧ 统一整组配图风格
│       ├── 配图验收.md            # ⑧ 制作、导出、manifest.json 与检查
│       └── 建立品牌.md            # 按需：用一张角色图建立视觉品牌
├── templates/
│   ├── 内容工作台/                # 初始化时整套复制到作者的工作台
│   │   ├── 工作台说明.md
│   │   ├── 用户人设.md            # 默认人设（状态：默认）
│   │   ├── 风格参考/              # Grok Bot 写法拆解、写作规则/档案/学习日志空架子
│   │   ├── 写作技巧/              # 内容写作技巧、金字塔原理写作技巧、偏航句用法
│   │   ├── 规范指南/              # 防限流、口播引导话术、自媒体动画、运营沉淀
│   │   └── 品牌资产/品牌资产说明.md
│   ├── 文章/                     # 写作过程中用的模板
│   │   ├── brief-template.md     # 需求卡与角度方案
│   │   ├── 协作文档-template.md   # 作者任务单
│   │   ├── 资料卡-template.md     # 资料卡
│   │   ├── article-template.md   # 文章结构
│   │   ├── review-template.md    # 发布前核验记录
│   │   ├── 口播稿-template.md     # 短视频逐字稿
│   │   ├── art-brief-template.md # 出图说明
│   │   ├── 经历条目-template.md   # 可复用的个人经历
│   │   └── 改稿复盘-template.md   # 改稿复盘报告
│   └── 品牌/                     # 视觉品牌包空白版，create_project.py brand 用
└── scripts/                      # 可选脚本，没有 Python 时手工操作即可
    ├── create_project.py         # 初始化工作台、建品牌目录、新建带日期的项目
    ├── save_article.py           # 发布后把项目移入 历史存档/
    ├── style_learning.py         # 个人规则的只读选择与检查
    ├── analyze_style.py          # 多篇文章的风格统计
    └── visual_assets.py          # 品牌列表、配图台账与图片检查
```

圆圈数字对应 SKILL.md 里的流程步骤：① 接需求 ② 调研 ③ 选角度 ④ 备素材 ⑤ 搭结构 ⑥ 写初稿 ⑦ 打磨四遍 ⑧ 配图 ⑨ 平台改编 ⑩ 发布归档 ⑪ 复盘学习。

## references 和 templates/内容工作台 的分工

- `references/` 是公共操作手册：流程怎么走、调研怎么做、文件怎么放。所有作者都一样，随 Skill 更新。
- `templates/内容工作台/` 是作者可以改的默认内容：人设、写作技巧、平台规范、风格参考。初始化时复制进作者的工作台，之后以工作台里的版本为准，Skill 更新不覆盖。

## 作者的内容工作台

工作台和 Skill 分开存放，结构见 [发布合同](references/流程/发布合同.md)，初始化流程见 [工作台初始化](references/流程/工作台初始化.md)。

```text
python scripts/create_project.py init --workspace "<工作台路径>"
python scripts/create_project.py brand <brand-id> --name "<显示名>"
python scripts/create_project.py new <topic-slug>
python scripts/save_article.py <YYYYMMDD-topic-slug>
```

`init` 会把位置记到 `~/.ai-knowledge/settings.json`，以后的命令不用再传 `--workspace`；也可以用环境变量 `AI_KNOWLEDGE_WORKSPACE` 临时指定。重新运行 `init` 只补缺的文件，已有文件不覆盖。
