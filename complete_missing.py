# -*- coding: utf-8 -*-
"""Patch all remaining omitted sections in the Chinese translation."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
MD = ROOT / "correlated-randomness-sts2-zh.md"
MAP = json.loads((ROOT / "translation_map.json").read_text(encoding="utf-8"))

MANUAL_CARDS = {"NotYet": "时候未到", "Prepared": "早有准备"}
MANUAL_RELICS = {
    "CursedPearl": "诅咒珍珠",
    "HeftyTablet": "沉重石板",
    "LargeCapsule": "巨大扭蛋",
    "LeafyPoultice": "树叶药膏",
    "NeowsBones": "涅奥的骨骰",
    "PrecariousShears": "松动羊毛剪",
    "SilkenTress": "华美发束",
    "SilverCrucible": "白银熔炉",
}
RELIC_ORDER = [
    "诅咒珍珠",
    "沉重石板",
    "巨大扭蛋",
    "树叶药膏",
    "涅奥的骨骰",
    "松动羊毛剪",
    "华美发束",
    "白银熔炉",
]

CSHARP_APPENDIX = """```csharp
// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==

[...]

private int inext;
private int inextp;
private int[] SeedArray = new int[56];

[...]

public Random(int Seed) {
  int ii;
  int mj, mk;

  //Initialize our Seed array.
  //This algorithm comes from Numerical Recipes in C (2nd Ed.)
  int subtraction = (Seed == Int32.MinValue) ? Int32.MaxValue : Math.Abs(Seed);
  mj = MSEED - subtraction;
  SeedArray[55]=mj;
  mk=1;
  for (int i=1; i<55; i++) {  //Apparently the range [1..55] is special (Knuth) and so we're wasting the 0'th position.
    ii = (21*i)%55;
    SeedArray[ii]=mk;
    mk = mj - mk;
    if (mk<0) mk+=MBIG;
    mj=SeedArray[ii];
  }
  for (int k=1; k<5; k++) {
    for (int i=1; i<56; i++) {
  SeedArray[i] -= SeedArray[1+(i+30)%55];
  if (SeedArray[i]<0) SeedArray[i]+=MBIG;
    }
  }
  inext=0;
  inextp = 21;
  Seed = 1;
}

[...]

private int InternalSample() {
    int retVal;
    int locINext = inext;
    int locINextp = inextp;

    if (++locINext >=56) locINext=1;
    if (++locINextp>= 56) locINextp = 1;

    retVal = SeedArray[locINext]-SeedArray[locINextp];

    if (retVal == MBIG) retVal--;
    if (retVal<0) retVal+=MBIG;

    SeedArray[locINext]=retVal;

    inext = locINext;
    inextp = locINextp;

    return retVal;
}
```"""

DIVINATION_WIDGET = """
<div class="divination-widget">
  <p><label>第一场战斗金币（进阶 3+）：<input id="divgold" type="number" min="7" max="15" value="7"></label></p>
  <p class="divination-note">下表为水晶球遗物箱落在各格子的概率（共 41 格，布局与原文一致）。</p>
  <div id="divination-grid"></div>
  <div id="divination-table-wrap"></div>
</div>
<script src="divination-widget.js"></script>
"""


def fetch_html() -> str:
    req = urllib.request.Request(
        "https://tck.mn/blog/correlated-randomness-sts2/",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")


def cn_card(name: str) -> str:
    name = name.strip()
    if name in MANUAL_CARDS:
        return MANUAL_CARDS[name]
    if name in MAP:
        return MAP[name]
    return MAP.get(re.sub(r"([a-z])([A-Z])", r"\1 \2", name), name)


def cn_relic(key: str) -> str:
    key = key.strip()
    tag = ""
    if key.endswith("[U]"):
        tag = " [暗港]"
        key = key[:-3]
    elif key.endswith("[O]"):
        tag = " [密林]"
        key = key[:-3]
    return MANUAL_RELICS.get(key, MAP.get(key, key)) + tag


def slice_html(html: str, start: str, end: str) -> str:
    m = re.search(start, html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    s = m.start()
    m2 = re.search(end, html[s + 5 :], re.IGNORECASE)
    e = s + 5 + m2.start() if m2 else len(html)
    return html[s:e]


def parse_key_pct_pairs(chunk: str) -> list[tuple[str, str]]:
    pat = re.compile(
        r"<div class='key'>([^<]+)</div><div class='bar'><div[^>]*><span>([^<]+)</span>",
        re.IGNORECASE,
    )
    return [(a.strip(), b.strip()) for a, b in pat.findall(chunk)]


def parse_stacked_rows(chunk: str) -> list[tuple[str, list[tuple[str, str]]]]:
    rows = []
    row_pat = re.compile(
        r"<div class='key'>([^<]+)</div><div class='bar'>(.*?)</div></div>",
        re.DOTALL | re.IGNORECASE,
    )
    seg_pat = re.compile(r"<span>([^<]+)</span>")
    for key, bar in row_pat.findall(chunk):
        segments = []
        for label in seg_pat.findall(bar):
            m = re.match(r"^(.+?) \(([^)]+)\)$", label.strip())
            if m:
                segments.append((cn_card(m.group(1)), m.group(2)))
        rows.append((cn_relic(key), segments))
    return rows


def simple_table(rows: list[tuple[str, str]], h1: str, h2: str) -> str:
    out = [f"| {h1} | {h2} |", "|------|------|"]
    out.extend(f"| {a} | {b} |" for a, b in rows)
    return "\n".join(out)


def stacked_table(rows: list[tuple[str, list[tuple[str, str]]]]) -> str:
    out = ["| 诅咒池遗物 | 可能卡牌（概率） |", "|-----------|----------------|"]
    for key, segments in rows:
        text = "；".join(f"{name} ({pct})" for name, pct in segments)
        out.append(f"| {key} | {text} |")
    return "\n".join(out)


def split_uo_pairs(pairs: list[tuple[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    u, o = {}, {}
    for k, p in pairs:
        if k.endswith("[U]"):
            u[cn_relic(k)] = p
        elif k.endswith("[O]"):
            o[cn_relic(k)] = p
    return u, o


def uo_table(u: dict[str, str], o: dict[str, str]) -> str:
    out = ["| 诅咒池遗物 | 暗港 | 密林 |", "|-----------|------|------|"]
    for name in RELIC_ORDER:
        ku = next((v for k, v in u.items() if name in k), "")
        ko = next((v for k, v in o.items() if name in k), "")
        out.append(f"| {name} | {ku} | {ko} |")
    return "\n".join(out)


def patch_trash_heap(text: str, html: str) -> str:
    base = slice_html(html, r"Since the Trash Heap is Underdocks-exclusive", r"In case you want to predict the Trash Heap")
    cond = slice_html(html, r"In case you want to predict the Trash Heap more precisely", r"Potion drops and question mark combats")
    base_rows = [(cn_card(k), p) for k, p in parse_key_pct_pairs(base)]
    cond_rows = parse_stacked_rows(cond)
    section = f"""## 垃圾堆

**垃圾堆**是暗港专属事件，因此有内在偏差。以下是垃圾堆 RNG 在幕别 RNG roll 出暗港时的输出：

{simple_table(base_rows, "卡牌", "概率")}

如你所见，在单人模式中**根本不可能**获得**弹回**这张牌。[^3]

如果你关心遗物预测：连续两张卡牌对应**黑石护符**、**捕梦网**、**手钻**、**巨口储蓄罐**和**发条靴**（例如，卡牌是巩固或你好世界时，遗物是手钻）。

若你想更精确地预测垃圾堆，还可以进一步根据看到的诅咒池遗物条件化：[^4]

{stacked_table(cond_rows)}

发现这一点后，我在网上搜索相关讨论，确实有人注意到似乎无法完成**百科大全**。我还发现 Discord 用户 @hoge 大约一个月前就精准描述了这个问题。向他们致敬！
"""
    return re.sub(r"## 垃圾堆.*?## 药水掉落与？房间战斗", section + "\n## 药水掉落与？房间战斗", text, flags=re.DOTALL)


def patch_potion(text: str, html: str) -> str:
    pot = slice_html(html, r"Potion drops and question mark combats", r"Doll Room")
    pot_pairs = parse_key_pct_pairs(pot.split("first ? room")[0] if "first ? room" in pot else pot)
    qm_chunk = pot.split("first ? room")[-1] if "first ? room" in pot else ""
    qm_pairs = parse_key_pct_pairs(qm_chunk)
    u, o = split_uo_pairs(pot_pairs)
    u2, o2 = split_uo_pairs(qm_pairs)
    section = f"""## 药水掉落与？房间战斗

最后是开篇第三点——第一场战斗掉落药水的频率？套路你已经熟了：

{uo_table(u, o)}

再次提醒：沉重石板和巨大扭蛋在暗港极为罕见，华美发束和松动羊毛剪在密林极为罕见。综合考量后，**第一场战斗掉落药水的总概率在暗港是 76%，在密林仅 4%**！

但要注意：选择任何会生成卡牌奖励或随机遗物的涅奥选项都会破坏这种相关性，因为它会「偷走」奖励 RNG 的第一次调用。因此在糟糕的密林地图上，**失物盒**可能看起来比平均更有吸引力。

额外福利：第一个？房间是战斗的概率分布也相当不均：

{uo_table(u2, o2)}

（按幕别平均后，暗港约 9.6%，密林约 10.4%，大体持平。）

到目前为止，以上内容都只适用于第一幕。但——你猜对了——还能走得更远……
"""
    return re.sub(r"## 药水掉落与？房间战斗.*?## 玩偶室", section + "\n## 玩偶室", text, flags=re.DOTALL)


def patch_lightning(text: str) -> str:
    return text.replace(
        "完整表格原文未列出，但举个例子",
        "原文作者未列出完整表格，但举个例子",
    )


def patch_divination(text: str) -> str:
    section = f"""## 占卜

**水晶球**同样只出现在第二或第三幕。

它也有自己的 RNG，但这次第一个有趣的 RNG 调用是**第二次**，决定遗物箱放在哪里。[^5]

最容易关联的第二次 roll 是什么？有些信号非常强（例如第一家商店左上角那张牌），但追踪起来有点烦，因为它取决于第一次roll出的稀有度。

结果是：**你第一场战斗掉落的金币数量**是「奖励」RNG 的第二次 roll（第一次是是否掉落药水，见上文）。

下面是可以按金币数量查看分布的交互小部件（假设进阶 3+）：

{DIVINATION_WIDGET.strip()}

但这打开了一个全新的世界。还能通过关联第二次 roll 做什么？
"""
    return re.sub(r"## 占卜.*?## 先古之民奖励", section + "\n## 先古之民奖励", text, flags=re.DOTALL)


def patch_appendix_how(text: str) -> str:
    text = text.replace(
        "于是意外开始了对游戏中每一个其他 roll 的关联深挖。为留纪念，作者在原文中保存了这整段冒险的视频（链接大致指向他注意到不对劲的时刻）。",
        "于是意外开始了对游戏中每一个其他 roll 的关联深挖。为留纪念，[我保存了这整段冒险的视频](https://youtu.be/kIBOvKzeNO0?t=8850)（链接大致指向我注意到不对劲的时刻）。",
    )
    text = text.replace(
        "（见树叶药膏表格）",
        "（[见树叶药膏表格](#树叶药膏与沉重石板)）",
    )
    if "transform_vs_act.png" not in text:
        text = text.replace(
            "结果嘛，相当震撼。",
            "结果嘛，相当震撼。\n\n![变化 roll 与幕别 roll 的散点图](images/transform_vs_act.png)",
        )
    return text


def patch_appendix_why(text: str) -> str:
    return re.sub(
        r"```csharp\n// （构造函数与 InternalSample 方法——与原文相同，此处保留英文源码）.*?```",
        CSHARP_APPENDIX,
        text,
        flags=re.DOTALL,
    )


def patch_footer(text: str) -> str:
    return re.sub(
        r"\*翻译说明：.*?\*",
        "*翻译说明：卡牌与遗物中文名均参照仓库内《杀戮尖塔2》中英对照表 v1.3。原文中未展开的交互图表（如新叶/奥术卷轴的 14 种组合）在原文中亦未列出；噬尸蛞蝓充能球目标的完整表同理。其余可提取的数据表与交互部件均已收录。*",
        text,
        flags=re.DOTALL,
    )


def main() -> None:
    html = fetch_html()
    text = MD.read_text(encoding="utf-8")
    text = patch_trash_heap(text, html)
    text = patch_potion(text, html)
    text = patch_lightning(text)
    text = patch_divination(text)
    text = patch_appendix_how(text)
    text = patch_appendix_why(text)
    text = patch_footer(text)
    MD.write_text(text, encoding="utf-8")
    print("Patched", MD)


if __name__ == "__main__":
    main()
