# Windows 与跨项目安装

以下命令供用户选择执行。安装或更新用户级 Skill 会影响全局环境；本项目开发不会替用户执行这些操作。

## 前提

安装器需要 Node.js 与 npm/npx；[skills CLI 当前主分支](https://github.com/vercel-labs/skills/blob/main/package.json) 的 Node 要求为 >=22.20.0（2026-10-14 核实）。请按实际安装包要求选择受支持版本。基础 Skill 由 Markdown 指令与模板组成，不需要 Node、Python、API Key 或 Obsidian 插件。v0.2.0 包含可选的本地风格统计脚本，仅运行该脚本时需 Python 3.10+ 标准库；没有 Python 可手工分析，不影响写文章。配图依赖宿主的生图或浏览器渲染能力；没有时 Skill 会做程序化图解或把图记为待制作项。

在 PowerShell 中先检查 `node --version` 与 `npx skills --help`。如果策略阻止 npx.ps1，可使用 `npx.cmd`；不要为此关闭整机执行策略。路径含空格时加引号。

## 从本地仓库发现与全局安装

进入本仓库根目录，然后运行：

```powershell
npx skills add . --list
npx skills add . -g -a codex -s ai-knowledge
npx skills ls -g
```

第一条只列出可发现的 Skill；第二条是你选择执行的全局安装。Windows 链接权限受限时可在安装命令后增加 `--copy`。请查看 CLI 返回的实际安装位置。

## 项目级安装

在需要使用的目标项目中运行，用本仓库实际路径替换示例：

```powershell
npx skills add "C:\work\ai-knowledge" -a codex -s ai-knowledge
```

不带 `-g` 即为项目级。不要在本仓库另外维护 `.agents/skills/ai-knowledge/SKILL.md` 副本；这里的 `skills/ai-knowledge/` 是唯一源码。

## GitHub 发布后安装与更新

将 `<owner>` 换成实际 GitHub 所有者；以下用于已发布版本；尚未提交/推送的本地改动不能通过远程更新取得。

```powershell
npx skills add <owner>/ai-knowledge -g -a codex -s ai-knowledge
npx skills update ai-knowledge -g
npx skills ls -g
```

选择更新单个技能；不要省略名称而意外更新全部。CLI 跟踪远程来源时才能从远程获取更新；本地路径安装遇到不可更新提示时，先确认源文件，再通过安装器重新选择安装；不要直接覆盖含个人修改的安装副本。

## 无 npm 的手动安装

[Codex 官方技能文档](https://developers.openai.com/codex/skills/) 列出项目级 `.agents/skills` 和用户级 `~/.agents/skills`。手动将完整 `skills/ai-knowledge` 文件夹复制到选定范围的技能目录，保留 references、assets 和 LICENSE。

Windows 用户级目标可用 `Join-Path $HOME '.agents\skills\ai-knowledge'` 表达。先检查是否存在；已存在时先比较并保留原目录，不能静默覆盖。某些旧版本仍使用 `.codex/skills`，优先依据实际宿主文档与 CLI 输出，不同时安装重复名称。通常会自动发现；未出现时重新打开 Codex 或新建会话。

## 在其他项目使用

全局安装后，在 OIDC 项目、新建的空项目或其他工作目录中打开 Codex，输入 `$ai-knowledge` 加任务描述即可。分析上下文始终是当前项目，默认输出也在当前项目的 `docs/knowledge/`，不会写回安装目录。

Claude Code、Cursor、OpenCode 可用同一安装源，并按 CLI 支持的 `-a claude-code`、`-a cursor`、`-a opencode` 指定宿主。调用入口以各宿主实际 UI 为准。本版不声称已在这些宿主实测。

## 常见问题

- 找不到技能：先 `npx skills add . --list` 检查源码可发现性，再检查安装范围与是否整目录安装。
- 安装器报语法或引擎错误：核对 Node 版本。不要把安装器的运行要求误当作 Skill 的依赖。
- 网络不可用：使用手动整目录复制，不假称在线安装已成功。
- 更新未显示：检查重复名称、禁用配置和宿主扫描路径，再重开会话。
- 生成目标已存在：默认新建日期序号目录，旧文件保持原样。

## 个人配置目录

个人写作规则和视觉品牌不在 Skill 里，安装和更新 Skill 都不会碰它们。Skill 按顺序查找：请求里明确给出的路径 → 环境变量 `AI_KNOWLEDGE_PERSONAL` → `%USERPROFILE%\.ai-knowledge\personal\`。都没有时用公共写作技法和通用图解。默认视觉品牌在其中的 `visual\`，其他品牌在 `brands\<brand-id>\`。

## 内容工作台（v0.7.0 起，可选）

工作台是放用户人设、风格参考、写作技巧和各平台稿件的目录，同样不在 Skill 里。查找顺序：请求里给出的路径 → 环境变量 `AI_KNOWLEDGE_WORKSPACE` → 个人配置目录 `settings.json` 的 `workspace` 字段。都没有时，文章照旧写到当前项目的 `docs/knowledge/<slug>/`。建一个空工作台：

```powershell
python skills/ai-knowledge/scripts/create_project.py init --workspace D:\内容工作台
```

目录结构见 [发布合同](../skills/ai-knowledge/references/发布合同.md) 的"内容工作台"一节。

## 从 v0.6.0 升级到 v0.7.0

- 内容类型由功能/知识/踩坑三种改为讲解 `explainer`、复盘 `retrospective`、测评 `evaluation`、观点 `opinion` 四种。旧文章 frontmatter 里的 `concept`、`feature`、`problem` 不会自动转换；用 `validate.py --bundle` 检查旧稿会报模式无效，需要时手动改成新值（concept → explainer，feature/problem → retrospective）。
- Skill 内的参考文档改为中文文件名，模板从 `assets/templates/` 移到 `templates/`，文件名加 `-template`。自己写过指向旧路径的链接或脚本要跟着改。
- 个人配置目录和视觉品牌格式不变，不用转换。
- 不建工作台也能照旧使用；要用工作台见上一节。

## 从 v0.5.0 升级到 v0.6.0

格式兼容，已有品牌不用转换，`kit` 检查照常通过。新版 style.md 模板多了"视觉语言"和"风格样板"两节；旧品牌没有这两节时，配图按美术方向的通用公式做。想补上时，可以让助手按模板起草视觉语言提案，再做一次四图测试。品牌图片新增 `sample` 角色（`assets/samples/`），用于登记风格样板。

## 从 v0.4.0 升级到 v0.5.0

v0.5.0 的视觉品牌只认精简格式（`brand-kit.json` 的 `schemaVersion` 为 `"2"`，外加 character.md、style.md、provenance.md）。旧格式的品牌会被当作无效，回退通用图解，不会报错中断写作。转换方法：先把旧品牌目录整体备份，再按 `skills/ai-knowledge/templates/brand/` 的四个模板合并原来的规范文件，图片原样保留，最后运行 `python skills/ai-knowledge/scripts/visual_assets.py kit <品牌目录>` 确认通过。也可以直接让助手按 [建立视觉品牌](../skills/ai-knowledge/references/视觉-建立品牌.md) 的格式转换。

要在多台电脑上使用同一份配置，可以把个人目录放进私有 Git 仓库，在每台电脑上克隆后设置用户级环境变量，重开终端和 Agent 生效：

```powershell
[Environment]::SetEnvironmentVariable('AI_KNOWLEDGE_PERSONAL', 'D:\private\my-style', 'User')
```

风格学习写回这个目录，下次调用即生效，不需要重装 Skill。不要把个人目录放进 Skill 安装目录或本仓库；仓库校验器会把 skills/ 下出现的 `styles/personal` 视为错误。

## 从 v0.3.0 升级到 v0.4.0

v0.4.0 把三稿合同改成 article.md 加 review.md，并删除了旧的 writing-style.md、teaching-principles.md、quality-checklist.md、diagram-guide.md 和四个三稿模板，个人配置也移出了 Skill（原来的 `styles/` 目录不再存在）。复制安装时直接覆盖会留下这些旧文件，旧副本里的个人配置还会继续躺在安装目录；新版 SKILL.md 不再引用它们，但宿主或你自己可能误读。建议先把旧安装目录改名备份（其中可能有个人修改），再整目录安装新版，确认新版能正常使用后再删除备份。

升级后在其他项目里试一次"什么是 SSO？"，确认产出是 `docs/knowledge/sso/` 下的 article.md、review.md 和 assets/，而不是三份编号稿件。已经生成的旧三稿不需要迁移，它们仍是普通 Markdown。

## 刷新已有安装副本（Windows）

不能仅看版本号判断安装副本是否最新：同一版本号下也可能改过规则。运行源码本身无需重装；复制安装或指向安装器缓存副本的链接需要从本地源刷新。仅当实际链接目标就是当前源码目录时，文件变化才直接可见。skills CLI 的 Symlink 模式可能链接到其 canonical 安装副本，并不保证链接到 Git 源码。

在其他项目调用前，可由用户在 PowerShell 执行：

~~~powershell
Set-Location 'C:\develop\workspaces\ai-knowledge'
npx.cmd skills@1.7.2 ls -g
npx.cmd skills@1.7.2 add . --list
npx.cmd skills@1.7.2 add . -g -a codex -s ai-knowledge
npx.cmd skills@1.7.2 ls -g
~~~

参数按 skills 1.7.2 README 核对（2026-10-15）；npx 可能按需下载该版本。安装保留交互确认，先查看实际目标；若发现旧副本有个人修改，先比较并另存再更新，不能静默覆盖。Windows 无链接权限时可为 add 命令追加 --copy。复制完整 Skill 目录，不能只复制入口或这一份规范。

按安装器输出确认实际目录后，比较入口文件散列；以下 installedSkill 要替换为真实安装路径，不假定目标：

~~~powershell
$sourceSkill = 'C:\develop\workspaces\ai-knowledge\skills\ai-knowledge'
$installedSkill = Read-Host '输入安装器显示的 ai-knowledge 完整目录'
Get-Item -LiteralPath $installedSkill | Select-Object FullName,LinkType,Target
Get-FileHash -LiteralPath (Join-Path $sourceSkill 'SKILL.md') -Algorithm SHA256
Get-FileHash -LiteralPath (Join-Path $installedSkill 'SKILL.md') -Algorithm SHA256
~~~

散列不同需先检查安装来源/副本和换行转换，不用远程 update 获取未推送的本地改动。[Codex 官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)说明支持链接目录并自动检测技能变化；更新未出现时重启 Codex。新会话中从实际安装位置核对 SKILL.md 的 version，再试写一篇文章，不在此源码仓库创建第二份入口。
