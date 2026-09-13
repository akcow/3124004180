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

#: 汉字 + 拉丁字母。用于需要支持英文论文的场景（``--keep-latin``）。
_CJK_LATIN_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbfA-Za-z]")


def normalize(text: str, keep_latin: bool = False) -> str:
    """把任意文本压成可比较的字符序列。

    Args:
        text: 原始文本，可以是任意内容。
        keep_latin: 为 ``True`` 时同时保留拉丁字母（用于英文论文）；
            默认为 ``False``，只保留汉字。

    Returns:
        归一化后的字符串；若原文没有任何有效字符，返回空串。
    """
    pattern = _CJK_LATIN_PATTERN if keep_latin else _CJK_PATTERN
    return "".join(pattern.findall(text))
