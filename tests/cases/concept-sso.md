# Case B — 首个主要生成测试

输入：什么是单点登录（SSO）？请用适合 Java 初学者理解的方式讲解。

执行上下文：按本仓库 Skill 工作流，中文、允许公开资料检索。输出目录显式指定 `examples/concept-sso/`，便于开源展示；不需要业务项目。

预期产物：`article.md`（唯一要发表的文章）、`review.md`（发布前核验记录，不发表）、`assets/`（默认 1 张封面 + 2–4 张解释图的 PNG 与 `manifest.json`，可附可编辑 SVG 源）。不再生成知识笔记、发布稿、复习卡三份草稿。

必须检查：问题驱动开头；认证与登录态分开；两个应用各自建立会话；SSO / OAuth2 / OIDC 不混同；不把 Access Token 当 ID Token；解释图与正文一致，正文不放 Mermaid；文章没有一级标题，标题、摘要、标签写在 frontmatter；正文不出现草稿、核验日期、工作区之类的生产信息。

review.md 检查：六个固定二级标题齐全且按顺序；事实核验表每条结论有类型与依据，协议原理写到规范与章节；写稿者自己写下的结论一律"未核验"，不能自标"已核验"；建议类填"不适用"；配图一节写清每张图要让读者看懂什么及其状态；至少 3 个标题备选。

通过标准：`python tests/validate.py --bundle examples/concept-sso` 与 `visual_assets.py bundle` 通过、关键事实可定位到资料；图片逐张打开核对；教学效果做审读并标明非真人实验。不能只创建空文件或空表格算通过。

变体：用户说"不要图"时只交付 article.md 与 review.md，不建 assets/，review.md 的配图一节写明原因。
