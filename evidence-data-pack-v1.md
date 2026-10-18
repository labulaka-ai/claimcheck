# S69 Graph Hacks 证据图谱数据包 v1（赛前数据准备，2026-10-12）

性质：赛前允许范围内的**数据准备**，不含主要实现代码。数据源＝自家已组装进公众号草稿箱的三篇组（appmsgid=100000374，2026-10-11），每篇的结论与数字均已在写稿时核过并附支撑原句。
与 prep-plan-20261012.md 的出入：原计划候选写的第三篇是 Xaurora，实际三篇组是「全球火势 GNN / CLARA / GraphCast 可解释性」——本包按实际成稿的三篇建，Xaurora 与 OneStreamer、FairRSFM 留作备选扩容。

## 图谱 schema（沿用 prep-plan 草案）
- 节点：Paper / Claim / Evidence / Counterexample / Method / Dataset
- 边：Claim -SUPPORTED_BY-> Evidence；Claim -CONTRADICTED_BY-> Counterexample；Paper -TESTED_BY-> Method；Evidence -DERIVED_FROM-> Dataset
- 问答目标：agent 沿图回答「这篇结论靠不靠谱、证据在哪、反例是什么」。

---

## Paper 1：全球火势 GNN 预报
- 论文：A Graph Neural Network for Global Daily Fire Radiative Power Prediction at Medium-Range Lead Times（Li Zhang、Jun Wang、Isidora Jankov 等，NOAA／科罗拉多大学博尔德分校）
- 来源：arXiv:2610.11022；自家稿：goals/ip/files/2026-10-11/wechat/a1-fire.md
- Method：时空图神经网络（格点按地理邻近连图），输入历史火点＋再分析气象＋地表覆盖/植被；2020–2022 训练，2023、2024 两年完整留出检验；对照业务在用的持续性预报。
- Dataset：卫星火点产品 GBBEPx（全球火灾辐射功率 FRP）。

| Claim | Evidence（自家已核数字） | Counterexample / 局限 |
|---|---|---|
| 提前 7 天报全球火势，误差显著低于业务持续性预报 | 0.1° 分辨率 MSE：2023 年提前 1 天降 32%、7 天降 43%；2024 年降 24% 与 40% | 优势随时效拉长反而变大，是因为「不变」假设错得更离谱——不等于 7 天绝对精度高 |
| 业务流程的火源数据严重过期 | 卫星火点产品约 1.5 天延迟，且在随后 5 天业务预报中被原样冻结（实验版冻结 7 天） | 范围局限（非反驳结论）：此过期口径只描述一条业务链——NOAA GEFS-Aerosols 以 GBBEPx 为初始火源；其他中心的火源输入不在本文覆盖内 |
| 大火位置可靠 | 1° 分辨率火点探测临界成功指数 0.32–0.60，随时效拉长只缓慢下降 | 大火辐射功率被**系统性低估**；小火位置容易放错——强度校准与小火定位是作者自标的「上岗前两课」 |
| 结论可信度边界 | 训练与检验同为 GBBEPx 口径 | 真实业务的观测噪声、产品换代未覆盖；预印本，未过同行评审 |

## Paper 2：CLARA 小参数联合概率预报
- 论文：Learning joint probabilistic weather forecasts from station observations alone（Chaeyeon Yi、Yun Am Seo，韩国外国语大学／济州国立大学）
- 来源：arXiv:2610.09898；自家稿：goals/ip/files/2026-10-11/wechat/a2-clara.md
- Method：带风向偏置的注意力（上风向位置随预报时效回推、权重随时效衰减）＋五变量联合高斯输出；只吃气象站观测，不用数值预报与再分析。
- Dataset：韩国自动气象站系统 96 站观测；预报时效 1–48 小时六档。

| Claim | Evidence | Counterexample / 局限 |
|---|---|---|
| 极小模型即可做联合概率预报 | 约 2.8 万参数；普通 CPU 训 40 轮 2.1 分钟；96 站一次预报 0.43 毫秒 | 范围局限（非反驳结论）：仅在 96 站、1–48 小时、五变量的规模上得到验证；业务级网格规模上无本文证据 |
| 泛化稳定 | 六大洲十个地区重训，60 组地区—时效对比全胜持续性预报；对同量级学习型模型赢 57 组；能量评分比同输入对手低 4.9%、比统计基线低 11%–65% | 胜的是持续性与同量级基线，未与业务级数值预报正面对打 |
| 变量间相关是真实信息、不是装饰 | 消融：拆掉学到的相关、只留方差，联合预报负对数似然每站变差 1.0–2.8 | 作者自曝：注意力偏置系数不能直接当「哪个站影响了预报」的因果证据 |
| 结论可信度边界 | 协方差尺度估计量有一致性证明 | 长时效下证明前提先破、会过度修正；联合分布用高斯假设，极端尾部（复合灾害最要命处）未必描得准；预印本 |

## Paper 3：GraphCast 内部概念可解释性
- 论文：Mechanistic Interpretability of Atmospheric Rivers in GraphCast（Madelyn Mathai 等，弗吉尼亚大学）
- 来源：arXiv:2610.07583；代码 github.com/AikyamLab/climate_xai；自家稿：goals/ip/files/2026-10-11/wechat/a3-graphcast.md
- Method：稀疏自编码器（Matryoshka 变体）在 GraphCast 处理器第 0/8/15 层装「概念字典」（512 维激活→4096 条目），逐概念对照真实大气现象，并做内部激活干预实验验因果。
- Dataset：GraphCast 内部激活 vs 大气河现象与 IVT（整层水汽输送）诊断量。

| Claim | Evidence | Counterexample / 局限 |
|---|---|---|
| 没人教过 IVT，GraphCast 内部却稳定地算着它 | IVT 从未作为输入或预报目标出现，内部激活中被稳定检出；概念跨处理器不同深度持续存在 | 相关 0.51 是「概念被检出」的证据，不是模型对 IVT 的计算精度 |
| 最强概念与大气河强度对应 | 编号 99「全球大气河」概念与区域最大 IVT 全时段平均相关 0.51；编号 1592 专对北美西岸强 IVT 响应；概念有父子层级（99 为父概念） | 范围局限（非反驳结论）：全时段平均相关 0.51，意味着单一最强概念仍漏掉大部分 IVT 方差；且响应强度有区域性（1592 号概念专对北美西岸强 IVT） |
| 概念是模型真在用的，不是旁观相关 | 直接干预内部激活，预报随之改变 | 干预证据只在大气河这一类现象上完整取得 |
| 结论可信度边界 | 代码已开源，可复现 | 只在**大气河一类现象**上完整验证；锋面、阻塞高压等现象未验；预印本 |

---

## 赛期使用方式（10-15 开赛后）
1. 按上表直接入图：3 Paper / 12 Claim / 每 Claim 至少 1 Evidence＋1 Counterexample（三条为范围局限口径，已标注非反驳结论；2026-10-17 由原「9 Claim」口径更正，与构建器实数一致）。
2. 入图前检查借 st-qc 口径：数字必须能回指本包出处行，不许扩读（如火势篇的降幅只对持续性基线、CLARA 的胜场只对同量级基线）。
3. 备选扩容（有余力再加）：OneStreamer、FairRSFM（已发表，有自家数字）；Xaurora 待其稿审发后再入。
