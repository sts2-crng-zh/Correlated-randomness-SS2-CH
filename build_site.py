# -*- coding: utf-8 -*-
"""Build static site from correlated-randomness-sts2-zh.md"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "correlated-randomness-sts2-zh.md"
DOCS = ROOT / "docs"
STYLE = DOCS / "style.css"
SITE_URL = "https://sts2-crng-zh.github.io/Correlated-randomness-SS2-CH/"


def ensure_markdown():
    try:
        import markdown  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "-q"])


def slugify(value: str, _separator: str = "-") -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "", value, flags=re.UNICODE)
    return value or "section"


def build_toc(content_html: str) -> tuple[str, str]:
    headings: list[tuple[int, str, str]] = []
    used: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        level = int(match.group(1))
        title = html.unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip()
        base = slugify(title)
        count = used.get(base, 0)
        used[base] = count + 1
        anchor = base if count == 0 else f"{base}-{count}"
        headings.append((level, title, anchor))
        return f'<h{level} id="{anchor}">{match.group(2)}</h{level}>'

    content_html = re.sub(r"<h([2345])>(.*?)</h\1>", repl, content_html, flags=re.DOTALL)

    items: list[str] = []
    for level, title, anchor in headings:
        cls = "toc-h3" if level == 3 else ""
        items.append(f'<li class="{cls}"><a href="#{anchor}">{html.escape(title)}</a></li>')
    toc = "\n".join(items)
    return content_html, toc


def markdown_extensions():
    from markdown.extensions.footnotes import FootnoteExtension

    return [
        "tables",
        "fenced_code",
        "sane_lists",
        "md_in_html",
        FootnoteExtension(),
    ]


def make_markdown():
    import markdown

    return markdown.Markdown(extensions=markdown_extensions())


def render_details_blocks(text: str) -> str:
    """Markdown inside <details> is not parsed by default; render it first."""
    pattern = re.compile(
        r"(<details[^>]*>\s*<summary>.*?</summary>\s*)(.*?)(\s*</details>)",
        re.DOTALL | re.IGNORECASE,
    )

    def repl(match: re.Match[str]) -> str:
        prefix, inner, suffix = match.groups()
        inner_html = make_markdown().convert(inner.strip())
        return f"{prefix}\n{inner_html}\n{suffix}"

    return pattern.sub(repl, text)


def main() -> None:
    ensure_markdown()

    text = SOURCE.read_text(encoding="utf-8")
    text = render_details_blocks(text)
    content_html = make_markdown().convert(text)
    content_html, toc_html = build_toc(content_html)

    title = "杀戮尖塔2中的相关随机数"
    description = "《杀戮尖塔2》CRNG（相关随机数）机制中文译文，基于 Andy Tockman 原文翻译。"
    style_version = STYLE.stat().st_mtime_ns if STYLE.exists() else 0

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}">
  <link rel="stylesheet" href="fonts/fonts.css">
  <link rel="stylesheet" href="style.css?v={style_version}">
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <a class="site-title" href="./">{html.escape(title)}</a>
      <div class="site-meta">中文译文 · 术语对照 v1.3</div>
    </div>
  </header>

  <div class="layout">
    <nav class="toc" aria-label="目录">
      <h2>目录</h2>
      <ul>
        {toc_html}
      </ul>
    </nav>

    <main class="article">
      {content_html}
    </main>
  </div>

  <footer class="site-footer">
    <p>译文仅供学习交流。原文作者 Andy Tockman · <a href="https://tck.mn/blog/correlated-randomness-sts2/">英文原文</a></p>
  </footer>

  <script>
    const links = [...document.querySelectorAll('.toc a')];
    const sections = links
      .map((link) => document.querySelector(link.getAttribute('href')))
      .filter(Boolean);

    const onScroll = () => {{
      let current = sections[0];
      for (const section of sections) {{
        if (section.getBoundingClientRect().top <= 120) current = section;
      }}
      links.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === '#' + current.id));
    }};

    window.addEventListener('scroll', onScroll, {{ passive: true }});
    onScroll();
  </script>
</body>
</html>
"""

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    widget_src = DOCS / "divination-widget.js"
    if widget_src.exists():
        print(f"Widget JS: {widget_src}")

    print(f"Built {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
