# 用一张人物图建立视觉品牌

把用户给的一张人物图，做成一套可以在写文章、做视频时复用的视觉品牌。产出放在个人配置目录，不进 Skill、当前项目或任何公开仓库。

## 什么时候启动

**两个条件同时满足**才启动：

1. 本次对话里有一张人物或角色图片（附件或明确的文件路径）。
2. 用户明确要求用它建立品牌，例如"用这张图建立视觉品牌""把这张图做成我的个人资产""新建一个 Brand Kit"。

以下情况**不启动**：只发了图没有说要做什么；写文章时附带的截图或素材；"参考这张图的风格配一张图"这类一次性要求；询问图片内容。只有描述没有图片时，请用户发图；图和意图都在但说法含糊时，问一次是否要建立品牌，不要擅自建目录。

## 第 1 步：问三个问题

一次问完，每个都可以跳过：

1. **品牌名字**：显示名和英文 ID（小写字母、数字、连字符，例如 `blue-cat`）。只给显示名时由你拟一个 ID 并告诉用户；完全跳过时用 `brand-YYYYMMDD`。
2. **图片来源**：自己画的、自己用 AI 工具生成的（哪个工具）、约稿或购买的，还是别的。
3. **主要用途**：文章、视频，还是都要。跳过时按"都要"。

来源决定 `licenseStatus`：自己画、自己生成或约稿时已获授权 → `local-only`；来源不明或跳过 → `pending`；用户明确说素材可以公开分发 → `public`。

两种情况要先提醒再继续：

- 图片像知名作品里的角色、别人的 IP 或品牌吉祥物：说明可能有版权问题，`licenseStatus` 只能是 `pending`。
- 图片是真人照片：只有用户说明这是本人并同意时才继续，`licenseStatus` 为 `local-only`；不推断身份，不在任何文件里写真实姓名或个人信息。

## 第 2 步：建目录、放原图

位置：`<个人配置目录>/brands/<brand-id>/`。个人配置目录按 [风格加载](style-loading.md) 的顺序确定；环境变量已设置但目录不存在时，报告给用户，不改用主目录。个人配置目录本身不存在时，可以创建（用户的明确要求就是授权）。

- 同名目录已存在就停下，请用户换名字或改为更新已有品牌；不覆盖。
- 原图**原样复制**到 `assets/canonical/original.png`（JPEG 用 `original.jpg`），不裁切、不压缩、不改色。对话附件往往是临时文件，先复制再做别的。
- 只支持 PNG 和 JPEG；其他格式请用户转换后再发。

```text
<个人配置目录>/brands/<brand-id>/
├── brand-kit.json      # 程序入口：状态、配色、素材清单
├── character.md        # 角色识别点、颜色、场景规则、生图提示词、验收清单
├── style.md            # 定位、配色、两种画面、各类图的做法
├── provenance.md       # 来源、授权、素材清单、版本记录
├── assets/
│   ├── canonical/      # 母版：original，以及确认后的 turnaround、detail
│   └── scenes/         # 确认后的场景图
└── candidates/         # 生成后还没选中的候选，不登记、不使用
```

## 第 3 步：看图写三份规范

**实际查看**原图后，按模板填写：[角色规范](../assets/templates/brand/character.md)、[风格规范](../assets/templates/brand/style.md)、[来源与授权](../assets/templates/brand/provenance.md)。

- 识别点只写看得见的特征。看不清或没画到的部分写"原图未展示"，留给三视图补充。
- 颜色是目测近似值，标明"目测近似值"；用户确认后才改成"用户确认"。
- 定位和介绍文案只用用户说过的话，没有就写"待补充"。不编身份、经历、性格设定或故事。
- 用途不含视频时，删去风格规范里的视频一项。

## 第 4 步：登记并检查

按 [brand-kit 模板](../assets/templates/brand/brand-kit.json) 写 `brand-kit.json`：`status` 为 `draft`，图片 `status` 为 `proposed`，`approval.brandPalette` 为 `proposed`。尺寸和校验值不要手填，用只读检查工具读出来，再检查整套品牌：

```text
python "<skill-dir>/scripts/visual_assets.py" inspect "<品牌目录>"
python "<skill-dir>/scripts/visual_assets.py" kit "<品牌目录>"
```

`kit` 必须通过才算建好。没有 Python 时，用系统自带的 SHA-256 工具算校验值，并告诉用户这一步没有经过检查工具。

## 第 5 步：可选，生成三视图和场景候选

交付草稿时问用户要不要生成。只在生图工具**能接收参考图**时做，并且每次都附上原图；工具做不到就不生成，把提示词留在 character.md，不声称已经锁定角色。

- **三视图**：同一角色的正面、侧面、背面，纯色背景，一张图。
- **场景图**：按用途出 2–3 张，例如讲解、操作电脑、思考；视频用途至少有一张 16:9。

生成结果先放进 `candidates/`，按 character.md 的验收清单逐项检查，明显走样就重新生成，同一张最多重试两次，之后如实报告。把通过检查的候选给用户挑选。被选中的才移到 `assets/canonical/turnaround.png` 或 `assets/scenes/<scene-id>.png`，登记为 `proposed`；三视图同时写进 `identity.turnaround`。然后重跑第 4 步的检查。

## 第 6 步：交付草稿

告诉用户：

- 品牌目录的位置，以及里面有哪些文件和图片。
- 请他重点看 character.md 的"不能变的识别点"和颜色是否准确。
- 现在是草稿：写文章时**不会自动使用**，只有说"用 `<brand-id>` 品牌"时才会用，做出来的图也只能算草稿。
- 满意后说"确认 `<brand-id>`"；配色另外说"配色也确认"。

## 第 7 步：确认

只有用户明确确认时才做：

1. 用户认可的图片 `status` 改为 `confirmed`；`identity` 里的图片必须全部确认，不认可的从 `identity` 移除。
2. `status` 改为 `confirmed`，`kitVersion` 升为 `1.0.0`；用户确认了配色才把 `approval.brandPalette` 改为 `confirmed`，三份规范里的状态同步修改，provenance.md 记一行版本记录。
3. 重跑 `kit` 检查。
4. 设为默认品牌：个人配置目录下还没有 `visual/` 时，把品牌目录整体移到 `visual/`，以后写文章自动使用。已有 `visual/` 时先问用户是否替换；同意后把旧的 `visual/` 移到 `brands/<旧 brandId>/`（目标已存在就停下），再把新品牌移进 `visual/`。不同意就保留原位，按名字选用。

## 以后增补

- **加场景图**：生成或收到新图后放进 `assets/scenes/`，登记为 `proposed`，确认后再改为 `confirmed`，版本号加一个小版本。
- **换母版**：必须用户明确批准；新图用新文件名，不覆盖旧母版，版本号升一个大版本，在 provenance.md 记录原因。
- 查看有哪些品牌：`python "<skill-dir>/scripts/visual_assets.py" list`。
