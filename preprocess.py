# -*- coding: utf-8 -*-
"""文本归一化：把原始文本压成可比较的字符序列。"""

from __future__ import annotations

import re

#: 汉字区（基本区 + 扩展 A 区）
_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

#: 汉字 + 拉丁字母，用于英文论文（--keep-latin）
_CJK_LATIN_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbfA-Za-z]")


def normalize(text: str, keep_latin: bool = False) -> str:
    """只保留汉字（可选一并保留拉丁字母），丢弃标点、空白、数字。

    丢标点是因为它几乎不承载语义，却会在字符级噪声下造成大量误判。
    """
    pattern = _CJK_LATIN_PATTERN if keep_latin else _CJK_PATTERN
    return "".join(pattern.findall(text))
