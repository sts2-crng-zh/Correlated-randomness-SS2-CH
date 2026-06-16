# -*- coding: utf-8 -*-
"""Extract Leafy Poultice / Hefty Tablet tables from original blog HTML."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
MAP = json.loads((ROOT / "translation_map.json").read_text(encoding="utf-8"))

MANUAL = {
    "NotYet": "时候未到",
    "Not Yet": "时候未到",
    "Prepared": "早有准备",
}

CHARS = [
    ("clad", "铁甲战士"),
    ("silent", "静默猎手"),
    ("regent", "储君"),
    ("necro", "亡灵契约师"),
    ("defect", "故障机器人"),
]
CHAR_INDEX = {c[0]: i for i, c in enumerate(CHARS)}


def cn(card_id: str) -> str:
    card_id = card_id.strip()
    if card_id in MANUAL:
        return MANUAL[card_id]
    if card_id in MAP:
        return MAP[card_id]
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", card_id)
    if spaced in MANUAL:
        return MANUAL[spaced]
    if spaced in MAP:
        return MAP[spaced]
    return card_id


def fetch_html() -> str:
    url = "https://tck.mn/blog/correlated-randomness-sts2/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")


def parse_barchart(section_html: str) -> list[dict]:
    rows = []
    pattern = re.compile(
        r"<div class='key'[^>]*data-keys='([^']*)'[^>]*>([^<]+)</div>"
        r"<div class='bar'><div[^>]*><span>([^<]+)</span>",
        re.IGNORECASE,
    )
    for keys, _label, pct in pattern.findall(section_html):
        rows.append({"pct": pct.strip(), "cards": keys.split("|")})
    return rows


def extract_details(html: str, summary: str) -> str:
    m = re.search(
        rf"<details><summary>{re.escape(summary)}</summary><div>(.*?)</div></details>",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    return m.group(1) if m else ""


def split_acts(block: str) -> tuple[str, str]:
    under = ""
    over = ""
    um = re.search(r"<p>Underdocks:</p>(.*?)(<p>Overgrowth:</p>|$)", block, re.DOTALL | re.IGNORECASE)
    if um:
        under = um.group(1)
    om = re.search(r"<p>Overgrowth:</p>(.*)$", block, re.DOTALL | re.IGNORECASE)
    if om:
        over = om.group(1)
    return under, over


def table_md(rows: list[dict], char_key: str) -> str:
    idx = CHAR_INDEX[char_key]
    lines = ["| 卡牌 | 概率 |", "|------|------|"]
    for row in rows:
        if idx >= len(row["cards"]):
            continue
        lines.append(f"| {cn(row['cards'][idx])} | {row['pct']} |")
    return "\n".join(lines)


def render_leafy_hefty_section(html: str | None = None) -> str:
    html = html or fetch_html()
    leafy = extract_details(html, "Leafy Poultice")
    hefty_block = html.split("Similarly,")[1].split("## New Leaf")[0] if "Similarly," in html else ""
    leafy_under, leafy_over = split_acts(leafy)
    hefty_under, hefty_over = split_acts(hefty_block)

    lines = [
        "## 树叶药膏与沉重石板",
        "",
        "（分别是「变化 2 张」和「选择一张稀有牌」。）",
        "",
        "两者都是诅咒池遗物，因此有内在偏差。但它们都会生成多张牌，我们只能预测第一张。",
        "",
        "结果是：**树叶药膏的第一次变化只有 22 种可能**（每个角色 80 张牌池中的子集），其中一些明显更常见。",
        "",
        "（原文将这些图表做成可折叠区块；以下按角色列出完整数据。）",
        "",
        "### 树叶药膏",
        "",
    ]

    for act_html, act_label in [(leafy_under, "暗港"), (leafy_over, "密林")]:
        rows = parse_barchart(act_html)
        lines.append(f"#### {act_label}")
        lines.append("")
        for char_key, char_cn in CHARS:
            lines.append(f"##### {char_cn}")
            lines.append("")
            lines.append(table_md(rows, char_key))
            lines.append("")

    lines.extend(
        [
            "类似地，**沉重石板在密林的第一次选项只有 11 种可能，在暗港只有 3 种**！正如上文所示，沉重石板在暗港本身大约只出现 1.3%，因此看到它本身就是极强的信息。",
            "",
            "### 沉重石板",
            "",
        ]
    )

    for act_html, act_label in [(hefty_under, "暗港"), (hefty_over, "密林")]:
        rows = parse_barchart(act_html)
        lines.append(f"#### {act_label}")
        lines.append("")
        for char_key, char_cn in CHARS:
            lines.append(f"##### {char_cn}")
            lines.append("")
            lines.append(table_md(rows, char_key))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def patch_translation_markdown(md_path: Path | None = None) -> str:
    md_path = md_path or ROOT / "correlated-randomness-sts2-zh.md"
    text = md_path.read_text(encoding="utf-8")
    start = text.index("## 树叶药膏与沉重石板")
    end = text.index("## 新叶与奥术卷轴")
    new_section = render_leafy_hefty_section()
    updated = text[:start] + new_section + "\n" + text[end:]
    md_path.write_text(updated, encoding="utf-8")
    return new_section


if __name__ == "__main__":
    section = patch_translation_markdown()
    print("Patched correlated-randomness-sts2-zh.md")
    print("Section length:", len(section))
