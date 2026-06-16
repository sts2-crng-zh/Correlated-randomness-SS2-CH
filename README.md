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

## 隐私说明

### 当前状态

| 项目 | 说明 |
|------|------|
| **仓库** | **公开**（免费 Organization 仅支持公开仓库） |
| **Pages 站点** | 公开，持有链接者可阅读 |
| **分享链接** | 使用组织域名，不含个人用户名 |
| **提交作者** | 已统一为组织匿名身份 `sts2-crng-zh` |
| **访客追踪** | 站点不加载 Google Fonts / 分析脚本；字体与附录图片自托管 |

### 仍可能被关联的途径

- 若你曾在 Issues、PR 或 fork 中用过个人账号互动，GitHub 仍可能显示关联。
- 外部链接（原文、YouTube、wiki）仅在访客**主动点击**时跳转。

### 组织与仓库设置（建议检查）

在 GitHub 网页端确认：

1. **Organization → People → Member visibility**：设为 **Private**
2. **仓库 Settings → General**：关闭 **Issues**、**Wiki**（如不需要）
3. **仓库 Settings → Pages**：Source 为 **GitHub Actions**

### 字体与图片

站点字体（Noto Sans SC）与附录散点图存放在 `docs/fonts/`、`docs/images/`，构建时不向 Google 或第三方发送访客 Referer。更新资源：

```bash
python fetch_assets.py
python build_site.py
```
