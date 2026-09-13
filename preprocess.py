# -*- coding: utf-8 -*-
"""文本归一化模块。

查重前必须先把两份文本压成可比较的字符序列。本模块只保留汉字，
丢弃标点、空白、数字与字母。

为什么丢掉标点：标点几乎不承载语义，但在字符级噪声（随机增删几个字）
下会大量误判——把"逗号是否还对得上"也算进相似度，结果会失真。
"""

from __future__ import annotations

import re

#: 汉字区（基本区 + 扩展 A 区）。用单次 findall 而不是反复 replace，
#: 是因为前者只需扫一遍字符串，后者要扫描多遍——这是一个有意的性能选择。
_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def normalize(text: str) -> str:
    """把任意文本压成只含汉字的字符串。

    Args:
        text: 原始文本，可以是任意内容。

    Returns:
        仅由汉字组成的字符串；若原文没有任何汉字，返回空串。
    """
    return "".join(_CJK_PATTERN.findall(text))
