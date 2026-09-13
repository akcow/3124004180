"""性能回归测试（对应 Stage 5）。

改进前（朴素 DP）此用例会因超时失败；换成位并行实现后转绿——测试本身
就是性能改进最直接的证据。
"""

import time

from similarity import plagiarism_rate


def test_large_input_under_5_seconds():
    """10 万字的输入，整个查重流程必须在 5 秒内完成。"""
    original = "春江花月夜山水云天风霜雪雨" * 6250      # 16 × 6250 = 100000 字
    copy = original[:90_000]

    started = time.perf_counter()
    plagiarism_rate(original, copy)
    elapsed = time.perf_counter() - started

    assert elapsed < 5.0, f"10 万字耗时 {elapsed:.2f}s，超过 5 秒限制"
