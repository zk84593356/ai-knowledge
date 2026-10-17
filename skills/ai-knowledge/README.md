# ai-knowledge Skill 目录说明

本文件给维护者和想了解 Skill 内部结构的作者看，Agent 运行时从 [SKILL.md](SKILL.md) 进入，按流程节点按需加载下面的文件。

```text
ai-knowledge/
├── SKILL.md                      # 入口：11 步内容创作流程、四种内容类型、三种协作强度
├── README.md                     # 本文件
├── LICENSE
├── references/                   # 参考资料，按流程节点按需加载
│   ├── 发布合同.md                # 工作台目录、文件名、frontmatter、review.md 结构
│   ├── 用户人设-快速参考.md        # ① 怎么读工作台的 用户人设.md
│   ├── 调研-讲解.md               # ② 讲解类调研
│   ├── 调研-复盘功能.md            # ② 功能复盘调研
│   ├── 调研-复盘故障.md            # ② 故障复盘调研
│   ├── 调研-测评.md               # ② 测评：测试设计、记录、利益披露
│   ├── 调研-观点.md               # ② 观点：事实与判断、反方、论证漏洞
│   ├── 调研-资料卡.md             # ② 资料卡的存放、有效期和复用
│   ├── 选题与角度.md              # ③ 角度方案、核心判断、选题库
│   ├── 协作文档与真实经历.md       # ④ 作者任务单与经历采集
│   ├── 写作技巧-金字塔原理.md      # ⑤ 结论先行、分组、SCQA、小标题
│   ├── 内容写作技巧.md            # ⑥ 读者、标题、开头、段落、版式
│   ├── 偏航句用法.md              # ⑥ 制造转折和信息缺口
│   ├── 风格-加载.md               # ⑥ 个人配置与工作台风格资料的加载顺序
│   ├── 风格-应用.md               # ⑥ 在事实稳定后应用个人规则
│   ├── 打磨与核验.md              # ⑦ 四遍打磨、阻断项、独立复查
│   ├── 降AI味指南.md              # ⑦ 文字遍：AI 味模式与改法
│   ├── 自媒体防限流指南.md         # ⑦⑨ 平台规则、AI 标识、广告标识
│   ├── 视觉-品牌加载.md           # ⑧ 选用视觉品牌
│   ├── 视觉-美术方向.md           # ⑧ 统一整组配图风格
│   ├── 视觉-配图验收.md           # ⑧ 制作、导出、manifest.json 与检查
│   ├── 视觉-建立品牌.md           # 按需：用一张角色图建立视觉品牌
│   ├── 平台改编.md               # ⑨ 小红书、微博、X、短视频口播
│   ├── 口播引导话术.md            # ⑨ 开头钩子、中段提示、合规结尾
│   ├── 自媒体动画.md              # ⑨ 口播稿的画面与动效
│   ├── 运营沉淀.md               # ⑪ 发布数据的记录、比较和写回
│   ├── 风格-改稿复盘.md           # ⑪ 对比 AI 稿和作者发出的版本
│   ├── 风格-分析.md               # ⑪ 从多篇文章分析风格
│   └── 风格-写回.md               # ⑪ 把确认的习惯写回个人规则
├── templates/                    # 模板
│   ├── brief-template.md         # 需求卡与角度方案
│   ├── 协作文档-template.md       # 作者任务单
│   ├── 资料卡-template.md         # 资料卡
│   ├── 用户人设-template.md       # 工作台的 用户人设.md 空白版
│   ├── article-template.md       # 文章结构
│   ├── review-template.md        # 发布前核验记录
│   ├── 口播稿-template.md         # 短视频逐字稿
│   ├── art-brief-template.md     # 出图说明
│   ├── 经历条目-template.md       # 可复用的个人经历
│   ├── 改稿复盘-template.md       # 改稿复盘报告
│   ├── writing-rules-template.md # 个人写作规则
│   ├── writing-profile-template.md # 个人写作档案
│   └── brand/                    # 视觉品牌包空白版
└── scripts/                      # 可选脚本，没有 Python 时手工操作即可
    ├── create_project.py         # 建工作台目录、新建带日期的项目和需求卡
    ├── save_article.py           # 发布后把项目移入 历史存档/
    ├── style_learning.py         # 个人规则的只读选择与检查
    ├── analyze_style.py          # 多篇文章的风格统计
    └── visual_assets.py          # 配图台账与图片检查
```

圆圈数字对应 SKILL.md 里的流程步骤：① 接需求 ② 调研 ③ 选角度 ④ 备素材 ⑤ 搭结构 ⑥ 写初稿 ⑦ 打磨四遍 ⑧ 配图 ⑨ 平台改编 ⑩ 发布归档 ⑪ 复盘学习。

## 作者的内容工作台

工作台由作者自己建，和 Skill 分开存放，结构见 [发布合同](references/发布合同.md)。可以用脚本建好空目录：

```text
python scripts/create_project.py init --workspace "<工作台路径>"
python scripts/create_project.py new <topic-slug> --workspace "<工作台路径>"
python scripts/save_article.py <YYYYMMDD-topic-slug> --workspace "<工作台路径>"
```

设置环境变量 `AI_KNOWLEDGE_WORKSPACE`，或在个人配置目录的 `settings.json` 里写 `{"workspace": "<工作台路径>"}`，以后就不用每次传 `--workspace`。

工作台根目录的 `用户人设.md`、`风格参考/`、`写作技巧/`、`规范指南/` 由作者维护，优先于本 Skill 的通用资料。`规范指南/` 适合放作者自己更新过的防限流、口播话术、运营沉淀等版本；本 Skill 的同名参考是公开的通用版本。
