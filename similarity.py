# -*- coding: utf-8 -*-
"""相似度计算模块：最长公共子序列（LCS）与论文重复率。

对外只暴露一个接口 —— :func:`plagiarism_rate`。**这个签名在本项目中
自始至终不会变动**：性能改进只替换内部实现，不改变接口，这样"计算模块
接口部分的性能改进"才有前后可比的对象。
"""

from __future__ import annotations


def lcs_length_dp(original: str, plagiarized: str) -> int:
    """用经典动态规划求最长公共子序列（LCS）的长度。

    时间复杂度 ``O(n*m)``，空间复杂度 ``O(min(n, m))``（滚动数组，
    只保留上一行）。

    .. note::
       这是**性能基线实现**（v0）。它把 n×m 个单元格逐格算一遍，
       每个单元格都要执行一次 Python 层循环，因此在大文本上会成为
       唯一的性能瓶颈。后续版本会把它替换成位并行实现，但保留本函数
       作为正确性对拍的参照。

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


def plagiarism_rate(original: str, plagiarized: str) -> float:
    """计算抄袭版论文相对原文的重复率。

    定义::

        重复率 = LCS(原文, 抄袭版) / len(原文)

    语义是「原文中有多大比例的内容，在抄袭版里被原样、按序保留了下来」。

    Args:
        original: 已归一化的原文字符串。
        plagiarized: 已归一化的抄袭版字符串。

    Returns:
        取值 ``0.0`` ~ ``1.0`` 的浮点数。约定：

        * 原文为空 → ``0.0``
        * 抄袭版为空 → ``0.0``
        * 两者完全相同 → ``1.0``
        * 抄袭版完全包含原文 → ``1.0``
        * 抄袭版是原文的真子集 → ``len(抄袭版) / len(原文)``
    """
    if not original:
        return 0.0
    return lcs_length_dp(original, plagiarized) / len(original)
