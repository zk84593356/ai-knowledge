"""Synthetic article.md + review.md topic bundles for contract tests; not subject evidence."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

ARTICLE_META = dict(title="会话为什么能跨应用", topic="topic", type="article", mode="concept",
                    summary="用两次跳转讲清登录态从哪里来", tags=["登录", "会话"],
                    created="2026-10-14", updated="2026-10-14", language="zh-CN")
ARTICLE_BODY = """![封面：两个应用共用一次登录](./assets/cover.png)

开头先讲读者遇到的问题。

## 两个应用各有会话

应用各自建立会话，认证中心只负责确认身份。

![关系图：浏览器、应用与认证中心](./assets/flow.png)

```text
# 代码块里的井号不是标题
```

## 参考

- 示例规范：https://example.com/spec
"""
REVIEW_META = dict(title="会话为什么能跨应用｜发布前核验", topic="topic", type="review", mode="concept",
                   status="draft", created="2026-10-14", updated="2026-10-14", language="zh-CN")
REVIEW_BODY = """# 会话为什么能跨应用｜发布前核验

## 发布状态

当前为 draft，用户尚未确认发布。

## 事实核验

| ID | 结论 | 类型 | 依据 | 核验 |
| --- | --- | --- | --- | --- |
| C1 | 应用各自建立会话 | 协议原理 | 示例规范第 3 节 | 未核验 |
| C2 | 认证中心只确认身份 | 通用知识 | 示例教材 | 已核验 |
| S1 | 登出时同时清理应用会话 | 建议 | 无 | 不适用 |

## 公开安全过滤

无真实系统信息，示例为新构造。

## 可补充的个人经历

无。

## 配图

| 文件 | 位置 | 状态 |
| --- | --- | --- |
| ./assets/cover.png | 开头 | generated |
| ./assets/flow.png | 第一节 | generated |

## 标题与摘要备选

1. 会话为什么能跨应用：直接回答问题。
2. 一次登录背后的两次跳转：强调过程。
3. 登录态从哪里来：面向初学者。

选定第 1 个。
"""
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="3">'
       '<rect width="4" height="3" fill="#fff"/></svg>')


def png_bytes(width=4, height=3, shade=255):
    """Smallest valid RGB PNG with real IHDR/IDAT/IEND chunks."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    rows = b"".join(b"\x00" + bytes([shade, shade, shade]) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def document(meta, body):
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in meta.items()]
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body


def asset_record(folder, asset_id, name, kind="infographic", status="generated"):
    data = (Path(folder) / "assets" / name).read_bytes()
    width, height = (4, 3)
    return dict(id=asset_id, type=kind, path="./assets/" + name, status=status,
                source="synthetic contract test", method="generated in test", references=[],
                width=width, height=height, sha256=hashlib.sha256(data).hexdigest(),
                review=dict(identity="na", knowledge="pass", readability="pass",
                            rights="local-only", aesthetic="pending"))


def manifest(assets, **overrides):
    value = dict(schemaVersion="1", brandId="generic", kitVersion="none", paletteStatus="none",
                 batch="test-only", status="draft", assets=assets)
    value.update(overrides)
    return value


def write_bundle(folder, images=True):
    """Write a valid two-file bundle; with images, add two PNGs, one editable SVG and a manifest."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    body = ARTICLE_BODY
    if not images:
        body = "\n".join(line for line in body.splitlines() if not line.startswith("![")) + "\n"
    (folder / "article.md").write_text(document(ARTICLE_META, body), encoding="utf-8")
    (folder / "review.md").write_text(document(REVIEW_META, REVIEW_BODY), encoding="utf-8")
    if images:
        assets = folder / "assets"
        assets.mkdir()
        (assets / "cover.png").write_bytes(png_bytes(shade=250))
        (assets / "flow.png").write_bytes(png_bytes(shade=200))
        (assets / "cover.svg").write_text(SVG, encoding="utf-8")
        records = [asset_record(folder, "cover", "cover.png", "cover"),
                   asset_record(folder, "flow", "flow.png"),
                   asset_record(folder, "cover-source", "cover.svg", "cover")]
        (assets / "manifest.json").write_text(json.dumps(manifest(records), ensure_ascii=False),
                                              encoding="utf-8")
    return folder
