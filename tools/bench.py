"""基准跑分工具：测量 ``lcs_length`` 在不同文本规模下的耗时。

用法::

    python tools/bench.py --sizes 1500,3000,6000,12000 --runs 3 --out docs/perf/baseline.csv

用固定种子生成「原文 + 随机删 10% 的抄袭版」文本对，每档跑 runs 次取中位数
（先跑一次热身不计入），结果写成 CSV：规模, 中位数秒。
"""

# 本脚本在 tools/ 下，需先把项目根目录加进 sys.path 才能 import similarity
# pylint: disable=wrong-import-position
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import csv
import random
import time

from similarity import lcs_length

_ALPHABET = "春江花月夜山水云天风霜雪雨梅兰竹菊"


def make_pair(length: int, seed: int) -> tuple[str, str]:
    """生成 ``(原文, 随机删掉 10% 的抄袭版)``，固定种子保证可复现。"""
    rng = random.Random(seed)
    text = "".join(rng.choice(_ALPHABET) for _ in range(length))
    mutated = "".join(char for char in text if rng.random() >= 0.10)
    return text, mutated


def measure(length: int, runs: int, seed: int) -> float:
    """跑 runs 次（另加一次热身），返回耗时中位数。"""
    original, copy = make_pair(length, seed)
    lcs_length(original, copy)      # 热身，避免首次调用的冷启动开销
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        lcs_length(original, copy)
        samples.append(time.perf_counter() - started)
    samples.sort()
    return samples[len(samples) // 2]


def main(argv: list[str] | None = None) -> int:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="LCS 计算耗时基准")
    parser.add_argument("--sizes", default="1500,3000,6000,12000",
                        help="逗号分隔的文本规模（字符数）")
    parser.add_argument("--runs", type=int, default=3, help="每档重复次数，取中位数")
    parser.add_argument("--out", default="docs/perf/bench.csv", help="输出 CSV 路径")
    parser.add_argument("--seed", type=int, default=20260913, help="随机种子")
    args = parser.parse_args(argv)

    sizes = [int(item) for item in args.sizes.split(",")]
    rows = [("size", "median_seconds")]
    for size in sizes:
        median = round(measure(size, args.runs, args.seed), 6)
        rows.append((size, median))
        print(f"{size:>8} 字 -> {median:.4f} 秒")

    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    print(f"结果已写入 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
