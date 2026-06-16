# 杀戮尖塔2中的相关随机数（Correlated Randomness）

> 原文：[Correlated randomness in Slay the Spire 2](https://tck.mn/blog/correlated-randomness-sts2/)  
> 作者：Andy Tockman  
> 日期：2026-06-13  
> 译者注：游戏术语参照《杀戮尖塔2》中英对照表 v1.3（测试版 105）。原文基于 v0.107.0。

---

关于《杀戮尖塔2》单人模式，以下三句话都是真的：

1. 如果你在**暗港**选了**涅奥的骨骰**，随机诅咒有约 **54%** 的概率是**债务**。\*
2. 你不可能从**垃圾堆**事件中获得**弹回**。
3. 在暗港，你第一场战斗掉落药水的概率是 **76%**；在密林则是 **4%**。\*\*

（\* 假设涅奥的骨骰给出的两件遗物都不是**新叶**或**万花筒**）  
（\*\* 假设你的涅奥遗物不会给出卡牌或其他遗物）  
（\*\*\* 以下数据均基于当前测试版补丁 v0.107.0）

什么？！

为什么？罪魁祸首是不同随机数生成器之间出人意料的**相关性**——只要你知道其中一个 RNG 的第一次输出，就能推断出所有其他 RNG 第一次输出的大致范围。

## 杀戮尖塔2的随机数生成器

下面先给出一个极度简化的解释。若你想了解细节，请跳到文末附录；若你不关心原理，可以直接跳过本节，去看后面那些有趣的例子。

「相关 RNG」（CRNG）现象在杀戮尖塔社区里并不陌生，因为一代也有类似问题，[Forgotten Arbiter 的博客](https://tck.mn/blog/correlated-randomness-sts/)对此有详尽分析。[^1]

简要来说，在一代中，游戏使用了多个独立的伪随机数生成器，以免战斗内的随机性影响未来的卡牌奖励。但它们初始化时使用了相同的起始状态，因此会产出相同的数字序列。精明的玩家因此可以通过观察过去的随机结果，推断未来的随机事件。

为了避免同样的问题，二代将各个伪随机数生成器初始化到**不同**的状态。代码大致如下（为教学目的做了高度简化）：

```
Rng UpFront = new Rng(seed + hash("up_front"));
Rng Shuffle = new Rng(seed + hash("shuffle"));
Rng UnknownMapPoint = new Rng(seed + hash("unknown_map_point"));
Rng CombatCardGeneration = new Rng(seed + hash("combat_card_generation"));
Rng CombatPotionGeneration = new Rng(seed + hash("combat_potion_generation"));
Rng CombatCardSelection = new Rng(seed + hash("combat_card_selection"));
Rng CombatEnergyCosts = new Rng(seed + hash("combat_energy_costs"));
Rng CombatTargets = new Rng(seed + hash("combat_targets"));
Rng MonsterAi = new Rng(seed + hash("monster_ai"));
Rng Niche = new Rng(seed + hash("niche"));
Rng CombatOrbGeneration = new Rng(seed + hash("combat_orbs"));
Rng TreasureRoomRelics = new Rng(seed + hash("treasure_room_relics"));
// ...
```

游戏中还有更多 RNG，此处为简洁省略；值得注意的是，**每个事件都有自己独立的 RNG**。

`hash` 函数本质上把输入字符串映射成一个「看起来随机」的数字，但对相同输入永远返回相同结果。因此思路是：打乱各 RNG 的初始状态，但相同种子仍然保证整局游戏完全一致。

问题出在：这些种子被传给了 C# 内置的 `System.Random` 类。不幸的是，C# 所用的伪随机算法，其输出与起始种子之间几乎是**完全线性**的关系。

这意味着什么，说起来有点复杂——我稍后在附录里会细讲。但后果是：两个种子相差一个已知固定量的 RNG，其输出也会相差一个模糊、但仍可利用的固定量。

可利用到什么程度？嗯……

下面是一大堆 CRNG 的后果，从「好笑但无关紧要」到「确实影响游戏体验」都有（其中一些甚至会影响完全不知道 CRNG 存在的休闲玩家！）。

## 涅奥的骨骰

先从开篇第一个例子说起。如果你在暗港选择**涅奥的骨骰**，你收到的「随机」诅咒实际上近似服从以下分布：

| 诅咒 | 暗港 |
|------|------|
| 笨拙 | 0.10% |
| **债务** | **54.25%** |
| 腐朽 | 40.32% |
| 疑虑 | 1.50% |
| 愧疚 | 0% |
| 受伤 | 0% |
| 凡庸 | 0% |
| 悔恨 | 0% |
| 羞耻 | 0% |
| 苦恼 | 3.82% |

而在密林，诅咒分布则是：

| 诅咒 | 密林 |
|------|------|
| 笨拙 | 0.51% |
| 债务 | 0% |
| 腐朽 | 0% |
| 疑虑 | 0% |
| 愧疚 | 0.19% |
| 受伤 | 5.53% |
| 凡庸 | 1.18% |
| 悔恨 | 0% |
| 羞耻 | 18.85% |
| 苦恼 | 73.74% |

这一点我觉得特别好笑——Reddit 和 Discord 上到处都有人哀叹自己运气太差，涅奥的骨骰老是roll出**债务**。[^2] 甚至在发现 CRNG 之前，我就看到过一些帖子坚称债务出现得比随机更频繁。我脑子里几乎是**瞬间**就把它们归类为教科书式的确认偏误。然而……

要理解这一点，需要把三处随机性关联起来：

* **涅奥提供的「诅咒遗物」**来自涅奥事件专用 RNG，种子为 `seed + 1 + hash("NEOW")`。  
  涅奥选项中永远恰好有一件来自「诅咒池」的遗物（[wiki 有说明](https://slaythespire2.wiki.gg/wiki/Neow)）。从 8 件诅咒遗物中选出哪一件，是涅奥 RNG 的第一次调用。
* **涅奥的骨骰给出的随机诅咒**来自 `RunState.Rng.Niche` 的调用，种子为 `seed + hash("niche")`。  
  由于**新叶**和**万花筒**也会调用 `Niche` 来随机，如果从涅奥的骨骰中roll到这两件遗物之一，相关性就会被破坏。否则，这通常是 `Niche` 的第一次调用。
* **第一幕变体**（暗港或密林）来自 `StartRunLobby#BeginRunLocally` 中创建的一个未命名 RNG，种子为基础种子。

涅奥的骨骰来自涅奥的「诅咒池」，因此你只有在涅奥 RNG 第一次调用roll到特定区间时才会看到它，这对 `Niche` 第一次调用的可能区间施加了强约束（再结合你所在的第一幕变体，约束更强）。

显然，这种相关性对游戏体验影响很大，即便玩家浑然不觉。它让涅奥的骨骰变成了一件差得多的遗物：像笨拙、愧疚、受伤这类较轻的诅咒极少出现，而像债务这样更致命的诅咒却频繁得多。

此时你可能会想：「等等，那岂不是意味着我们能预测**所有**涅奥遗物的随机性？」确实可以！再来看几个。

## 巨大扭蛋

**巨大扭蛋**给出的第一件遗物**永远不会是普通**。

什么加强！

更具体地说：在密林，约 70% 是罕见、30% 是稀有；在暗港，约 37% 是罕见、63% 是稀有——但有一个前提：

由于一切都彼此相关，巨大扭蛋在暗港整幕中大约只出现 **1.65%** 的时间。（似乎还没人注意到这一点；我当时刚开始调查这一切时，有人对此信息的反应非常好笑。）

暗港涅奥「诅咒池」选项的具体分布：

| 遗物 | 暗港 |
|------|------|
| 诅咒珍珠 | 11.95% |
| 沉重石板 | 1.32% |
| 巨大扭蛋 | 1.65% |
| 树叶药膏 | 12.72% |
| 涅奥的骨骰 | 13.01% |
| 松动羊毛剪 | 23.75% |
| 华美发束 | 23.22% |
| 白银熔炉 | 12.37% |

密林：

| 遗物 | 密林 |
|------|------|
| 诅咒珍珠 | 12.99% |
| 沉重石板 | 23.79% |
| 巨大扭蛋 | 23.24% |
| 树叶药膏 | 12.39% |
| 涅奥的骨骰 | 11.90% |
| 松动羊毛剪 | 1.35% |
| 华美发束 | 1.65% |
| 白银熔炉 | 12.70% |

回到巨大扭蛋本身：和涅奥的骨骰类似，这种相关性对游戏平衡有实质影响。这件遗物平均来说比它「理应」的更强。

那**小型扭蛋**呢？

## 小型扭蛋

小型扭蛋不是诅咒池遗物，因此不像涅奥的骨骰和巨大扭蛋那样有内在偏差。

但这也意味着：我们可以根据是否出现了另一件诅咒池遗物，来预测小型扭蛋遗物的稀有度：

（\[U\] = 暗港，\[O\] = 密林。巨大扭蛋不会出现，因为有硬编码限制：两种扭蛋不能同时出现。）

<div class="barchartlgnd zh">
  <div><div class="bc0"></div>常见</div>
  <div><div class="bc1"></div>罕见</div>
  <div><div class="bc2"></div>稀有</div>
</div>
<div class="barchart zh">
  <div class="key">诅咒珍珠 [暗港]</div><div class="bar"><div style="width:33.74%" class="bc0"><span>4.58%</span></div><div style="width:6.75%" class="bc1"><span>0.92%</span></div><div style="width:9.76%" class="bc2"><span>1.33%</span></div></div>
  <div class="key">沉重石板 [暗港]</div><div class="bar"><div style="width:4.12%" class="bc0"><span>0.56%</span></div><div style="width:1.46%" class="bc2"><span>0.20%</span></div></div>
  <div class="key">树叶药膏 [暗港]</div><div class="bar"><div style="width:42.77%" class="bc0"><span>5.81%</span></div><div style="width:3.54%" class="bc1"><span>0.48%</span></div><div style="width:7.03%" class="bc2"><span>0.95%</span></div></div>
  <div class="key">涅奥的骨骰 [暗港]</div><div class="bar"><div style="width:54.64%" class="bc0"><span>7.42%</span></div></div>
  <div class="key">松动羊毛剪 [暗港]</div><div class="bar"><div style="width:99.81%" class="bc1"><span>13.56%</span></div></div>
  <div class="key">华美发束 [暗港]</div><div class="bar"><div style="width:97.80%" class="bc1"><span>13.28%</span></div></div>
  <div class="key">白银熔炉 [暗港]</div><div class="bar"><div style="width:52.14%" class="bc0"><span>7.08%</span></div></div>
  <div class="key">诅咒珍珠 [密林]</div><div class="bar"><div style="width:41.99%" class="bc0"><span>5.70%</span></div><div style="width:12.64%" class="bc2"><span>1.72%</span></div></div>
  <div class="key">沉重石板 [密林]</div><div class="bar"><div style="width:80.70%" class="bc1"><span>10.96%</span></div><div style="width:19.30%" class="bc2"><span>2.62%</span></div></div>
  <div class="key">树叶药膏 [密林]</div><div class="bar"><div style="width:33.95%" class="bc0"><span>4.61%</span></div><div style="width:18.27%" class="bc1"><span>2.48%</span></div></div>
  <div class="key">涅奥的骨骰 [密林]</div><div class="bar"><div style="width:16.43%" class="bc0"><span>2.23%</span></div><div style="width:8.38%" class="bc1"><span>1.14%</span></div><div style="width:25.41%" class="bc2"><span>3.45%</span></div></div>
  <div class="key">松动羊毛剪 [密林]</div><div class="bar"><div style="width:5.67%" class="bc0"><span>0.77%</span></div></div>
  <div class="key">华美发束 [密林]</div><div class="bar"><div style="width:6.92%" class="bc0"><span>0.94%</span></div></div>
  <div class="key">白银熔炉 [密林]</div><div class="bar"><div style="width:10.47%" class="bc0"><span>1.42%</span></div><div style="width:26.90%" class="bc1"><span>3.65%</span></div><div style="width:15.77%" class="bc2"><span>2.14%</span></div></div>
</div>

（条形图比例与上一节两张图相同——每行总宽度与该诅咒池遗物在本幕中的实际出现频率成正比。）

这展示了一个简洁的经验法则：**小型扭蛋在暗港通常会给出普通遗物，在密林通常会给出罕见或稀有遗物**。

涅奥带随机性的选项还有很多，这里加快节奏过几个，然后换点别的内容。

## 树叶药膏与沉重石板

（分别是「变化 2 张」和「选择一张稀有牌」。）

两者都是诅咒池遗物，因此有内在偏差。但它们都会生成多张牌，我们只能预测第一张。

结果是：**树叶药膏的第一次变化只有 22 种可能**（每个角色 80 张牌池中的子集），其中一些明显更常见。

以下图表按原文做成可折叠区块，可点击角色按钮切换查看。

<details class="chart-details" open>
<summary>树叶药膏</summary>

<p><strong>暗港：</strong></p>
<div class="barchartbtns">
<button type="button" class="clad active" data-btn="leafy-u" data-idx="0">铁甲战士</button>
<button type="button" class="silent" data-btn="leafy-u" data-idx="1">静默猎手</button>
<button type="button" class="regent" data-btn="leafy-u" data-idx="2">储君</button>
<button type="button" class="necro" data-btn="leafy-u" data-idx="3">亡灵契约师</button>
<button type="button" class="defect" data-btn="leafy-u" data-idx="4">故障机器人</button>
</div>
<div class="barchart">
<div class='key' data-btn='leafy-u' data-keys='好勇斗狠|磨蚀|星位序列|来生|适应打击'>好勇斗狠</div><div class='bar'><div style='width:48.16539298547497%' class='bc0'><span>3.78%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='愤怒|触媒|武器库|女妖之嚎|万物一心'>愤怒</div><div class='bar'><div style='width:99.84310946910269%' class='bc0'><span>7.84%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='武装|精准|星界脉冲|荒疫打击|球状闪电'>武装</div><div class='bar'><div style='width:99.66597499873475%' class='bc0'><span>7.82%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='灰烬打击|杂技|锻打成型|碎骨|弹幕齐射'>灰烬打击</div><div class='bar'><div style='width:99.65332253656561%' class='bc0'><span>7.82%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='壁垒|肾上腺素|下去！|预借时间|光束射线'>壁垒</div><div class='bar'><div style='width:99.87600587074245%' class='bc0'><span>7.84%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='战斗专注|余像|大爆炸|埋葬|高速脱离'>战斗专注</div><div class='bar'><div style='width:99.62548711979352%' class='bc0'><span>7.82%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='血墙|预判|黑洞|钙化|启动流程'>血墙</div><div class='bar'><div style='width:99.69127992307303%' class='bc0'><span>7.83%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='放血|刺杀|轰击|虚空之唤|缓冲'>放血</div><div class='bar'><div style='width:99.59259071815376%' class='bc0'><span>7.82%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='重锤|后空翻|铸墙|捕捉灵魂|暴涨'>重锤</div><div class='bar'><div style='width:99.73682878688193%' class='bc0'><span>7.83%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='全身撞击|背刺|新生之喜|洁净|扩容'>全身撞击</div><div class='bar'><div style='width:100.0%' class='bc0'><span>7.85%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='烙印|墨之刃|天穹之力|倒数计时|混沌'>烙印</div><div class='bar'><div style='width:51.217166860671085%' class='bc0'><span>4.02%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='恶魔之焰|独门技术|创世纪|取回|超越光速'>恶魔之焰</div><div class='bar'><div style='width:20.254061440356292%' class='bc0'><span>1.59%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='与我一战！|暴露|微光|重压|聚变'>与我一战！</div><div class='bar'><div style='width:27.4001720734855%' class='bc0'><span>2.15%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='火焰屏障|刀扇|流光溢彩|友谊|遗传算法'>火焰屏障</div><div class='bar'><div style='width:27.66840427147123%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='被遗忘的仪式|终结技|辉光|守墓人|冰川'>被遗忘的仪式</div><div class='bar'><div style='width:27.65322131686826%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='破灭|飞镖|护驾！！！|坟冢爆射|玻璃工艺'>破灭</div><div class='bar'><div style='width:27.6380383622653%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='头槌|翻越撑击|引导之星|吊杀|眼部攻击'>头槌</div><div class='bar'><div style='width:27.673465256338883%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='地狱狂徒|跟进|天际钻头|纠缠|污秽攻击'>地狱狂徒</div><div class='bar'><div style='width:27.69623968824333%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='御血术|灵动步法|霸权|击掌|冰雹风暴'>御血术</div><div class='bar'><div style='width:27.76203249152285%' class='bc0'><span>2.18%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='彼岸咆哮|华丽收场|传承之锤|唤起|螺旋钻击'>彼岸咆哮</div><div class='bar'><div style='width:27.67599574877271%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='岿然不动|手上技法|隐秘藏品|致死性|全息影像'>岿然不动</div><div class='bar'><div style='width:27.678526241206537%' class='bc0'><span>2.17%</span></div></div>
<div class='key' data-btn='leafy-u' data-keys='地狱之刃|迷雾|所向无敌|忧郁|热修复'>地狱之刃</div><div class='bar'><div style='width:7.601599271218179%' class='bc0'><span>0.60%</span></div></div>
</div>

<p><strong>密林：</strong></p>
<div class="barchartbtns">
<button type="button" class="clad active" data-btn="leafy-o" data-idx="0">铁甲战士</button>
<button type="button" class="silent" data-btn="leafy-o" data-idx="1">静默猎手</button>
<button type="button" class="regent" data-btn="leafy-o" data-idx="2">储君</button>
<button type="button" class="necro" data-btn="leafy-o" data-idx="3">亡灵契约师</button>
<button type="button" class="defect" data-btn="leafy-o" data-idx="4">故障机器人</button>
</div>
<div class="barchart">
<div class='key' data-btn='leafy-o' data-keys='熔融之拳|谋划专家|君权自授|书页风暴|机器学习'>熔融之拳</div><div class='bar'><div style='width:8.114362112408083%' class='bc0'><span>0.64%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='时候未到|铭记死亡|王之凝视|领会|陨石打击'>时候未到</div><div class='bar'><div style='width:28.13287396513601%' class='bc0'><span>2.20%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='祭品|蜃景|独白|戳击|模组改造'>祭品</div><div class='bar'><div style='width:28.14058723710598%' class='bc0'><span>2.20%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='连环拳|谋杀|中子护盾|吸引仇恨|趁势打击'>连环拳</div><div class='bar'><div style='width:28.09687869594282%' class='bc0'><span>2.20%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='契约终结|夜魇|环绕轨道|亡魂牵引|多重释放'>契约终结</div><div class='bar'><div style='width:28.256286316655526%' class='bc0'><span>2.21%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='完美打击|毒雾|暗淡蓝点|腐败|空值'>完美打击</div><div class='bar'><div style='width:28.197151231552425%' class='bc0'><span>2.21%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='劫掠|毒性爆发|招架|猛晃|超频'>劫掠</div><div class='bar'><div style='width:28.16115596235923%' class='bc0'><span>2.21%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='剑柄打击|幻影之刃|粒子墙|死者苏生|彩虹'>剑柄打击</div><div class='bar'><div style='width:28.19200905023911%' class='bc0'><span>2.21%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='原始力量|尖啸|星星点点|收割|重启'>原始力量</div><div class='bar'><div style='width:28.179153596955828%' class='bc0'><span>2.21%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='薪火之源|精密瞄准|光子切割|死神形态|折射'>薪火之源</div><div class='bar'><div style='width:28.143158327762638%' class='bc0'><span>2.20%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='狂怒|带毒刺击|创世之柱|剥夺|火箭飞拳'>狂怒</div><div class='bar'><div style='width:20.21648583329048%' class='bc0'><span>1.58%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='重振精神|猎杀者|辐射|鞭打|暗影之盾'>重振精神</div><div class='bar'><div style='width:50.951303542962926%' class='bc0'><span>3.99%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='预备打击|早有准备|淬炼刀刃|雕琢打击|打碎'>预备打击</div><div class='bar'><div style='width:99.4677842340721%' class='bc0'><span>7.79%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='耸肩无视|本能反应|倒映|降灵|信号增强'>耸肩无视</div><div class='bar'><div style='width:99.75574638761763%' class='bc0'><span>7.81%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='怨恨|连续反弹|共鸣|哨卫模式|快速检索'>怨恨</div><div class='bar'><div style='width:99.5680567696817%' class='bc0'><span>7.80%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='惊逃|群蛇形态|胜券在王|切断|烟囱'>惊逃</div><div class='bar'><div style='width:99.65804494266467%' class='bc0'><span>7.80%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='添柴|暗影步|王国资产|命运同担|旋转工艺'>添柴</div><div class='bar'><div style='width:99.39322260502905%' class='bc0'><span>7.78%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='踩踏|融入暗影|追踪之刃|厄运之衣|雷暴'>踩踏</div><div class='bar'><div style='width:99.34437188255258%' class='bc0'><span>7.78%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='岩石铠甲|串刺|七星|紧追不放|子程序'>岩石铠甲</div><div class='bar'><div style='width:100.0%' class='bc0'><span>7.83%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='飞剑回旋镖|切割|明耀打击|血肉戏法|分离'>飞剑回旋镖</div><div class='bar'><div style='width:99.11554481411015%' class='bc0'><span>7.76%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='挑衅|蛇咬|太阳打击|响指|超临界态'>挑衅</div><div class='bar'><div style='width:99.49349514063866%' class='bc0'><span>7.79%</span></div></div>
<div class='key' data-btn='leafy-o' data-keys='扯碎|速行者|光谱偏移|灵魂风暴|扫荡射线'>扯碎</div><div class='bar'><div style='width:48.30822234791999%' class='bc0'><span>3.78%</span></div></div>
</div>

</details>

类似地，**沉重石板在密林的第一次选项只有 11 种可能，在暗港只有 3 种**！正如上文所示，沉重石板在暗港本身大约只出现 1.3%，因此看到它本身就是极强的信息。

<details class="chart-details">
<summary>沉重石板</summary>

<p><strong>暗港：</strong></p>
<div class="barchartbtns">
<button type="button" class="clad active" data-btn="tablet-u" data-idx="0">铁甲战士</button>
<button type="button" class="silent" data-btn="tablet-u" data-idx="1">静默猎手</button>
<button type="button" class="regent" data-btn="tablet-u" data-idx="2">储君</button>
<button type="button" class="necro" data-btn="tablet-u" data-idx="3">亡灵契约师</button>
<button type="button" class="defect" data-btn="tablet-u" data-idx="4">故障机器人</button>
</div>
<div class="barchart">
<div class='key' data-btn='tablet-u' data-keys='势不可当|刀刃陷阱|传承之锤|死神形态|机器学习'>势不可当</div><div class='bar'><div style='width:100.0%' class='bc0'><span>72.52%</span></div></div>
<div class='key' data-btn='tablet-u' data-keys='扯碎|狩猎|铸剑者|大限已至|超临界态'>扯碎</div><div class='bar'><div style='width:23.126201153106983%' class='bc0'><span>16.77%</span></div></div>
<div class='key' data-btn='tablet-u' data-keys='痛殴|必备工具|暴政|重构|化废为宝'>痛殴</div><div class='bar'><div style='width:14.772581678411274%' class='bc0'><span>10.71%</span></div></div>
</div>

<p><strong>密林：</strong></p>
<div class="barchartbtns">
<button type="button" class="clad active" data-btn="tablet-o" data-idx="0">铁甲战士</button>
<button type="button" class="silent" data-btn="tablet-o" data-idx="1">静默猎手</button>
<button type="button" class="regent" data-btn="tablet-o" data-idx="2">储君</button>
<button type="button" class="necro" data-btn="tablet-o" data-idx="3">亡灵契约师</button>
<button type="button" class="defect" data-btn="tablet-o" data-idx="4">故障机器人</button>
</div>
<div class="barchart">
<div class='key' data-btn='tablet-o' data-keys='势不可当|刀刃陷阱|传承之锤|死神形态|机器学习'>势不可当</div><div class='bar'><div style='width:26.14622814525003%' class='bc0'><span>4.52%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='凌虐|萎靡|所向无敌|献祭|陨石打击'>凌虐</div><div class='bar'><div style='width:58.818315197456904%' class='bc0'><span>10.17%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='时候未到|谋划专家|如此甚好|降灵|模组改造'>时候未到</div><div class='bar'><div style='width:58.848881281330236%' class='bc0'><span>10.17%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='祭品|谋杀|王之凝视|哨卫模式|多重释放'>祭品</div><div class='bar'><div style='width:44.238293189876515%' class='bc0'><span>7.65%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='连环拳|夜魇|中子护盾|命运同担|彩虹'>连环拳</div><div class='bar'><div style='width:35.40316664628928%' class='bc0'><span>6.12%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='契约终结|群蛇形态|王国资产|灵魂风暴|重启'>契约终结</div><div class='bar'><div style='width:92.4853282797408%' class='bc0'><span>15.99%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='原始力量|暗影步|追踪之刃|灰烬之灵|打碎'>原始力量</div><div class='bar'><div style='width:75.13907568162367%' class='bc0'><span>12.99%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='薪火之源|融入暗影|七星|榨取|信号增强'>薪火之源</div><div class='bar'><div style='width:100.0%' class='bc0'><span>17.29%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='添柴|钢铁风暴|剑圣|巨镰|旋转工艺'>添柴</div><div class='bar'><div style='width:52.280229856950726%' class='bc0'><span>9.04%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='扯碎|狩猎|铸剑者|大限已至|超临界态'>扯碎</div><div class='bar'><div style='width:32.4734075070302%' class='bc0'><span>5.61%</span></div></div>
<div class='key' data-btn='tablet-o' data-keys='痛殴|必备工具|暴政|重构|化废为宝'>痛殴</div><div class='bar'><div style='width:2.590475608265069%' class='bc0'><span>0.45%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:50.322327176870175%' class='bc0'><span>11.91%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:5.666706095067507%' class='bc0'><span>1.34%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:7.073032663613782%' class='bc0'><span>1.67%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:53.33817739400801%' class='bc0'><span>12.63%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:53.145119045607395%' class='bc0'><span>12.58%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:35.59075009716285%' class='bc0'><span>8.42%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:46.53551090758546%' class='bc0'><span>11.02%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:52.37584278206796%' class='bc0'><span>12.40%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:50.76823686134677%' class='bc0'><span>10.14%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:74.37173849898336%' class='bc0'><span>14.85%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:100.0%' class='bc0'><span>19.97%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:69.00710143330762%' class='bc0'><span>13.78%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:49.28935586293933%' class='bc0'><span>9.84%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:49.515720309698615%' class='bc0'><span>9.89%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:25.903204158695498%' class='bc0'><span>5.17%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:31.009925980829134%' class='bc0'><span>6.19%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:50.94101503420507%' class='bc0'><span>10.17%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:66.62888995223345%' class='bc0'><span>HelloWorld (66.63%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:98.82212613687193%' class='bc0'><span>Outmaneuver (98.82%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.035835871707579285%' class='bc0'><span>HelloWorld (0.04%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.08395374623792175%' class='bc0'><span>Entrench (0.08%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:76.61197346017882%' class='bc0'><span>Caltrops (76.61%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:57.60700586356647%' class='bc0'><span>Clash (57.61%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.5614478222955355%' class='bc0'><span>Clash (0.56%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.8323788937103773%' class='bc0'><span>Caltrops (0.83%)</span></div></div>
<div class='key'></div><div class='bar'><div style='width:16.93695266868976%' class='bc0'><span>16.85%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:51.487403231380355%' class='bc0'><span>51.23%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:96.51294763243519%' class='bc0'><span>96.02%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:97.70613975208082%' class='bc0'><span>97.21%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:84.72409532667795%' class='bc0'><span>84.30%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:100.0%' class='bc0'><span>99.49%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:13.15077174648483%' class='bc0'><span>13.08%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:73.27095404511932%' class='bc0'><span>72.90%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:37.27241273999929%' class='bc0'><span>37.08%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:6.644627784853899%' class='bc0'><span>6.61%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:25.52846840454035%' class='bc0'><span>10.58%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:13.811663257823296%' class='bc0'><span>5.72%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:46.077341987306234%' class='bc0'><span>19.09%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:100.0%' class='bc0'><span>41.44%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:56.02459705982269%' class='bc0'><span>23.22%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:38.82157288072348%' class='bc0'><span>16.09%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:36.775155648876726%' class='bc0'><span>15.24%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:0.0%' class='bc0'><span>0%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:60.770476399912035%' class='bc0'><span>60.77%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:90.99784809117718%' class='bc0'><span>91.00%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:55.067696319326046%' class='bc0'><span>55.07%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:23.139968492631663%' class='bc0'><span>23.14%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:4.5375427645399435%' class='bc0'><span>4.54%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:46.09254550187213%' class='bc0'><span>46.09%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:8.503346827528157%' class='bc0'><span>8.50%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:32.222555789052336%' class='bc0'><span>32.22%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:47.16743902000934%' class='bc0'><span>47.17%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:75.02786967779056%' class='bc0'><span>75.03%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:3.627849905717405%' class='bc0'><span>3.63%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:4.306172839506173%' class='bc0'><span>4.31%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:33.98451931481298%' class='bc0'><span>33.98%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:56.829202343397924%' class='bc0'><span>56.83%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:33.38835264989773%' class='bc0'><span>33.39%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:84.14430665163472%' class='bc0'><span>84.14%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:2.631389164337871%' class='bc0'><span>2.63%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:19.36590262673582%' class='bc0'><span>19.37%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:36.635457565690125%' class='bc0'><span>36.64%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:69.32701652089408%' class='bc0'><span>69.33%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:39.00023579344494%' class='bc0'><span>39.00%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:29.190942491276076%' class='bc0'><span>29.19%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:9.54181438472097%' class='bc0'><span>9.54%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:33.77296887518199%' class='bc0'><span>33.77%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:69.43555426243817%' class='bc0'><span>69.44%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:36.77564408580624%' class='bc0'><span>36.78%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:90.85422235671895%' class='bc0'><span>90.85%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:89.55841608012528%' class='bc0'><span>89.56%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:71.41657651257044%' class='bc0'><span>71.42%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:1.3423608077685563%' class='bc0'><span>1.34%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:36.286606213765424%' class='bc0'><span>36.29%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:68.04374240583232%' class='bc0'><span>68.04%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:12.9794439631409%' class='bc0'><span>12.98%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:15.651453720735383%' class='bc0'><span>15.65%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:39.992032467694145%' class='bc0'><span>39.99%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:46.56958131944008%' class='bc0'><span>46.57%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:16.522729548412936%' class='bc0'><span>16.52%</span></div></div>
<div class='key'></div><div class='bar'><div style='width:42.19390360875469%' class='bc0'><span>42.19%</span></div></div>
</div>

</details>

## 新叶与奥术卷轴

（分别是「变化 1 张」和「随机稀有牌」。）

与小型扭蛋类似，幕别和诅咒池选项都会影响这两件遗物。

完整列出 14 种「幕别 × 诅咒池遗物」组合的卡牌表会占太多篇幅，概括来说：根据你的幕别和涅奥选项，**新叶**的可能变化可以缩小到 **4～39 种**（共 80 种），**奥术卷轴**的可能卡牌可以缩小到 **3～12 种**（共 25 种）。

有一个有趣的小细节：如果你在密林看到**松动羊毛剪**（相当罕见），那么**新叶**约有 70% 概率给出你角色按字母排序的第一张牌，**奥术卷轴**约有 65% 概率给出你角色按字母排序的第一张稀有牌。

好了，说实话，到这一步，大部分内容其实不会改变你的打法。来点更能影响决策的吧？

## 闪电充能球与随机目标

暗港简单怪物池有两个多敌战斗：**噬尸蛞蝓**和**蟾蜍蝌蚪**。如果你是**故障机器人**，可能想知道第一个闪电充能球打向哪里，尤其当你第一回合抽到**双重释放**时。

在暗港的第一场战斗中，**你的第一个充能球有 75% 概率打向左侧敌人**。（无论你打出双重释放激发它，还是不打出、靠被动触发，都适用。）如果你记得看到了哪件诅咒池遗物，可以预测得更准：

| 诅咒池遗物 | 左侧 | 右侧 |
|-----------|------|------|
| 诅咒珍珠 | 11.91% | |
| 沉重石板 | 1.34% | |
| 巨大扭蛋 | 1.67% | |
| 树叶药膏 | 12.63% | |
| 涅奥的骨骰 | 12.58% | 0.52% |
| 松动羊毛剪 | 8.42% | 15.25% |
| 华美发束 | 11.02% | 12.26% |
| 白银熔炉 | 12.40% | |

在**噬尸蛞蝓**战斗中还能预测得更准——该战斗有随机起始攻击模式。原文作者未列出完整表格，但举个例子：如果你看到了松动羊毛剪，**且**右侧噬尸蛞蝓在施加减益，那么你的充能球实际上有超过 95% 概率打向右侧那只。

（顺便说一句，第二层噬尸蛞蝓在第一回合双方都攻击的概率不到 3%。它们可真客气！）

这适用于整局游戏第一次随机战斗目标——例如，你可以预测**亡灵契约师**第一次**倒数计时**触发，或任何人第一次**招架盾**触发。

说到第一幕前期，终于来到开篇的另外两个例子。

## 垃圾堆

**垃圾堆**是暗港专属事件，因此有内在偏差。以下是垃圾堆 RNG 在幕别 RNG roll 出暗港时的输出：

| 卡牌 | 概率 |
|------|------|
| 铁蒺藜 | 10.14% |
| 交锋 | 14.85% |
| 声东击西 | 19.97% |
| 双持 | 13.78% |
| 巩固 | 9.84% |
| 你好世界 | 9.89% |
| 抢占先机 | 5.17% |
| 弹回 | 0% |
| 狂乱撕扯 | 6.19% |
| 堆栈 | 10.17% |

如你所见，在单人模式中**根本不可能**获得**弹回**这张牌。[^3]

如果你关心遗物预测：连续两张卡牌对应**黑石护符**、**捕梦网**、**手钻**、**巨口储蓄罐**和**发条靴**（例如，卡牌是巩固或你好世界时，遗物是手钻）。

若你想更精确地预测垃圾堆，还可以进一步根据看到的诅咒池遗物条件化：[^4]

| 诅咒池遗物 | 可能卡牌（概率） |
|-----------|----------------|
| 诅咒珍珠 | 你好世界 (66.63%)；抢占先机 (32.26%)；狂乱撕扯 (0.43%)；堆栈 (0.69%) |
| 沉重石板 | 抢占先机 (98.82%)；狂乱撕扯 (1.18%) |
| 巨大扭蛋 | 你好世界 (0.04%)；抢占先机 (0.26%)；狂乱撕扯 (99.70%) |
| 树叶药膏 | 巩固 (0.08%)；你好世界 (0.26%)；狂乱撕扯 (35.29%)；堆栈 (64.36%) |
| 涅奥的骨骰 | 铁蒺藜 (76.61%)；交锋 (8.24%)；双持 (0.14%)；巩固 (0.18%)；堆栈 (14.82%) |
| 松动羊毛剪 | 交锋 (57.61%)；声东击西 (42.16%)；双持 (0.23%) |
| 华美发束 | 交锋 (0.56%)；声东击西 (42.90%)；双持 (56.54%) |
| 白银熔炉 | 铁蒺藜 (0.83%)；交锋 (0.03%)；双持 (4.40%)；巩固 (79.10%)；你好世界 (15.46%)；堆栈 (0.18%) |

发现这一点后，我在网上搜索相关讨论，确实有人注意到似乎无法完成**百科大全**。我还发现 Discord 用户 @hoge 大约一个月前就精准描述了这个问题。向他们致敬！

## 药水掉落与？房间战斗

最后是开篇第三点——第一场战斗掉落药水的频率？套路你已经熟了：

| 诅咒池遗物 | 暗港 | 密林 |
|-----------|------|------|
| 诅咒珍珠 | 16.85% | 0% |
| 沉重石板 | 0% | 0% |
| 巨大扭蛋 | 0% | 0% |
| 树叶药膏 | 51.23% | 0% |
| 涅奥的骨骰 | 96.02% | 13.08% |
| 松动羊毛剪 | 97.21% | 72.90% |
| 华美发束 | 84.30% | 37.08% |
| 白银熔炉 | 99.49% | 6.61% |

再次提醒：沉重石板和巨大扭蛋在暗港极为罕见，华美发束和松动羊毛剪在密林极为罕见。综合考量后，**第一场战斗掉落药水的总概率在暗港是 76%，在密林仅 4%**！

但要注意：选择任何会生成卡牌奖励或随机遗物的涅奥选项都会破坏这种相关性，因为它会「偷走」奖励 RNG 的第一次调用。因此在糟糕的密林地图上，**失物盒**可能看起来比平均更有吸引力。

额外福利：第一个？房间是战斗的概率分布也相当不均：

| 诅咒池遗物 | 暗港 | 密林 |
|-----------|------|------|
| 诅咒珍珠 | 10.58% | 23.22% |
| 沉重石板 | 0% | 16.09% |
| 巨大扭蛋 | 0% | 15.24% |
| 树叶药膏 | 5.72% | 0% |
| 涅奥的骨骰 | 19.09% | 0% |
| 松动羊毛剪 | 0% | 0% |
| 华美发束 | 0% | 0% |
| 白银熔炉 | 41.44% | 0% |

（按幕别平均后，暗港约 9.6%，密林约 10.4%，大体持平。）

到目前为止，以上内容都只适用于第一幕。但——你猜对了——还能走得更远……

## 玩偶室

**玩偶室**是第二幕的事件。和大多数事件一样，它使用自己的 RNG，因此可以与所有其他 RNG 的第一次调用相关联。

到游戏这个阶段，你已经目睹了极大量「各 RNG 的第一次调用」，仅凭已有信息大概就能以很高精度预测玩偶室。但即便只用涅奥选项也已经相当不错：

（下表为点击「一个玩偶」选项时获得的玩偶。）

| 诅咒池遗物 | 风的女儿 | 抱抱先生 | 宾邦 |
|-----------|---------|---------|------|
| 诅咒珍珠 | 60.77% | 7.66% | 31.57% |
| 沉重石板 | 91.00% | 9.00% | |
| 巨大扭蛋 | 55.07% | 44.35% | 0.58% |
| 树叶药膏 | 23.14% | 70.81% | 6.05% |
| 涅奥的骨骰 | 4.54% | 70.38% | 25.08% |
| 松动羊毛剪 | 46.09% | 53.91% | |
| 华美发束 | 8.50% | 91.50% | |
| 白银熔炉 | 32.22% | 9.89% | 57.88% |

「两个玩偶」选项可由「一个玩偶」结果推导：

| 一个玩偶 | → | 两个玩偶 |
|---------|---|---------|
| 风的女儿 | → | 风的女儿 + 抱抱先生 |
| 抱抱先生 | → | 抱抱先生 + 宾邦 |
| 宾邦 | → | 宾邦 + 风的女儿 |

因此，如果你roll到了沉重石板且想保证拿到抱抱先生，或者roll到了松动羊毛剪/华美发束且想保证拿到宾邦，只需支付 5 点生命，它**永远**会是可选项之一。

你可能注意到玩偶分布与暗港/密林分布颇为相似。事实上有一条更简单的规则：暗港局中，「一个玩偶」按钮约有 62% 是宾邦、4% 是风的女儿；密林则相反。

## 占卜

**水晶球**同样只出现在第二或第三幕。

它也有自己的 RNG，但这次第一个有趣的 RNG 调用是**第二次**，决定遗物箱放在哪里。[^5]

最容易关联的第二次 roll 是什么？有些信号非常强（例如第一家商店左上角那张牌），但追踪起来有点烦，因为它取决于第一次roll出的稀有度。

结果是：**你第一场战斗掉落的金币数量**是「奖励」RNG 的第二次 roll（第一次是是否掉落药水，见上文）。

下面是可以按金币数量查看分布的交互小部件（假设进阶 3+）：

<div class="divination-widget">
  <p><label>第一场战斗金币（进阶 3+）：<input id="divgold" type="number" min="7" max="15" value="7"></label></p>
  <p class="divination-note">下表为水晶球遗物箱落在各格子的概率（共 41 格，布局与原文一致）。</p>
  <div id="divination-grid"></div>
  <div id="divination-table-wrap"></div>
</div>
<script src="divination-widget.js"></script>

但这打开了一个全新的世界。还能通过关联第二次 roll 做什么？

## 先古之民奖励

能预测先古之民会极其强大。但不幸的是（或者说幸运的是——取决于你怎么看），战斗、精英、Boss 和先古之民都由 `RunState.Rng.UpFront` 负责roll，它会先大约调用 100 次来洗牌遗物列表。

你能做的是预测：**如果**某位先古之民出现，你会得到什么选项。例如，**佩尔第二选项**与第一场战斗金币的关系：

| 金币 | 佩尔之翼 | 佩尔之爪 | 佩尔之牙 | 佩尔的增生组织 |
|------|---------|---------|---------|--------------|
| 7 | 47.17% | 50.23% | | 2.60% |
| 8 | 75.03% | 16.04% | | 8.93% |
| 9 | 3.63% | 12.60% | 46.84% | 36.93% |
| 10 | 4.31% | 25.40% | 68.59% | 1.71% |
| 11 | 33.98% | 52.76% | | 13.25% |
| 12 | 56.83% | 40.97% | | 2.20% |
| 13 | 33.39% | 9.47% | 16.47% | 40.68% |
| 14 | 84.14% | 15.86% | | |
| 15 | 2.63% | 49.67% | 28.03% | 19.67% |

这些信息出乎意料地强，但很难立刻转化为行动，因为你不知道第二幕先古之民会不会是佩尔。但我想这意味着：如果你roll到 11 金币，就该立刻放弃**克隆**的梦想。（或者我想得太小了——13 金币意味着**完美打击**立刻进牌组……）

**特兹卡塔拉**第二选项也可以同样分析，但那些选项在第一幕大多不太能据此行动。另一方面，**特兹卡塔拉第一选项**包含**营养汤**，很可能影响你移除**打击**的优先级：

| 诅咒池遗物 | 烫嘴可可 | 美味饼干 | 营养汤 |
|-----------|---------|---------|--------|
| 诅咒珍珠 \[U\] | 19.37% | 67.89% | 12.74% |
| 沉重石板 \[U\] | 36.64% | 63.36% | |
| 巨大扭蛋 \[U\] | 69.33% | 30.67% | |
| 树叶药膏 \[U\] | 39.00% | 32.20% | 28.80% |
| 涅奥的骨骰 \[U\] | 29.19% | 70.81% | |
| 松动羊毛剪 \[U\] | 9.54% | 90.46% | |
| 华美发束 \[U\] | 33.77% | 66.23% | |
| 白银熔炉 \[U\] | 69.44% | 30.56% | |
| 诅咒珍珠 \[O\] | 36.78% | 63.22% | |
| 沉重石板 \[O\] | 90.85% | 9.15% | |
| 巨大扭蛋 \[O\] | 89.56% | 10.44% | |
| 树叶药膏 \[O\] | 71.42% | 28.58% | |
| 涅奥的骨骰 \[O\] | 1.34% | 32.13% | 66.52% |
| 松动羊毛剪 \[O\] | 36.29% | 63.71% | |
| 华美发束 \[O\] | 68.04% | 31.96% | |
| 白银熔炉 \[O\] | 12.98% | 67.89% | 19.13% |

（若出现松动羊毛剪——你可能用它移除了两张打击——则特兹第一选项有 88.75% 是营养汤。这特别好笑：我往 Discord 狂倒 CRNG 发现时，两个人发了悲伤截图，说移除了 2+ 张打击却看到营养汤。你猜怎么着，遗物栏里都有松动羊毛剪。我打破幻想时只有一点点愧疚。）

**欧洛巴斯**呢？它会先为毒液玻璃roll颜色、再在棱彩宝石和毒液玻璃之间选择，然后才选第一选项，因此我们实际上需要某个 RNG 的**第三次** roll。最容易拿到的是**第一场战斗奖励**：

| 第一场战斗奖励 | 放电异虾 | 玻璃眼珠 | 沙堡 | 宝石或玻璃 |
|--------------|---------|---------|------|-----------|
| 普通药水 | 15.65% | 23.77% | 37.93% | 22.65% |
| 罕见药水 | 39.99% | 28.81% | 1.63% | 29.58% |
| 稀有药水 | 46.57% | 23.14% | | 30.29% |
| 普通卡牌 | 16.52% | 23.65% | 37.47% | 22.36% |
| 罕见卡牌 | 42.19% | 27.85% | | 29.95% |

如果你拿到了药水，那是第三次 RNG roll；否则是第一张卡牌。还要注意：选择任何会给你卡牌或遗物的涅奥选项都会破坏这种相关性并引入新的相关性，此处不再展开。

这里可操作的或许是**放电异虾**的不均匀分布，可能影响你是否想选一张好的**注能**牌。

至于**达弗**和第三幕先古之民，它们都会洗较长的列表，调用 RNG 次数太多，难以干净地预测。

## 还有更多……

在杀戮尖塔一代，要从若干选项中选取时，大多数 RNG 会roll一个 0 到极大整数，再对选项数量取余。这意味着只有当被选取数量共享大量公因子时才能利用相关性，而这种情况并不常见。

在杀戮尖塔二代，选取时大多数 RNG 会roll一个 0 到 1 的小数，再按比例缩放。这意味着基本上**每一个** RNG 输出都会给其他**每一个** RNG 输出提供信息。

上文已经描述了许多具体的相关实例。但实际上，每一次第一次 roll 都可以与其他每一次第一次 roll 关联，第二次对第二次，以此类推。

为此，原文有一份很长但仍不完整的「第一次 roll」列表。记住，**所有这些**都会给**所有其他** roll 提供**某种**信息：

* 第一幕变体
* 涅奥诅咒池遗物
* 第一家商店见到的第一件普通遗物
* 第一场战斗你抽到的最后一张牌
* 第一个？房间的内容
* 战斗中生成的第一张牌（例如攻击药水）
* 战斗中随机选中的第一张牌（例如干瘪之手）
* 第一次随机能量费用（例如蛇行）
* 第一次随机敌人选择（例如闪电充能球）
* 第一次随机怪物 AI
* 第一次「niche RNG」结果（例如磨刀石）
* 化废为宝或混沌生成的第一个充能球
* 第一场战斗是否掉落药水
* 第一家商店打折的是哪张牌
* 佩尔或特兹卡塔拉第一选项
* 树叶药膏的第一次变化
* 有多首曲目幕别的音乐版本
* 异鸟宝宝或佩尔的士兵的外观皮肤
* 以下遭遇的行为：无尽传送带（初始提供食物）、直飞产卵虫（蛋的外观皮肤[^6]）、重拳出击（拳击构装体起始生命）、三只/四只史莱姆（两只小史莱姆顺序），以及任何随机起始意图的遭遇（例如双尾鼠）、任何随机敌人的遭遇（例如扼杀者的同伴）
* 以下事件的随机性：混沌芳香（变化）、色彩哲学家（提供的颜色）、水晶球（金币费用）、茂密的植被（金币数量）、玩偶室（任意按钮结果）、丛林迷宫奇遇（第一次金币数量）、冷光合唱团（金币费用）、变形灵林谷（第一次变化）、长者兰伟德（要求的药水）、镜中倒影（第一次降级牌）、永恒之石（要求的药水）、滑脚木桥（初始提供的牌）、淹水金库（第一次金币奖励）、共生体（变化）、真理石板（第一次升级）、药水的未来？（第一种卡牌类型）、迷失鬼火（金币数量）、沉没雕像（金币数量）、审判（哪种审判）、这个还是那个？（金币数量）、打造时间（缺失的卡牌类型）、垃圾堆（牌或遗物）、欢迎来到旺购百货（降级牌）、低语空谷（金币费用）

第二次 roll 的较短列表：

* 所有以「第一次」开头的条目，换成「第二次」
* 第一场战斗的金币奖励
* 第一家商店左上角那张牌
* 佩尔或特兹卡塔拉第二选项
* 你扮演的角色（若选择了「随机角色」[^7]）
* 以下事件的随机性：水晶球（遗物箱位置）、玩偶室（第二或第三按钮结果）、无尽传送带（变化/升级/下一份食物）、丛林迷宫奇遇（第二次金币数量）、变形灵林谷（第二次变化）、长者兰伟德（要求的遗物）、镜中倒影（第二张降级牌）、滑脚木桥（下一张牌）、淹水金库（第二次金币奖励）、真理石板（第二次升级）、药水的未来？（第二种卡牌类型）、审判（第一次变化）、打造时间（提供卡牌类型的顺序）、低语空谷（变化）

还能继续列，但希望我已经说明问题了。

## 致开发者

这个标题主要是对 Forgotten Arbiter 关于一代 CRNG 那篇文章的致敬。当然，我认为二代 CRNG 是一个 bug，应该修复；如果不修，对游戏会很糟糕。

不过我相信 Mega Crit 会处理这个问题。一方面，二代仍在抢先体验阶段，比一代发现 CRNG 时早得多。

而且与一代相比，CRNG 对不知道也不关心的玩家的影响要直接得多。例如，如果因为永远看不到**弹回**而无法完成游戏内**百科大全**，那就很不合理。其他相关性，例如涅奥的骨骰的诅咒分布，对平衡有显著影响，在一款刻意设计的策略游戏中没有理由放任存在。

幸运的是，**修复这个问题非常简单**。例如，用我随手写的这个 50 行即插即用替代品替换 `System.Random`，在杀戮尖塔2代码里改三行就能立刻消除所有相关性。（我不指望 Mega Crit 字面意义上照搬这段代码，他们全盘复制我也完全没问题；重点只是说明有多容易。）

若你对成因的技术细节和其他修复方案好奇，请阅读下方附录。

否则，几句收尾：我写这篇文章花了很多功夫，基本上完全是因为觉得有趣。文章长度与这个 bug 的严重性和规模完全不成比例。但希望你读得也开心！:)

---

## 附录：怎么发现的？

你可能会好奇：既然代码看起来明确是为了防止 CRNG 而写的，我是怎么意识到二代有 CRNG 的？事实上，如果对 C# 中 `System.Random` 的实现做一些非常合理的假设，杀戮尖塔的随机性本来会是完全没问题的。

我希望我能说我是读了代码、从第一性原理想到了这个缺陷——那会很酷。可惜，我没那么聪明。这完全是意外：在 jmac 最近通宵用**王国资产** + **光谱偏移**刷 200 万金币[^8] 期间，我受到启发写了一个种子搜索程序，寻找能在涅奥变化出**巨镰** + **虚空之唤**、并在第一场战斗拖住敌人、用**重构**无限次变化巨镰、把伤害叠到任意高度的种子。[^9]

种子搜索跑通了，我逐个添加条件。它成功找到了很多涅奥提供树叶药膏、且两次变化是巨镰和虚空之唤（某种顺序）的种子。但我还想让幕别是密林——密林有更多可拖时间的简单池，还有密林专属的「变化 2」事件，能在第三层再拿 2 把巨镰。

可我一加上密林条件，突然一个种子都找不到。我懵了，以为代码有 bug，但它仍然能大量生成暗港种子。

最后我让它检查其他条件，并打印用于决定幕别的 RNG 原始输出（小于 0.5 是暗港，否则是密林）。令我困惑的是，值不仅总是小于 0.5，而且总是非常接近 0.1。

除非确实存在某种相关性，否则这完全讲不通。为了确认相关性是否存在，我做了散点图：X 轴是变化 roll，Y 轴是幕别 roll。结果嘛，相当震撼。

![变化 roll 与幕别 roll 的散点图](images/transform_vs_act.png)

于是意外开始了对游戏中每一个其他 roll 的关联深挖。为留纪念，[我保存了这整段冒险的视频](https://youtu.be/kIBOvKzeNO0?t=8850)（链接大致指向我注意到不对劲的时刻）。

顺便说一句，我的虚空之唤 + 巨镰种子之所以不可能，是因为在密林且提供树叶药膏时，这两张牌都不可能成为第一次变化（[见树叶药膏表格](#树叶药膏与沉重石板)）。

## 附录：为什么？

如承诺，现在真正展示 C# 实现为何会导致这一切。

一句话总结：「输出与 abs(seed) 线性相关」——如果你懂这些词的意思。若不懂，或想要更具体的细节，下面是更完整的解释。

`System.Random` 的实际代码，直接摘自 .NET 参考源码：

```csharp
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
```

有两部分——构造函数（`public Random`）和最终生成随机数的函数（`int InternalSample`）。

首先，构造函数的大部分工作是用内部 `SeedArray` 状态初始化，最终将用于产生输出。最后一项设为某个常数减去种子的绝对值，然后以看似随机的顺序跳转设置其他项（乘 21 mod 55 就是在干这个）。下一项的值由前两项相减得到。

之后，再做 4 轮「从随机看似的项中互相相减」。这一切都在 mod 2^31-1 下进行（`MBIG` 行就是在处理这个，`MBIG` 设为 `Int32.MaxValue`）。

最后，当我们真正要一个随机数时，得到的值是 `SeedArray[1] - SeedArray[22]`。每次要新数字，这些索引递增（下一个是 `SeedArray[2] - SeedArray[23]`），必要时回绕。输出也会写回 `SeedArray`，替换某个旧值。

问题的根源是：这整个过程的唯一输入是种子的**绝对值**——记为 *S*——而 `SeedArray` 的每一项都是 **S 的线性函数**。意思是你可以把它们写成 x·*S* + y，其中 x、y 是某些整数。[^10]

为什么成立？`SeedArray` 里第一项是常数减 *S*，是线性的。构造函数里其他项都是已有两项之差。但**两个线性量之差仍是线性的**——(x₁·*S* + y₁) - (x₂·*S* + y₂) = (x₁-x₂)·*S* + (y₁-y₂)。所以无论做多少看似随机的减法，这个性质都保持。

`InternalSample` 也只包含减法。因此若用某个 *S* 建 RNG，第一次输出恰好是 x·*S* + y，x、y 是已知常数。但若用 *S*+1 建新 RNG，第一次输出会比另一个**恰好大 x**！一般地，*S* 相差 *d* 的两个 RNG，第一次输出相差恰好 x·*d*。

由于游戏中各 RNG 的种子相差已知固定量，这立刻给出我们想要的相关性。有一个小波折：*S* 是输入种子的**绝对值**。若 RNG 之间的固定偏移跨过 0，其中一个会多一次取负。这就是为什么上文散点图里既有正斜率也有负斜率的线。

顺便，网上也有关于 C# 默认随机生成器这一性质及其如何产生此类相关性的进一步讨论。

## 附录：怎么修？

具体怎么修？从最简单的方案说起。

朴素的一阶修复是用非线性运算生成不同 RNG 的种子，比如乘法。若对每个 RNG 把种子乘固定常数，而不是相加，线性带来的极易预测性就消失了。（或者，你也可以在选定运算之后对产出值再做 hash。）

但这仍不是很好的方案。它确实能解决弹回、涅奥的骨骰这类明显问题，但仍留下可 exploit 的细微空间。即使事先不知道精确偏移，只要对两个 RNG 流各取足够多样本，知道它们相差常数偏移仍可被利用。

最容易的「真正」修复，就是**实现一个非线性伪随机数生成器**。具有理想随机外观性质的 PRNG 是研究得很充分的领域，许多合适选项算法极其简单。我在主文示例实现里选的是 PCG32，但这相当随意，基本上任何现代算法都行。

在代码库内实现 PRNG、而非调用 C# 标准库，还有额外好处：**种子在所有平台上保证一致**。在一代中，桌面版与移动版的种子不同，因为各平台标准库 PRNG 实现不同。标准库实现也可能随时间变化，从而破坏所有历史种子。

额外提一个稍复杂的选项。杀戮尖塔保存并恢复一局的方式，是存储每个 RNG 被调用的总次数，加载存档时对每个 RNG 调用那么多次（丢弃结果）。这完全可行，但有点傻。另一种方案[^11]是**基于计数器的随机数生成器**，不存储内部状态。要第 *n* 个随机数，传入参数 *n*（也可以把内部状态想成每次调用加 1 的整数）。用这类 PRNG 并稍作修改游戏内部的 `Rng` 类，就不再需要「推进」过程。

---

[^1]: 本文标题和几个章节标题是对那篇文章的有意致敬。另外，Arbiter 你好，我相信你迟早会读到这篇 :)

[^2]: 实际上，涅奥的骨骰刚加入时，大家老是拿到愧疚——我猜测那个补丁的相关性不同，后来涅奥选项增多后变了，但我没去翻旧补丁源码核实。另外，Reddit 上那个贴了 9 张截图的楼主（顺便说全是暗港）完全不知道，他们关于疑虑和债务「字母上够接近」的玩笑其实完全正确——因为诅咒在内部是按字母排序的。

[^3]: 多人模式为何不同？因为事件 RNG 的偏移不仅包含对应事件的常数，还包含你的 Steam ID（多人模式下避免所有人得到相同结果）。单人模式默认为 1，以保证所有人的单人种子一致。这也意味着，若你 Steam ID 不幸，可能在多人模式也**永远**看不到弹回。真惨。

[^4]: 为可见性我把所有条形拉满，但这扭曲了表观总概率——沉重石板和巨大扭蛋在暗港都极为罕见，因此抢占先机实际上比看起来少见得多。

[^5]: 第一次调用决定第一个事件选项的随机生成金币价格。

[^6]: 蛋有两种不同皮肤，不知为何！单场战斗中所有蛋皮肤相同，但不同局之间会看到不同皮肤。

[^7]: 若你好奇：**静默猎手**是最「富」的角色（第一场战斗平均 13.4 金币），**亡灵契约师**最「穷」（平均 8.3 金币）。

[^8]: 我说的「期间」是字面意思——整个发现过程发生在他还在「打」那一局的时候。（我是在他还在睡觉、8 小时王国资产动画播到一半时开始的。）

[^9]: 即使敌人先死，伤害也会按完整次数叠加，这可能也是个 bug。希望 CRNG 修之前我还能做到。（或者希望别修，因为真执行起来可能很可怕。）

[^10]: 再次说明，一切都在 mod 2^31-1 下，下文默认如此。

[^11]: 其实还有另一种选择：实现支持高效「推进」函数的 PRNG。PCG32 就可以，但示例代码里我没实现，因为会显著增加复杂度、收益很小。

---

*翻译说明：卡牌与遗物中文名均参照仓库内《杀戮尖塔2》中英对照表 v1.3。原文中未展开的交互图表（如新叶/奥术卷轴的 14 种组合）在原文中亦未列出；噬尸蛞蝓充能球目标的完整表同理。其余可提取的数据表与交互部件均已收录。*
