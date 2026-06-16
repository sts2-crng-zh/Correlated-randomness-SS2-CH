# -*- coding: utf-8 -*-
"""Download self-hosted site assets (fonts, images)."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
FONTS = DOCS / "fonts"
IMAGES = DOCS / "images"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=120).read()


def find_scatter_url() -> str:
    return "https://tck.mn/blog/correlated-randomness-sts2/transform_vs_act.png"


def main() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    scatter_url = find_scatter_url()
    print("scatter:", scatter_url)
    (IMAGES / "transform_vs_act.png").write_bytes(fetch(scatter_url))

    css_url = "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700&display=swap"
    css = fetch(css_url).decode("utf-8")
    urls = re.findall(r"url\((https://[^)]+)\)", css)
    local = css
    for i, url in enumerate(urls):
        fname = f"noto-sans-sc-{i}.woff2"
        (FONTS / fname).write_bytes(fetch(url))
        local = local.replace(url, fname)
        print("font:", fname)
    (FONTS / "fonts.css").write_text(local, encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
