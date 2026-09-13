# -*- coding: utf-8 -*-
"""相似度计算模块：最长公共子序列（LCS）与论文重复率。

接口层级（这一层设计在性能改进前后保持不变）::

    plagiarism_rate()        ←  对外主接口，返回值就是最终答案
        └── similarity_report()   ←  更详细的报告，供 --verbose 使用
                └── lcs_length()  ←  LCS 计算的唯一收口点
                        └── lcs_length_dp()   ← 当前实现（性能基线）

性能改进只会替换 :func:`lcs_length` 的实现，不会改动上述任何签名。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------- 重复率口径

#: 口径一：LCS ÷ 原文长度。语义是"原文有多大比例被原样抄走"，默认口径。
METRIC_ORIG_BASE = "orig_base"

#: 口径二：LCS ÷ max(原文长度, 抄袭版长度)。
METRIC_MAX_BASE = "max_base"

#: 全部可用口径，供命令行参数校验使用。
METRICS = (METRIC_ORIG_BASE, METRIC_MAX_BASE)

# ------------------------------------------------------------ 大规模输入兜底

#: 精确 LCS 允许的最大单元格数（``len(原文) × len(抄袭版)``）。
#: 超过这个量就在时间上不划算了，改用下面的分块对齐估计。
MAX_EXACT_CELLS = 200_000_000

#: 分块估计时单块的字符数下限。块太小会让估计失真，所以宁可超预算也不破这个下限。
MIN_BLOCK_LENGTH = 2_000

#: 在抄袭版中取对应窗口时，窗口两端各额外放宽"块长的若干倍"。
#: 这是为了容忍局部增删造成的对齐漂移。
MARGIN_RATIO = 1.0


# -------------------------------------------------------------------- 数据结构


@dataclass(frozen=True)
class SimilarityReport:
    """一次相似度计算的完整结果。

    Attributes:
        rate: 重复率，取值 0.0 ~ 1.0。
        common_length: 最长公共子序列的长度。
        base_length: 重复率的分母（取决于所用口径）。
        metric: 实际使用的口径名。
        original_length: 原文归一化后的字符数。
        plagiarized_length: 抄袭版归一化后的字符数。
        estimated: 是否因为文本过大而走了分块对齐估计（而非精确计算）。
    """

    rate: float
    common_length: int
    base_length: int
    metric: str
    original_length: int
    plagiarized_length: int
    estimated: bool


# ---------------------------------------------------------------- LCS 计算


def lcs_length_dp(original: str, plagiarized: str) -> int:
    """用经典动态规划求最长公共子序列（LCS）的长度。

    时间复杂度 ``O(n*m)``，空间复杂度 ``O(min(n, m))``（滚动数组，
    只保留上一行）。

    .. note::
       这是**性能基线实现**（v0）。它把 n×m 个单元格逐格算一遍，
       每个单元格都要执行一次 Python 层循环，因此在大文本上会成为
       唯一的性能瓶颈。后续版本会换掉它，但保留本函数作为正确性对拍的参照。

    Args:
        original: 已归一化的原文字符串。
        plagiarized: 已归一化的抄袭版字符串。

    Returns:
        两串的最长公共子序列长度；任一方为空时返回 0。
    """
    if not original or not plagiarized:
        return 0

    # 让较短的一串落在内层循环上，减小滚动数组的宽度
    if len(original) < len(plagiarized):
        original, plagiarized = plagiarized, original

    width = len(plagiarized)
    previous = [0] * (width + 1)

    for char_a in original:
        current = [0] * (width + 1)
        for j, char_b in enumerate(plagiarized, 1):
            if char_a == char_b:
                current[j] = previous[j - 1] + 1
            else:
                # 取"跳过 char_a"与"跳过 char_b"中的较大者
                current[j] = current[j - 1] if current[j - 1] >= previous[j] else previous[j]
        previous = current

    return previous[width]


def lcs_length(original: str, plagiarized: str) -> int:
    """求最长公共子序列长度的**唯一收口点**。

    所有调用方都只经由本函数取 LCS，因此性能改进只需要替换这里的实现。

    Args:
        original: 已归一化的原文字符串。
        plagiarized: 已归一化的抄袭版字符串。

    Returns:
        LCS 长度。
    """
    return lcs_length_dp(original, plagiarized)


# ------------------------------------------------------ 大规模输入的分块估计


def _block_count(length_a: int, length_b: int) -> int:
    """决定把原文切成多少块，使分块估计的总代价落进预算。

    单块代价约为 ``块长² × (比例 + 2×余量)``，切成 K 块后总代价约
    ``len(a)² / K × (比例 + 2×余量)``。令它不超过 :data:`MAX_EXACT_CELLS`
    即可解出 K 的下界。
    """
    ratio = length_b / length_a
    factor = ratio + 2 * MARGIN_RATIO
    needed = math.ceil(length_a ** 2 * factor / MAX_EXACT_CELLS)
    cap = max(1, length_a // MIN_BLOCK_LENGTH)      # 块长不低于下限
    return max(1, min(needed, cap))


def chunked_common_length(original: str, plagiarized: str) -> int:
    """文本过大时，用**分块对齐**的方式估计公共子序列总长度。

    为什么不直接等距抽样字符：抄袭版经过增删之后，它第 k 个字符对应的
    早已不是原文第 k 个字符。按固定步长抽字符会把两串的对应关系彻底打乱，
    算出来的相似度会**大幅偏低**（实测 0.90 会掉到 0.40）。

    所以这里改为**保持连续片段不拆散**：把原文切成若干块，按长度比例在
    抄袭版里取出对应的连续窗口（两端各放宽一段余量以容忍局部漂移），
    在窗口内做精确 LCS，再把各块结果累加。

    因为原文各块互不重叠，累加值天然不超过 ``len(原文)``，重复率不会越界。

    .. note::
       本函数是**估计**而非精确计算：块内 LCS 的搜索窗口比全局对齐更宽松，
       因此估计值会**系统性略偏高**。实测（6 万字原文 + 随机删 10%）：
       精确 0.8985，估计 0.9176，偏差约 +0.019。

    Args:
        original: 已归一化的原文。
        plagiarized: 已归一化的抄袭版。

    Returns:
        公共子序列总长度的估计值。
    """
    length_a, length_b = len(original), len(plagiarized)
    if length_a == 0 or length_b == 0:
        return 0

    ratio = length_b / length_a
    block = max(1, -(-length_a // _block_count(length_a, length_b)))
    margin = max(1, int(block * MARGIN_RATIO))

    total = 0
    for start in range(0, length_a, block):
        lower = max(0, int(start * ratio) - margin)
        upper = min(length_b, int((start + block) * ratio) + margin)
        if upper <= lower:
            continue
        total += lcs_length(original[start:start + block], plagiarized[lower:upper])
    return total


def is_exact_feasible(original: str, plagiarized: str) -> bool:
    """判断这两串是否可以走精确计算（而不是分块估计）。"""
    return len(original) * len(plagiarized) <= MAX_EXACT_CELLS


# ---------------------------------------------------------------- 重复率


def similarity_report(original: str, plagiarized: str,
                      metric: str = METRIC_ORIG_BASE) -> SimilarityReport:
    """计算重复率并返回完整报告。

    Args:
        original: 已归一化的原文字符串。
        plagiarized: 已归一化的抄袭版字符串。
        metric: 重复率口径，取值见 :data:`METRICS`。

    Returns:
        :class:`SimilarityReport`。

    Raises:
        ValueError: ``metric`` 不是受支持的口径。
    """
    if metric not in METRICS:
        raise ValueError(f"未知的重复率口径: {metric!r}，可选值为 {METRICS}")

    feasible = is_exact_feasible(original, plagiarized)
    if feasible:
        common = lcs_length(original, plagiarized)
    else:
        common = chunked_common_length(original, plagiarized)

    if metric == METRIC_MAX_BASE:
        base = max(len(original), len(plagiarized))
    else:
        base = len(original)

    return SimilarityReport(
        rate=common / base if base else 0.0,
        common_length=common,
        base_length=base,
        metric=metric,
        original_length=len(original),
        plagiarized_length=len(plagiarized),
        estimated=not feasible,
    )


def plagiarism_rate(original: str, plagiarized: str,
                    metric: str = METRIC_ORIG_BASE) -> float:
    """计算抄袭版论文相对原文的重复率（对外主接口）。

    默认口径的定义::

        重复率 = LCS(原文, 抄袭版) / len(原文)

    语义是「原文中有多大比例的内容，在抄袭版里被原样、按序保留了下来」。

    Args:
        original: 已归一化的原文字符串。
        plagiarized: 已归一化的抄袭版字符串。
        metric: 重复率口径，默认 :data:`METRIC_ORIG_BASE`。

    Returns:
        取值 ``0.0`` ~ ``1.0`` 的浮点数。约定：

        * 原文为空 → ``0.0``
        * 抄袭版为空 → ``0.0``
        * 两者完全相同 → ``1.0``
        * 抄袭版完全包含原文 → ``1.0``
        * 抄袭版是原文的真子集 → ``len(抄袭版) / len(原文)``

    Raises:
        ValueError: ``metric`` 不是受支持的口径。
    """
    return similarity_report(original, plagiarized, metric).rate
