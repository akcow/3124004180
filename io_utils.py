# -*- coding: utf-8 -*-
"""文件读写模块。

本模块负责两件事：把文本文件读成字符串、把重复率写成答案文件。
读写范围**严格限定在命令行传入的路径**上——程序不访问任何其他文件，
也不访问网络。
"""

from __future__ import annotations

from pathlib import Path

#: 答案文件的小数位数。题目要求精确到小数点后两位。
RATE_DECIMALS = 2


def read_text(path: str) -> str:
    """读取文本文件内容。

    Args:
        path: 文件路径（由命令行参数给出）。

    Returns:
        文件内容字符串。
    """
    return Path(path).read_text(encoding="utf-8")


def write_answer(path: str, rate: float) -> None:
    """把重复率写入答案文件。

    文件内容只有数字本身（形如 ``0.80``），不含任何说明文字。

    Args:
        path: 答案文件路径（由命令行参数给出）。
        rate: 重复率，取值 0.0 ~ 1.0。
    """
    Path(path).write_text(f"{rate:.{RATE_DECIMALS}f}\n", encoding="utf-8")
