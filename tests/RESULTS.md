# 实际验收记录

## v0.5.0 精简视觉品牌 + 用一张图建立品牌 — 2026-10-16

视觉品牌只认一种格式（brand-kit.json `schemaVersion` "2" + character.md、style.md、provenance.md + assets/），新增建立品牌的说明文档、四个模板，以及检查工具的 `--brand-id`、`list`、`inspect`。

### 实际检查

| 命令/检查 | 本轮结果 |
| --- | --- |
| python -m unittest discover -s tests | 159 项：158 通过、1 跳过（符号链接权限，同前）；新增 test_brand_kit.py 15 项 |
| python tests/validate.py | PASS，0 项发现；新增检查 visual-brand-setup.md、四个品牌模板、草稿品牌夹具 |
| python tests/validate.py --skill skills/ai-knowledge | PASS |
| python tests/validate.py --bundle（两篇示范） | 均 PASS |
| python skills/ai-knowledge/scripts/visual_assets.py bundle（两篇示范） | ok，0 错误 |
| visual_assets.py kit / inspect（两套演示品牌） | ok；inspect 输出与登记一致 |
| node tests/check-mermaid.mjs | 1 图渲染通过 |
| 全仓库文本扫描 | 个人品牌名只出现在 validate.py 的守卫常量里 |

### 本机私有品牌的转换（不在仓库内）

作者本机的默认品牌按新格式转换：旧目录先整体复制到本机 backup 目录并逐文件比对 SHA-256（24 个文件一致）；十几份规范、提示词和模板合并为三份规范，11 张图片字节不变，状态和授权保持原样。转换后 `kit` 检查通过，`context --visual` 自动选中该品牌。

### 没有验证的

- 没有用真实人物图完整走一遍建立流程（三个问题、看图写规范、生成三视图和场景候选、确认）。自动测试只覆盖"模板 + inspect 能拼出一套通过检查的草稿"，看图写出的识别点是否准确、生成的候选是否走样，仍要靠人工判断。
- 没有在 Codex 等其他宿主里实测触发条件（"图片 + 明确要求"）。

## v0.4.0 个人配置移出公开仓库 — 2026-10-16

个人写作规则与视觉品牌改放使用者的个人配置目录（明确路径 → `AI_KNOWLEDGE_PERSONAL` → `~/.ai-knowledge/personal/`），包内 `styles/` 目录、相关历史文档与含角色的示例图片从仓库移除。完整 Git 历史已打包备份在本机私有目录，未推送。

### 实际检查

| 命令/检查 | 本轮结果 |
| --- | --- |
| python -m unittest discover -s tests | 145 项：144 通过、1 跳过（符号链接权限，同前） |
| python tests/validate.py | PASS，0 项发现；新增守卫：skills/ 或 examples/ 出现个人配置标记即报错 |
| python tests/validate.py --bundle（两篇示范） | 均 PASS |
| python skills/ai-knowledge/scripts/visual_assets.py bundle（两篇示范） | ok，0 错误 |
| node tests/check-mermaid.mjs / check-visuals.mjs | 1 图渲染通过；28 次 720/390px 检查通过 |
| 两篇示范配图重生成 | 通用配色、封面无人物，重新导出 PNG，台账哈希/尺寸/rights=public 已更新，390px 预览逐张目视检查 |
| 全仓库文本扫描（排除 .git 与忽略目录） | 无个人配置名称、私人素材路径残留；仅 validate.py 守卫常量与测试夹具按设计包含 |

加载顺序的自动测试覆盖：明确路径 > 环境变量 > 主目录；环境变量失效时不悄悄回退主目录；测试全程用合成夹具与临时主目录，不读真实个人目录。

## v0.4.0：一篇文章 + 发布前核验记录 — 2026-10-16

本轮改动见 [CHANGELOG](../CHANGELOG.md)。没有 Commit、Push 或全局安装。

### 实际检查

| 命令/检查 | 本轮结果 |
| --- | --- |
| python -m unittest discover -s tests | 130 项：129 通过、1 跳过（test_symlink_escape_rejected，Windows 创建符号链接受权限限制，跳过不算通过） |
| python tests/validate.py | PASS，0 项结构/敏感模式发现 |
| python tests/validate.py --bundle examples/concept-sso | PASS |
| python tests/validate.py --bundle examples/feature-oidc-demo | PASS |
| python skills/ai-knowledge/scripts/visual_assets.py bundle（两篇示范） | ok，0 错误 |
| python -m unittest discover -s tests -p test_oidc_demo.py | 8 项通过；OIDC 示范文章引用的行为与此一致 |
| 模拟干净检出：临时索引 git add -A 后 git checkout-index 到临时目录（core.autocrlf=true，Markdown 实际转为 CRLF），在该目录重跑上面四项 Python 检查 | 全部通过；130 个跟踪文件，未改动真实索引 |
| node tests/check-mermaid.mjs | 1 图（docs/architecture.md）实际解析/渲染通过，错误语法负向对照被拒绝 |
| node tests/check-visuals.mjs | 28 次 720/390px 图片解码与文字边界检查通过 |
| git diff --check | 无空白错误 |

环境：Python 3.12.7；Node 24.14.0（Codex 自带，完整路径调用；系统 PATH 中的 Node 12.14.1 无法运行 .mjs 检查）；AI_KNOWLEDGE_NODE_MODULES 指向已有的 playwright 模块；Windows Edge。未安装依赖、字体或 Skill。skill-creator 的 quick_validate.py 本轮未运行。

### 示范文章的人工检查

- 配图：7 张 SVG 用程序生成，经 Edge 导出 2× PNG，并在 390px 宽度下逐张目视检查；修正了 OIDC 封面标题行、标签内边距、步骤编号颜色，删去一处图例。随后改为通用配色、封面去掉人物，全部为程序化原创图并重新导出。审美仍待用户确认，manifest 中为 generated。
- 事实：OIDC 示范的项目事实对照 examples 中的演示代码与单元测试逐条写出行号；协议原理条目的规范原文本轮未能在线取回，证据表中如实标为"未核验"，SSO 示范 F14 标为"存疑"。两篇都未经独立复查。

### 限制

- 校验器只证明两份文件合同、图片台账和有限敏感模式，不能证明事实正确、内容可以公开或文章好读。
- 新流程尚未在真实业务项目（Java OIDC 验收方案）和其他宿主中运行；tests/cases 中的案例本轮未让另一个 Agent 从零重跑，两篇示范由本轮主 Agent 按新流程撰写。

## v0.2.1–v0.3.0 记录（未公开）

这几轮的逐项记录涉及已移出公开仓库的个人写作与视觉配置，以及 v0.4.0 已删除的三稿示例，没有随公开仓库发布。

## v0.2.0 — 2026-10-14

状态：本地实现与开发检查完成，等待用户审阅 SSO 写作效果；未发布、未打标签、未 Git Push。v0.3.0 只保留设计计划。执行者为开发主 Agent，没有独立评测 Agent 或真人读者参与。

### 基线与本轮产物

升级前本地 HEAD 与 GitHub main 均为 `20462ace7dc8da2ceb2e6e06a9d89c110e20c851`，工作区干净；原 24 项测试与结构检查通过。本轮结束时九份 v0.1.0 示例与 HEAD 的内容一致（比较时允许 Git 的 CRLF/LF 转换，另存当前字节 SHA-256）。

新增 SSO 风格版（`examples/concept-sso-style/02-publish-article.md`，v0.4.0 已移除，见 Git 历史） 只改发布文章；其笔记与卡片和基础版本字节相同。[验收对照](../docs/v0.2.0-acceptance.md) 记录 8 项事实清单、实际片段和字符统计。新增 [公开演示档案](../examples/style-profile/writing-profile.md) 来自可迁移技巧与三篇原创模拟语料，不代表用户已确认习惯。

用户提供的 xilo 三篇 Markdown 已完整阅读，执行统计、系统抽样和关键语境复核；只有方法概括、散列与聚合统计进入 [研究记录](../docs/style-research.md)。外部原文、图片和完整报告不入公开仓库。Morry.AI 四篇资料仅检查目录，正文与图片待 v0.3.0 研究。

### 实际命令与自动结果

环境：Python 3.12.7、PyYAML 6.0.2；复用已有 Node 24.19.0、Mermaid 11.12.2、Playwright 1.62.1 和 Edge 155.0.4283.45。没有新增全局依赖或修改系统默认 Node。

| 检查 | 实际命令 / 方式 | 结果与范围 |
| --- | --- | --- |
| 全量单元与负向测试 | `python -m unittest discover -s tests -v` | 44 项通过：原 24 项 + 新 20 项 |
| 结构、包闭包、相对链接和有限敏感模式 | `python tests/validate.py` | PASS，0 项发现，包含新 SSO 三稿 |
| 独立包执行 | 单元测试复制 Skill 到临时目录，从包外运行其统计脚本 | 无仓库外层文件依赖，输出可解析 JSON |
| Skill 格式 | `python -X utf8 <skill-creator目录>/scripts/quick_validate.py skills/ai-knowledge` | Skill is valid |
| 真实资料统计 | `python skills/ai-knowledge/scripts/analyze_style.py <用户提供的xilo.zip> --output tests/.tmp/xilo-style-statistics.json` | 3 篇解码并统计；Agent 阅读与脚本字节读取分别记录 |
| 公开多篇与新旧稿统计 | 使用 analyze() 读取 fixtures/style-corpus 及两个 SSO 发布稿 | 3 篇独立正文；原稿 849、新稿 807 个统计字符，非质量评分 |
| 三模式结构回归 | 原三套及风格 SSO 均由单元测试调用 validate_bundle | 元数据、三稿合同、链接检查通过 |
| 新 Feature / Problem 回归稿 | `python tests/validate.py --bundle tests/.tmp/v02-behavior/feature-oidc --expected-date 2026-10-14`；Problem 使用同级 problem-cf-pages | 两套各三稿，均 0 项发现 |
| 英文离线与路径冲突 | 主 Agent 原创机会成本三稿；两次排他写入，同名目录存在时递增目录；调用 validate_bundle | 两套通过，第一次三文件 SHA-256 未变 |
| Mermaid | 用已有隔离 Node 执行 `tests/check-mermaid.mjs`，设置 AI_KNOWLEDGE_NODE_MODULES 指向已有 Playwright | 6 图解析及本地 SVG/PNG 渲染通过；故意错误图被拒绝 |
| 差异空白 | `git -c safe.directory=<本仓库> diff --check` | 无空白错误；Git 提示未来可能转换 LF/CRLF，未改变全局配置 |

本轮没有重新执行安装器发现命令，也没有全局安装。此前 CLI 发现的结果保留在下方 v0.1.0 历史记录，不能当作本轮安装验收。

### 三个案例与边界的实际回归

Concept 使用新 SSO 文章，按 F01–F08 逐项对照旧稿与协议依据；没有删掉会话条件、令牌区别和登出边界。Feature 重读演示源码，重新生成三稿，明确适配器只有合同、替身测试不等于真实验签。Problem 重读 F1/C1/L1/A1/L2，重新生成三稿，只确认模拟记录的构建恢复，不宣称上线。

Feature / Problem 的新稿与原有边界响应保存在被忽略的 `tests/.tmp/v02-behavior/`；原公开样例不覆盖。主 Agent 同时生成了英文机会成本三稿，并将同一组已审稿件写入两次来检查目录冲突，第二次使用日期序号目录。这是本次执行行为，不是独立生成器或并发安全证明。

按 [旧边界](cases/boundaries.md) 与 [新风格边界](cases/style-engine.md) 完成如下内容走查，实际响应存于该临时目录的 decisions.md：

- 仅 L1 不宣布唯一根因；缺 L2 不宣布恢复；空源码不编造实现。
- 离线新功能标注未核实，非技术英文不强塞源码章节。
- 资料提示词不成为执行授权，私有材料不进入公开稿。
- 跳过经历仍生成 SSO；外部作者经历不改成用户自述。
- “改配置仍失败”的模拟回答不补出成功；公开范围未知不保存真实用户条目。
- 冲突规则不能移除事实限定；只分析风格不强制三稿；临时偏好不永久改档案。
- 无 Python 的模拟约束下手工观察，不填写自动统计数字；机器未实际卸载 Python。

这是主 Agent 的开发走查，不是独立对抗评测。真实用户确认习惯、经历授权与多轮长期档案更新尚无真人验收。显式更新保留人工段落、宿主并发写入/符号链接逃逸/中断恢复仍未新增端到端测试。

### 内容审读与视觉回归

SSO 新稿从一次具体跳转展开，开头就标明假设，流程、令牌、权限分节衔接。新稿少 42 个统计字符，但平均句长略增；不以“更短”证明“更好”。审读认为本篇主线更集中，用户偏好与真人复述效果待确认。

打开并检查 SSO、OIDC、Pages 三个案例的实际 PNG：标签可读，SSO 的两应用会话、OIDC 的互斥成功/失败分支和 Pages 的另行部署验证与正文一致；Pages 节点仍有自动换行，不作为新品牌视觉样例。新增 SSO 图是原图随笔记复制，因此渲染总数从 5 增为 6，不是 v0.3.0 新制配图。

### 本轮发现、修复与限制

1. Windows 文本写入默认 CRLF，导致测试中 ZIP 与目录输入的原始字节散列不同；修正夹具使用明确 LF，语义统计本来一致。
2. Windows ZipInfo 在读写时规范化反斜杠；负向测试发现仅检查 filename 会漏检原始路径形式。工具改为同时检查 orig_filename 和 filename，保留真实恶意路径夹具，重跑 44 项通过。
3. 排除只有标题/引用的空正文，避免把它计成第二篇独立文章；对应功能测试通过。
4. 新文档未写完时链接检查如实报告两处缺失；补齐研究与验收说明后全仓检查为 0 项发现。

统计使用有限 Markdown 启发式，不是完整语法解析或中文分词；行内引语、复杂引用、主题词归属仍要全文复核。去重只识别规范化后相同的正文，不能识别所有改写/转载。脚本不推断人格，不评分“AI 味”，也不能证明内容没有抄袭。

当前具备 v0.2.0 用户验收条件，未获得用户对写作效果或个人品牌方向的确认。v0.3.0 的四类视觉样例、品牌规范和资产检查尚未实现，不能把现有 Mermaid 回归当作视觉引擎验收。

## v0.1.0 历史记录（保留）

以下为首次开发时的记录；其中“尚未发布”等描述指当时状态，本轮状态以上文为准。

执行日期：2026-10-14（Asia/Shanghai）。执行者：本次开发主 Agent。没有独立评测 Agent 或真人读者参与，因此内容审读不是盲测，不能据此保证所有初学者都能学会。

### 环境与操作范围

- Windows；Python 3.12.7，PyYAML 6.0.2。
- 默认 Node 12.14.1 不满足测试安装器要求；测试改用机器已有的隔离 Node 24.19.0，未切换系统默认版本。
- skills CLI 1.7.2 与 Mermaid 11.12.2 仅下载到被忽略的 `.test-tools/`；关闭依赖安装脚本。Playwright 1.62.1 使用机器已有模块，浏览器使用本地 Edge。
- 最初 npm 镜像请求因网络访问限制失败；随后针对官方 npm registry 的项目内测试依赖下载成功。未全局安装或更新任何 Skill，没有部署、发布、推送或上传私人材料。

### 已执行的生成工作流

顺序为 Concept SSO → Feature OIDC → Problem Pages。主 Agent 读取本项目 Skill 与对应指南，整理证据和教学路径，在当前会话中生成正文并写入指定 examples 目录。没有另启一个已安装 Skill 的宿主会话，也没有自动调用模型 API。

| 案例 | 输入证据 | 产物 | 结果及边界 |
| --- | --- | --- | --- |
| B：SSO，首个主要测试 | 官方 OIDC Core 与 RFC 6749，Java 初学者问题 | examples/concept-sso 下三文件 | 已生成、结构核对与内容审读；采用假设 OA/CRM 场景，没有真实服务器 |
| A：OIDC | 原创 tests/fixtures/oidc-demo 源码 | examples/feature-oidc 下三文件 | 已分析真实存在的演示代码；引用符号可查；没有生产源码或真实协议联调 |
| C：Pages | 固定模拟 F1/C1/L1/A1/L2 | examples/problem-cf-pages 下三文件 | 已分析并生成；限定“记录显示构建恢复”，没有捏造发布验证 |

三份稿件分别组织叙事，未把文章当作笔记删减版。SSO 以重复登录建立直觉，文章以“另一个网站凭什么认识你”展开，卡片用应用会话与 IdP 会话的区别进行提取练习。

### 自动检查与实际命令

| 检查 | 实际命令/方式 | 结果 |
| --- | --- | --- |
| 单元与负向测试 | `python -m unittest discover -s tests -v` | 24 项通过：8 项 OIDC 编排测试、16 项校验器测试 |
| 全仓结构与有限敏感模式 | `python tests/validate.py` | 0 项发现；不能视为全面隐私保证 |
| 三个案例元数据与链接 | 对三个目录运行 validate_bundle，传入生成日期 2026-10-14 | 三套均无结构问题；卡片正文均短于笔记的 60% |
| skill-creator 验证 | `python -X utf8 <skill-creator目录>/scripts/quick_validate.py skills/ai-knowledge` | Skill is valid |
| 安装包资源闭包 | 复制 Skill 到临时目录，仅验证该目录；再删去必要参考文件做负向测试 | 完整包通过，缺失资源被拒绝 |
| CLI 发现 | 隔离 Node 执行 `.test-tools/node_modules/skills/bin/cli.mjs add . --list` | Found 1 skill：ai-knowledge；只列出，没有安装 |
| Mermaid | 隔离 Node 执行 `tests/check-mermaid.mjs` | 5 个图解析并渲染为本地 SVG/PNG；故意错误图被拒绝 |

Mermaid 图位于架构、SSO 笔记、OIDC 笔记、Pages 笔记及图解指南。主 Agent 打开三个案例的图片做了视觉检查，并逐箭头对照正文。PNG/SVG 和工具日志是开发临时产物，位于被忽略的 `tests/.tmp/mermaid/`，不成为运行资源。

### 已执行的边界冒烟测试

按 Skill 指令，在 `tests/.tmp/behavior-project/` 这一隔离模拟项目中，以英文、concise、离线方式解释“机会成本”，生成三个文件，然后再次生成同主题。

- 第一次输出到模拟项目的 `docs/knowledge/opportunity-cost/`。
- 第二次输出到 `docs/knowledge/opportunity-cost-20261014-02/`。
- 两组均通过结构检查；第一组三文件 SHA-256 前后完全一致。
- 内容未强加源码章节，明确本轮没有联网检索，没有假引用。
- 实际路径与散列记录保存在 `tests/.tmp/behavior-project/result.json`。

这是本次主 Agent 按规则执行的冒烟验证，不是一个运行时输出脚本的单元测试，也不是所有宿主的冲突安全保证。独立宿主的并发冲突、符号链接边界及中断恢复尚未实测。

另对以下输入做了桌面内容走查（不是完整落盘生成或自动通过）：仅 L1 时只确认文件读取失败；去掉 L2 时不确认构建恢复；日志中的上传指令不获得执行权。完整可重跑输入和判据见 [边界用例](cases/boundaries.md)。

### 十项内容审读：具体依据而非总分

| 标准 | 复核依据与本次判断 | 限制 |
| --- | --- | --- |
| 事实与证据 | SSO 区分授权/认证；OIDC 接口合同不冒充实现；Pages 每项结论映射记录编号 | 关键定义经来源复核；不是完整安全审计 |
| 初学者理解 | SSO 先解释认证、登录态、授权；源码前先讲业务问题 | 编辑审读可接受，真人效果未验证 |
| 循序渐进 | 三篇笔记均由场景进入机制，再进入细节或证据 | 模型审读，不是盲测 |
| 核心原理 | SSO 解释复用 IdP 会话；OIDC 解释请求绑定；Pages 连接执行目录与文件查找 | 案例限定范围内成立 |
| 实例完整 | OA/CRM 走完整主线；OIDC 真实演示符号；Pages 固定模拟记录 | 均没有伪装真实业务经历 |
| 图解有效 | 5 图实际渲染；OIDC 修复互斥分支；三个案例图已视觉审读 | 不等于所有 Obsidian 版本均实测 |
| 表达自然 | 发布稿各有独立疑问和论证顺序，无编造第一人称经历 | 主观编辑意见 |
| 信息密度 | 卡片正文均明显更短；文章没有照搬笔记的证据表与工程列表 | 长度不能单独证明好读 |
| Markdown / Obsidian | YAML、链接、日期、围栏与三文件一致性检查 | 未启动 Obsidian 做客户端验收 |
| 长期复习 | 四个要点、混淆、迁移问答、关键经验与快速回顾 | 半年后的记忆效果无法在本轮验证 |

### 本次发现与修复

1. 首轮校验脚本生成时出现重复 raw-string 前缀，导致语法错误；已修复并重跑全部 24 项测试。此错误属于开发检查工具，不是 Skill 输出逻辑。
2. OIDC 时序图原先把“返回 Identity 或异常”放在成功写入之前，易使读者误读异常也会继续。已增加互斥分支，并将此约束加入通用图解指南；三个案例重新结构检查，全部图重新渲染。
3. 开发阶段 Feature 笔记引用尚未创建的验收报告，链接检查准确报错；报告完成后再跑全仓链接检查。

### 尚未验证与原因

- 真实 OIDC 项目、指定 Commit/范围与真实 IdP 集成：未提供业务代码和可用服务；演示不能代替。
- Cloudflare 云端构建与访问：任务明确采用模拟记录，没有执行部署。
- Codex 全局安装后的发现与调用、其他 Agent 完整执行：未执行用户级安装，也未启动这些宿主；已核对标准与 CLI 发现。
- GitHub 安装和更新：尚未发布远程仓库；未全局更新。
- 并发写入、符号链接逃逸、无权限和显式更新保留人工段落：有执行规则/判据，但没有独立宿主行为验收。
- 网络受限的新版本问题、提示注入与敏感输入：已有规则和内容走查，尚无独立对抗评测。
- 真人教学效果、长期复习效果：需要真实读者及后续时间窗口，不能以自评分代替。

下一步优先引入一个授权可读的真实项目，保留输入快照和期望事实清单，并邀请初学者做复述与迁移题。增加宿主兼容测试时继续保留“格式兼容”与“实测执行”的区别。
