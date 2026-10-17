# 演示内容工作台（测试夹具）

这是为自动测试编写的合成内容工作台，不属于任何真实作者，也不随 Skill 安装。目录结构与作者初始化后的内容工作台一致，只放测试需要的部分：

- [写作规则](风格参考/我的写作规则.md)：一条已确认、一条候选、一条已停用。
- [写作档案](风格参考/我的写作档案.md)：演示用的范围说明。
- [改稿学习日志](风格参考/改稿学习日志.md)：只记录夹具本身的来历。
- [已确认品牌 demo-brand](品牌资产/demo-brand/brand-kit.json)：最小品牌，含 [角色规范](品牌资产/demo-brand/character.md)、[风格规范](品牌资产/demo-brand/style.md)、[来源与授权](品牌资产/demo-brand/provenance.md)，图片为程序生成的纯色块。
- [草稿品牌 demo-draft](品牌资产/demo-draft/brand-kit.json)：模拟"刚用一张图建立、尚未确认"的品牌，只能按名字选用。

测试通过环境变量 `AI_KNOWLEDGE_WORKSPACE`、`--workspace` 参数或临时主目录下的 `~/.ai-knowledge/settings.json` 指向这个目录的临时副本，不读取真实用户主目录。
