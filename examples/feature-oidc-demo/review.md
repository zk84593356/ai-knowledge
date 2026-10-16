---
title: "OIDC 登录能跑通，为什么还要多传三个随机值？｜发布前核验"
topic: "oidc-login-callback"
type: "review"
mode: "feature"
status: "draft"
created: "2026-10-16"
updated: "2026-10-16"
language: "zh-CN"
---

# OIDC 登录能跑通，为什么还要多传三个随机值？｜发布前核验

本文件只给作者看，不发表。这是 ai-knowledge v0.4.0 的 Feature 模式示范产物，分析对象是仓库内为教学原创的演示工程 `tests/fixtures/oidc-demo/`，不是任何真实系统。

## 发布状态

- 状态：draft。
- 发布前还要做：请新会话或子 Agent 按 editing.md 独立复查下表，尤其是 F12 引用的 RFC 9700 原文；确认配图审美；文末演示代码的位置如需改成可点击链接，换成仓库的公开地址。
- 用户确认记录：尚未确认。

## 事实核验

研究范围：逐行阅读 `tests/fixtures/oidc-demo/login.py`（75 行）和 `tests/test_oidc_demo.py`；2026-10-16 运行 `python -m unittest tests.test_oidc_demo -v`，8 个测试全部通过。测试使用假的身份服务适配器，只证明调用顺序、参数传递和失败分支，不涉及网络、签名或真实身份服务。协议条目按写作者已有知识整理，并通过网页搜索确认了 RFC 9700 和 OpenID Connect Core 1.0 的发布地址；规范全文未在本次会话中逐节打开。

| ID | 结论 | 类型 | 依据 | 核验 |
| --- | --- | --- | --- | --- |
| F01 | OIDC 授权码流程中 state 是推荐参数、nonce 是可选参数，规范不强制传 | 协议原理 | OpenID Connect Core 1.0 第 3.1.2.1 节 | 未核验 |
| F02 | PKCE 是否强制取决于身份服务配置 | 通用知识 | RFC 7636 将 PKCE 定义为扩展；RFC 9700 第 2.1.1 节对不同客户端给出 MUST/RECOMMENDED 的不同要求 | 未核验 |
| F03 | begin 用 secrets.token_urlsafe(32) 生成 state、nonce、verifier，原样存入会话的 pending | 项目事实 | `tests/fixtures/oidc-demo/login.py` 第 46–47 行 | 未核验 |
| F04 | challenge 是 verifier 的 SHA-256 摘要做无填充 Base64URL，请求里声明 S256 | 项目事实 | `login.py` 第 48–50、58–59 行；测试 `test_authorization_request_binds_nonce_state_and_s256` | 未核验 |
| F05 | callback 先 pop 出 pending 再用 compare_digest 比对 state，不通过就在调用适配器之前抛错；同一回调不能用第二次 | 项目事实 | `login.py` 第 63–65 行；测试 `test_wrong_state_stops_before_adapter`、`test_second_browser_cannot_use_first_browser_state`、`test_callback_cannot_be_replayed` | 未核验 |
| F06 | 没有 state 时，攻击者可以把自己的授权码注入受害者的回调，使受害者登录到攻击者账号（登录 CSRF） | 协议原理 | RFC 6749 第 10.12 节；RFC 9700 第 4.7 节 | 未核验 |
| F07 | 身份服务把 nonce 写进 ID Token，客户端必须比对它与请求时的值 | 协议原理 | OpenID Connect Core 1.0 第 3.1.2.1 节（nonce）、第 3.1.3.7 节第 11 步 | 未核验 |
| F08 | 演示把兑换与签名、iss、aud、exp、nonce 校验交给适配器，并明确不实现它 | 项目事实 | `login.py` 第 28–36 行 | 未核验 |
| F09 | ID Token 要验证签名、iss、aud、exp 和 nonce，只解码不验签的内容不可信 | 协议原理 | OpenID Connect Core 1.0 第 3.1.3.7 节 | 未核验 |
| F10 | PKCE 最初针对授权码被拦截（如移动端恶意应用注册相同回调），兑换时必须提交 verifier | 协议原理 | RFC 7636 第 1 节、第 4.5–4.6 节 | 未核验 |
| F11 | 客户端能用 S256 时必须用 S256；plain 方式等于直接发送 verifier | 协议原理 | RFC 7636 第 4.2 节 | 未核验 |
| F12 | RFC 9700 允许在身份服务支持 PKCE 时依靠 PKCE 防 CSRF，并指出 OIDC 的 nonce 也提供 CSRF 防护 | 协议原理 | RFC 9700 第 2.1 节 | 未核验 |
| F13 | 三个随机值都保留，因为检查点分别在客户端回调、身份服务和令牌验证代码 | 建议 | 由 F05、F07、F10 的检查位置推出的作者建议 | 不适用 |
| F14 | iss 与 sub 组合才是可长期依赖的用户标识，邮箱会变也不保证唯一 | 协议原理 | OpenID Connect Core 1.0 第 5.7 节 | 未核验 |
| F15 | 演示保存用户前核对 issuer 和 subject，存下 (issuer, subject)，并在注释中要求真实集成轮换会话 ID | 项目事实 | `login.py` 第 71–74 行；测试 `test_wrong_issuer_or_empty_subject_rejected` | 未核验 |
| F16 | 登录后不更换会话 ID 会导致会话固定攻击 | 通用知识 | OWASP Session Management Cheat Sheet（会话 ID 在权限变化后应更新）；本次未打开 | 未核验 |
| F17 | 演示代码 75 行，配有 8 个用假适配器运行通过的单元测试 | 项目事实 | 2026-10-16 实际运行 `python -m unittest tests.test_oidc_demo -v`：Ran 8 tests，OK | 未核验 |
| F18 | 比较秘密值时用恒定时间比较是好习惯 | 建议 | 通用安全编码建议 | 不适用 |
| F19 | 三个参数都不传，登录很可能照样成功 | 推测 | 由 F01、F02 推出；没有对任何真实身份服务做过测试，正文用了“很可能” | 未核验 |
| F20 | 授权码可能留在浏览器历史或代理日志中 | 通用知识 | RFC 9700 第 4.2 节（经 Referer、浏览器历史等泄露凭据）；本次未打开 | 未核验 |
| F21 | 三个随机值让登录地址多出一百多个字符 | 项目事实 | token_urlsafe(32) 生成 43 个字符；请求里发送 state、nonce、challenge 三个，共 129 个字符 | 未核验 |

## 公开安全过滤

无需过滤：文章只使用仓库内原创的演示代码（MIT 许可）和公开规范。演示里的地址使用保留的 `.example.test` 域名。本文没有使用任何真实公司项目、日志或配置，也没有沿用此前 Java OIDC 验收任务中的任何材料。

## 可补充的个人经历

| 位置 | 建议回答的问题 | 补上后的作用 |
| --- | --- | --- |
| 开头第一段 | 你第一次接统一登录时，有没有漏掉其中某个参数？是怎么发现的？ | 让“最容易被省掉”这句话有亲历证据 |
| “三个值有重叠，为什么都要留着”一节 | 你在项目里用的框架默认生成了哪些值？你是怎么确认的？ | 把通用建议落到读者熟悉的技术栈 |

文章不依赖这些补充也完整成立。补充时只写可以公开的部分，不写公司名、内部类名和尚未修复的问题。

## 配图

| 文件 | 位置 | 让读者看懂什么 | 制作方式 | 状态 |
| --- | --- | --- | --- | --- |
| `assets/cover.png` | 文首 | 文章的问题和三个随机值 | 程序化 SVG（标题加锁的几何示意，无人物），Edge 导出 PNG | generated |
| `assets/oidc-flow.png` | “先看一次完整的登录”一节 | 三个随机值在哪一步生成、经过谁、在哪一步被谁检查 | 程序化 SVG 竖向步骤卡，与正文五步编号一致 | generated |
| `assets/oidc-three-guards.png` | “三个值有重叠，为什么都要留着”一节 | 三个值各自绑定什么、在哪检查、挡住什么 | 程序化 SVG 分组卡片 | generated |

已检查：文件存在并登记在 assets/manifest.json；步骤编号与正文一致；在 390 像素宽度下预览，最小文字可读。人工待查：配图审美。全部为程序化原创图，使用通用配色，未使用个人品牌素材。

## 标题与摘要备选

| 标题 | 取向 |
| --- | --- |
| OIDC 登录能跑通，为什么还要多传三个随机值？ | 问题型 |
| 看懂 OIDC 回调：state、nonce、PKCE 各防哪一种冒充 | 结果型 |
| 登录成功不等于登录安全：回调里最容易省掉的三步 | 反差型 |

选定：OIDC 登录能跑通，为什么还要多传三个随机值？理由：读者正处在“功能已经跑通”的状态，这个问题直接接住他的疑惑；结果型标题信息更全，但三个参数名连在一起，对初学者门槛偏高，适合作为平台摘要或副标题。

摘要：state、nonce、PKCE 各绑定一样东西；少了哪个登录都能成功，所以最容易被省掉。
