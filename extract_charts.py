# -*- coding: utf-8 -*-
"""Extract Leafy Poultice / Hefty Tablet charts from original blog HTML."""

from __future__ import annotations

import html
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


def cn(card_id: str) -> str:
    card_id = card_id.strip()
    if not card_id:
        return ""
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
        r"<div class='key(?: phantom)?'([^>]*)>([^<]*)</div>"
        r"<div class='bar'><div[^>]*style='width:([^']+)'[^>]*><span>([^<]+)</span>",
        re.IGNORECASE,
    )
    for attrs, _label, width, pct in pattern.findall(section_html):
        phantom = "phantom" in attrs
        keys_m = re.search(r"data-keys='([^']*)'", attrs)
        btn_m = re.search(r"data-btn='([^']*)'", attrs)
        cards = keys_m.group(1).split("|") if keys_m else []
        rows.append(
            {
                "phantom": phantom,
                "btn": btn_m.group(1) if btn_m else "",
                "cards": cards,
                "width": width.strip(),
                "pct": pct.strip(),
            }
        )
    return rows


def extract_details(html: str, summary: str) -> str:
    m = re.search(
        rf"<details><summary>{re.escape(summary)}</summary><div>(.*?)</div></details>",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    return m.group(1) if m else ""


def extract_hefty_block(source_html: str) -> str:
    if "Similarly," not in source_html:
        return ""
    start = source_html.index("Similarly,")
    m = re.search(r"<h2[^>]*>\s*New Leaf", source_html[start:], re.IGNORECASE)
    end = start + m.start() if m else len(source_html)
    return source_html[start:end]


def split_acts(block: str) -> tuple[str, str]:
    under = ""
    over = ""
    um = re.search(r"<p>Underdocks:</p>(.*?)(<p>Overgrowth:</p>|$)", block, re.DOTALL | re.IGNORECASE)
    if um:
        under = um.group(1)
    om = re.search(r"<p>Overgrowth:</p>(.*?)(?=<h2|$)", block, re.DOTALL | re.IGNORECASE)
    if om:
        over = om.group(1)
    return under, over


def render_act_barchart(rows: list[dict], btn_id: str, act_label: str) -> str:
    out = [f'<p><strong>{act_label}：</strong></p>', '<div class="barchartbtns">']
    for i, (key, name) in enumerate(CHARS):
        active = " active" if i == 0 else ""
        out.append(
            f'<button type="button" class="{key}{active}" data-btn="{btn_id}" data-idx="{i}">{name}</button>'
        )
    out.append("</div>")
    out.append('<div class="barchart">')
    for row in rows:
        cn_names = [cn(card) for card in row["cards"]]
        label = cn_names[0] if cn_names else ""
        keys_attr = html.escape("|".join(cn_names), quote=True)
        phantom = " phantom" if row["phantom"] else ""
        attrs = f" data-btn='{btn_id}' data-keys='{keys_attr}'" if cn_names else ""
        out.append(
            f"<div class='key{phantom}'{attrs}>{html.escape(label)}</div>"
            f"<div class='bar'><div style='width:{row['width']}' class='bc0'><span>{row['pct']}</span></div></div>"
        )
    out.append("</div>")
    return "\n".join(out)


def render_leafy_hefty_section(source_html: str | None = None) -> str:
    source_html = source_html or fetch_html()
    leafy = extract_details(source_html, "Leafy Poultice")
    hefty_block = extract_hefty_block(source_html)
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
        "以下图表按原文做成可折叠区块，可点击角色按钮切换查看。",
        "",
        '<details class="chart-details" open>',
        "<summary>树叶药膏</summary>",
        "",
        render_act_barchart(parse_barchart(leafy_under), "leafy-u", "暗港"),
        "",
        render_act_barchart(parse_barchart(leafy_over), "leafy-o", "密林"),
        "",
        "</details>",
        "",
        "类似地，**沉重石板在密林的第一次选项只有 11 种可能，在暗港只有 3 种**！正如上文所示，沉重石板在暗港本身大约只出现 1.3%，因此看到它本身就是极强的信息。",
        "",
        '<details class="chart-details">',
        "<summary>沉重石板</summary>",
        "",
        render_act_barchart(parse_barchart(hefty_under), "tablet-u", "暗港"),
        "",
        render_act_barchart(parse_barchart(hefty_over), "tablet-o", "密林"),
        "",
        "</details>",
    ]
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
