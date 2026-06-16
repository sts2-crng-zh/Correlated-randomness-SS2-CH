# -*- coding: utf-8 -*-
"""Convert markdown probability tables into proportional bar charts at build time."""

from __future__ import annotations

import html
import re
from typing import Callable

RELIC_RATES_UNDER = {
    "诅咒珍珠": 11.95,
    "沉重石板": 1.32,
    "巨大扭蛋": 1.65,
    "树叶药膏": 12.72,
    "涅奥的骨骰": 13.01,
    "松动羊毛剪": 23.75,
    "华美发束": 23.22,
    "白银熔炉": 12.37,
}

RELIC_RATES_OVER = {
    "诅咒珍珠": 12.99,
    "沉重石板": 23.79,
    "巨大扭蛋": 23.24,
    "树叶药膏": 12.39,
    "涅奥的骨骰": 11.90,
    "松动羊毛剪": 1.35,
    "华美发束": 1.65,
    "白银熔炉": 12.70,
}

TABLE_RE = re.compile(
    r"(?:^|\n)((?:\|[^\n]+\|\n)+)",
    re.MULTILINE,
)

SEGMENT_RE = re.compile(r"([^；]+?)\s*\(([\d.]+)%\)")

JUNK_CARDS: list[tuple[str, str]] = [
    ("铁蒺藜", "bc0"),
    ("交锋", "bc1"),
    ("声东击西", "bc2"),
    ("双持", "bc3"),
    ("巩固", "bc4"),
    ("你好世界", "bc5"),
    ("抢占先机", "bc6"),
    ("弹回", "bc7"),
    ("狂乱撕扯", "bc8"),
    ("堆栈", "bc9"),
]

JUNK_CARD_CLASS = {name: cls for name, cls in JUNK_CARDS}


def strip_md(text: str) -> str:
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\\([\[\]])", r"\1", text)
    return text.strip()


def parse_pct(cell: str) -> float | None:
    cell = strip_md(cell)
    if not cell:
        return None
    m = re.search(r"([\d.]+)\s*%", cell)
    return float(m.group(1)) if m else None


def parse_markdown_table(block: str) -> tuple[list[str], list[list[str]]] | None:
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    if not all(line.startswith("|") and line.endswith("|") for line in lines):
        return None

    def split_row(line: str) -> list[str]:
        return [strip_md(cell.strip()) for cell in line.strip("|").split("|")]

    headers = split_row(lines[0])
    if not re.match(r"^[-:| ]+$", lines[1].replace("|", "").strip()):
        return None
    rows = [split_row(line) for line in lines[2:]]
    return headers, rows


def row_sum(values: list[float | None]) -> float:
    return sum(v for v in values if v is not None)


def rarity_class(label: str) -> str:
    if label.startswith("普通"):
        return "bc0"
    if label.startswith("罕见"):
        return "bc1"
    if label.startswith("稀有"):
        return "bc2"
    return "bc0"


def junk_card_class(card: str) -> str:
    return JUNK_CARD_CLASS.get(card.strip(), "bc0")


def junk_legend() -> str:
    return render_legend([(cls, name) for name, cls in JUNK_CARDS], "junk")


def render_legend(items: list[tuple[str, str]], chart_class: str = "") -> str:
    extra = f" {chart_class}" if chart_class else ""
    parts = [f'<div class="barchartlgnd zh{extra}">']
    for cls, name in items:
        parts.append(f'  <div><div class="{cls}"></div>{html.escape(name)}</div>')
    parts.append("</div>")
    return "\n".join(parts)


def render_bar(segments: list[tuple[float, str, str]], row_scale: float) -> str:
    if not segments:
        return '<div class="bar"></div>'
    chunks: list[str] = []
    for value, label, cls in segments:
        if value <= 0:
            continue
        width = value * row_scale
        if width <= 0:
            continue
        chunks.append(
            f'<div style="width:{width:.4f}%" class="{cls}">'
            f"<span>{html.escape(label)}</span></div>"
        )
    if not chunks:
        return '<div class="bar"></div>'
    return f'<div class="bar">{"".join(chunks)}</div>'


def render_barchart(
    rows: list[tuple[str, list[tuple[float, str, str]]]],
    legend: str = "",
) -> str:
    max_total = max((sum(v for v, _, _ in segs) for _, segs in rows), default=1.0)
    if max_total <= 0:
        max_total = 1.0

    parts = []
    if legend:
        parts.append(legend)
    parts.append('<div class="barchart zh">')
    for label, segments in rows:
        total = sum(v for v, _, _ in segments)
        row_scale = (total / max_total) * 100.0 / total if total > 0 else 0.0
        parts.append(f'<div class="key">{html.escape(label)}</div>')
        parts.append(render_bar(segments, row_scale))
    parts.append("</div>")
    return "\n".join(parts)


def convert_single(headers: list[str], rows: list[list[str]]) -> str:
    values = [parse_pct(row[1]) for row in rows]
    max_val = max((v for v in values if v is not None), default=1.0)
    chart_rows: list[tuple[str, list[tuple[float, str, str]]]] = []
    for row, value in zip(rows, values):
        if value is None:
            continue
        chart_rows.append((row[0], [(value, f"{value:g}%", "bc0")]))
    return render_barchart(chart_rows)


def convert_multi(
    headers: list[str],
    rows: list[list[str]],
    col_classes: list[str],
    get_row_weight: Callable[[str, list[float | None]], float] | None = None,
) -> str:
    legend = render_legend([(cls, hdr) for cls, hdr in zip(col_classes, headers[1:])])
    parsed: list[tuple[str, list[tuple[float, str, str]]]] = []
    weights: list[float] = []

    for row in rows:
        label = row[0]
        values = [parse_pct(cell) for cell in row[1:]]
        segments: list[tuple[float, str, str]] = []
        for value, cls in zip(values, col_classes):
            if value is None:
                continue
            if value <= 0:
                continue
            segments.append((value, f"{value:g}%", cls))
        parsed.append((label, segments))
        if get_row_weight:
            weights.append(get_row_weight(label, values))
        else:
            weights.append(row_sum(values) or 0.0)

    max_weight = max(weights) if weights and max(weights) > 0 else 1.0
    parts = [legend, '<div class="barchart zh">']
    for (label, segments), weight in zip(parsed, weights):
        total = sum(v for v, _, _ in segments)
        row_scale = (weight / max_weight) * 100.0 / total if total > 0 else 0.0
        parts.append(f'<div class="key">{html.escape(label)}</div>')
        parts.append(render_bar(segments, row_scale))
    parts.append("</div>")
    return "\n".join(parts)


def convert_junk_base(headers: list[str], rows: list[list[str]]) -> str:
    legend = junk_legend()
    values = [parse_pct(row[1]) for row in rows]
    max_val = max((v for v in values if v is not None), default=1.0)
    parts = [legend, '<div class="barchart zh junk">']
    for row, value in zip(rows, values):
        if value is None:
            continue
        card = row[0]
        cls = junk_card_class(card)
        row_scale = (value / max_val) * 100.0 / value if value > 0 else 0.0
        parts.append(f'<div class="key">{html.escape(card)}</div>')
        parts.append(render_bar([(value, f"{value:g}%", cls)], row_scale))
    parts.append("</div>")
    return "\n".join(parts)


def convert_junk_conditioned(headers: list[str], rows: list[list[str]]) -> str:
    legend = junk_legend()
    parts = [legend, '<div class="barchart zh junk">']

    for row in rows:
        relic = row[0]
        segments: list[tuple[float, str, str]] = []
        for match in SEGMENT_RE.finditer(row[1]):
            card = match.group(1).strip()
            value = float(match.group(2))
            segments.append((value, f"{card} ({value:g}%)", junk_card_class(card)))
        total = sum(v for v, _, _ in segments)
        row_scale = 100.0 / total if total > 0 else 0.0
        parts.append(f'<div class="key">{html.escape(relic)}</div>')
        parts.append(render_bar(segments, row_scale))

    parts.append("</div>")
    return "\n".join(parts)


def convert_ouroboros(headers: list[str], rows: list[list[str]]) -> str:
    legend = render_legend(
        [("bc0", "普通"), ("bc1", "罕见"), ("bc2", "稀有")]
    )
    chart_rows: list[tuple[str, list[tuple[float, str, str]]]] = []

    for row in rows:
        label = row[0]
        cls = rarity_class(label)
        segments: list[tuple[float, str, str]] = []
        for value, outcome in zip([parse_pct(cell) for cell in row[1:]], headers[1:]):
            if value is None or value <= 0:
                continue
            segments.append((value, f"{outcome} {value:g}%", cls))
        if segments:
            chart_rows.append((label, segments))

    return legend + "\n" + render_barchart(chart_rows)


def classify_table(headers: list[str]) -> str:
    joined = "|".join(headers)
    if headers[:2] == ["诅咒", "暗港"] or headers[:2] == ["诅咒", "密林"]:
        return "single"
    if headers[:2] == ["遗物", "暗港"] or headers[:2] == ["遗物", "密林"]:
        return "single"
    if headers[:2] == ["卡牌", "概率"]:
        return "junk_base"
    if headers[0] == "诅咒池遗物" and "可能卡牌" in joined:
        return "junk_conditioned"
    if headers[0] == "诅咒池遗物" and "左侧" in joined:
        return "two_col_lr"
    if headers[0] == "诅咒池遗物" and "暗港" in joined:
        return "two_col_acts"
    if "风的女儿" in joined:
        return "three_col"
    if headers[0] == "金币":
        return "four_col"
    if "烫嘴可可" in joined:
        return "three_col_food"
    if headers[0] == "第一场战斗奖励":
        return "ouroboros"
    if headers[0] == "一个玩偶":
        return "skip"
    return "single"


def convert_table(headers: list[str], rows: list[list[str]]) -> str | None:
    kind = classify_table(headers)
    if kind == "skip":
        return None
    if kind == "single":
        return convert_single(headers, rows)
    if kind == "junk_base":
        return convert_junk_base(headers, rows)
    if kind == "junk_conditioned":
        return convert_junk_conditioned(headers, rows)
    if kind == "two_col_lr":
        return convert_multi(
            headers,
            rows,
            ["bc3", "bc4"],
            get_row_weight=lambda label, _: RELIC_RATES_UNDER.get(label, 0.0),
        )
    if kind == "two_col_acts":
        return convert_multi(headers, rows, ["bc3", "bc4"])
    if kind == "three_col":
        return convert_multi(headers, rows, ["bc3", "bc4", "bc5"])
    if kind == "four_col":
        return convert_multi(headers, rows, ["bc3", "bc4", "bc5", "bc6"])
    if kind == "three_col_food":
        return convert_multi(headers, rows, ["bc3", "bc4", "bc5"])
    if kind == "ouroboros":
        return convert_ouroboros(headers, rows)
    return convert_single(headers, rows)


def visualize_tables_in_markdown(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        block = match.group(1)
        parsed = parse_markdown_table(block)
        if not parsed:
            return match.group(0)
        headers, rows = parsed
        chart = convert_table(headers, rows)
        if chart is None:
            return match.group(0)
        prefix = "\n" if match.group(0).startswith("\n") else ""
        return prefix + chart + "\n"

    return TABLE_RE.sub(repl, text)
