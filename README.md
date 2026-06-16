# 杀戮尖塔2 · 相关随机数（中文译文）

Andy Tockman 关于《杀戮尖塔2》CRNG（相关随机数）问题的博客中文译文。

## 在线阅读

**https://sts2-crng-zh.github.io/Correlated-randomness-SS2-CH/**

分享链接使用 GitHub Organization `sts2-crng-zh`，URL 中不含个人 GitHub 用户名。

## 本地预览

```bash
python fetch_assets.py   # 首次或更新字体/图片资源时
python build_site.py
python -m http.server 8080 --directory docs
```

然后在浏览器打开 http://localhost:8080

## 文件说明

| 文件 | 说明 |
|------|------|
| `correlated-randomness-sts2-zh.md` | 译文 Markdown 源文件 |
| `translation_map.json` | 从对照表提取的术语映射 |
| `杀戮尖塔2/翻译对照表/` | 中英术语对照表（xlsx） |
| `docs/` | 静态网站（由 `build_site.py` 生成） |
| `fetch_assets.py` | 下载自托管字体与附录图片 |

## 原文

https://tck.mn/blog/correlated-randomness-sts2/
