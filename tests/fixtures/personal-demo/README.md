# 演示个人配置（测试夹具）

这是为自动测试编写的合成个人配置，不属于任何真实作者，也不随 Skill 安装。目录结构与用户本地的个人配置根目录一致：

- [写作规则](writing-rules.md)：一条已确认、一条候选、一条已停用。
- [写作档案](writing-profile.md)：演示用的范围说明。
- [学习记录](learning-log.md)：只记录夹具本身的来历。
- [默认视觉品牌](visual/brand-kit.json)：已确认的最小品牌，含 [角色规范](visual/character.md)、[风格规范](visual/style.md)、[来源与授权](visual/provenance.md)，图片为程序生成的纯色块。
- [草稿品牌](brands/demo-draft/brand-kit.json)：模拟"刚用一张图建立、尚未确认"的品牌，只能按名字选用。

测试通过环境变量 `AI_KNOWLEDGE_PERSONAL` 或显式参数指向这个目录的临时副本，不读取真实用户主目录。
