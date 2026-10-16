# Case A — 原创演示代码复盘

输入：帮我总结 tests/fixtures/oidc-demo 的 OIDC 登录功能，写一篇《从零理解演示项目里的 OIDC 登录》，面向初学者。

上下文：[该目录](../fixtures/oidc-demo/README.md) 是公开原创演示源码，无真实业务仓库或 Commit 范围。输出到 `examples/feature-oidc-demo/`：`article.md`、`review.md` 与 `assets/`（默认 1 张封面 + 2–4 张解释图，用户说"不要图"时不做）。只读源码；不能把接口合同当作已有密码学实现。

验收：业务问题先于源码；begin/callback/adapter 关系准确；时序或关系图区分浏览器、应用、适配器与真实 IdP 的未实现边界，并导出为 PNG 嵌入文章；准确列出 state/nonce/PKCE；改进建议不冒充已有能力。

review.md 验收：项目事实写到 `tests/fixtures/oidc-demo/login.py` 的符号与行号，且路径和符号真实存在；明确记录未做生产联调、未验签；写稿者的结论保持"未核验"，建议类为"不适用"；公开安全过滤一节说明示例为新构造、没有可删的真实信息时也照实写。

负向重点：FakeAdapter 返回身份不等于签名验证成功；没有 session rotation 就不能宣称防止会话固定；不能把本例说成用户原有项目；文章正文不出现"未核验""草稿"等状态字样，这些只写在 review.md。
