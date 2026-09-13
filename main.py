#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文查重程序 · 命令行入口。

用法::

    python main.py <原文文件绝对路径> <抄袭版论文文件绝对路径> <答案文件绝对路径>

程序从命令行给出的两个路径读取文本，计算抄袭版相对原文的重复率，
并把结果写入第三个路径指定的答案文件。

本模块只做流程编排，不包含任何算法实现。
"""

from __future__ import annotations

import sys

from io_utils import read_text, write_answer
from preprocess import normalize
from similarity import plagiarism_rate

#: 除程序名外，命令行参数的个数
REQUIRED_ARGS = 3


def main(argv: list[str]) -> int:
    """程序主流程。

    Args:
        argv: 完整的命令行参数列表（含程序名）。

    Returns:
        进程退出码，0 表示成功。
    """
    original_path, plagiarized_path, answer_path = (
        argv[1],
        argv[2],
        argv[3],
    )

    original = normalize(read_text(original_path))
    plagiarized = normalize(read_text(plagiarized_path))

    write_answer(answer_path, plagiarism_rate(original, plagiarized))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
