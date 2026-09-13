"""测试用的常量与纯函数工具。"""

import random

#: 题目自带的样例
SAMPLE_ORIGINAL = "今天是星期天，天气晴，今天晚上我要去看电影。"
SAMPLE_COPY = "今天是周天，天气晴朗，我晚上要去看电影。"

#: 随机文本使用的字符表（16 个汉字，够分散）
_ALPHABET = "春江花月夜山水云天风霜雪雨"


def random_chinese(seed: int, length: int) -> str:
    """固定种子生成随机中文串，保证测试可复现。"""
    rng = random.Random(seed)
    return "".join(rng.choice(_ALPHABET) for _ in range(length))


def brute_force_lcs(first: str, second: str) -> int:
    """最朴素的二维 DP 求 LCS，与被测实现相互独立，用于对拍。"""
    table = [[0] * (len(second) + 1) for _ in range(len(first) + 1)]
    for i, char_a in enumerate(first, 1):
        for j, char_b in enumerate(second, 1):
            if char_a == char_b:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    return table[len(first)][len(second)]
