# 原创 OIDC 流程演示

本目录是用于教学复盘测试的最小 Python 工程，标准库即可运行单元测试。它不是完整 OIDC 实现，也不是可部署的认证服务。

业务目标：网站借助统一身份服务确认用户身份，再保存本地用户状态。`LoginFlow.begin` 生成绑定参数和授权 URL；`callback` 检查 state、一次性消费 pending，调用适配器，再保存 `(issuer, subject)`。

`OidcAdapter.exchange_and_validate` 只定义接口合同。网络交换、ID Token 签名/issuer/audience/时效/nonce 验证由真实适配器承担，本目录没有实现它。测试里的 FakeAdapter 只证明调用顺序、参数和失败传播，不能证明协议安全。

HTTP 路由、Cookie 标志、Session ID 轮换、并发登录、pending 超时、远程身份服务与单点登出都没有实现。源码中的 `.example.test` 地址专用于示意，不是真实服务。

运行仓库测试：`python -m unittest discover -s tests -v`。源码为本项目原创，采用仓库 MIT 许可。
