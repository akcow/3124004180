"""相似度计算模块的单元测试。

用例编号（test_case01 ~ test_case18）与开发计划 §五 的用例表一一对应，
其余是补充的分支覆盖用例。

注意契约：``plagiarism_rate`` 要求输入**已归一化**，归一化由
``preprocess.normalize`` 负责、由调用方先做。因此下面凡是用原始文本的
用例都先过一遍 :func:`rate`。
"""

import random

import pytest

import similarity
from helpers import SAMPLE_COPY, SAMPLE_ORIGINAL, brute_force_lcs, random_chinese
from preprocess import normalize
from similarity import (
    METRIC_MAX_BASE,
    METRIC_ORIG_BASE,
    chunked_common_length,
    is_exact_feasible,
    lcs_length,
    lcs_length_dp,
    plagiarism_rate,
    similarity_report,
)


def rate(first: str, second: str, metric: str = METRIC_ORIG_BASE) -> float:
    """归一化后再算重复率，模拟真实调用链（main → normalize → similarity）。"""
    return plagiarism_rate(normalize(first), normalize(second), metric)


# ---------------------------------------------------------------- 18 个主用例


def test_case01_identical_text_scores_one():
    """用例 1：两文相同 → 1.00。"""
    text = "春江潮水连海平，海上明月共潮生。"
    assert rate(text, text) == pytest.approx(1.0)


def test_case02_unrelated_text_scores_zero():
    """用例 2：两段完全无关的中文 → 0.00。"""
    assert rate("春江潮水连海平", "甲乙丙丁戊己庚辛") == pytest.approx(0.0)


def test_case03_empty_original_scores_zero():
    """用例 3：原文为空 → 0.00。"""
    assert rate("", "任何内容") == pytest.approx(0.0)


def test_case04_empty_copy_scores_zero():
    """用例 4：抄袭版为空 → 0.00。"""
    assert rate("任何内容", "") == pytest.approx(0.0)


def test_case05_both_empty_scores_zero():
    """用例 5：两文都空 → 0.00。"""
    assert rate("", "") == pytest.approx(0.0)


def test_case06_punctuation_only_scores_zero():
    """用例 6：纯标点空白，归一化后为空 → 0.00。"""
    assert rate("，。！？ \t\n", "，。！？") == pytest.approx(0.0)


def test_case07_assignment_sample():
    """用例 7：题目自带样例 → 14/19（写文件时四舍五入为 0.74）。"""
    assert rate(SAMPLE_ORIGINAL, SAMPLE_COPY) == pytest.approx(14 / 19)


def test_case08_copy_contains_original_scores_one():
    """用例 8：抄袭版在原文基础上新增内容，原文被 100% 抄走 → 1.00。"""
    original = "甲" * 100
    assert rate(original, original + "乙" * 25) == pytest.approx(1.0)


def test_case09_copy_is_half_of_original():
    """用例 9：抄袭版是原文的前一半 → 0.50。"""
    original = random_chinese(seed=7, length=2000)
    assert rate(original, original[:1000]) == pytest.approx(0.5)


def test_case10_single_character_difference():
    """用例 10：只改一个字 → (n-1)/n。"""
    original = random_chinese(seed=11, length=500)
    replacement = "甲" if original[0] != "甲" else "乙"
    assert rate(original, replacement + original[1:]) == pytest.approx(499 / 500)


def test_case11_scrambled_blocks_stay_between_zero_and_one():
    """用例 11：把原文分块打乱 → 重复率严格落在 0 与 1 之间。"""
    original = random_chinese(seed=13, length=600)
    blocks = [original[i:i + 30] for i in range(0, len(original), 30)]
    random.Random(99).shuffle(blocks)
    assert 0.0 < rate(original, "".join(blocks)) < 1.0


def test_case12_matches_brute_force_reference():
    """用例 12：与独立的暴力 DP 对拍，验证 LCS 结果一致。"""
    rng = random.Random(2026)
    for _ in range(20):
        first = "".join(rng.choice("甲乙丙丁戊") for _ in range(rng.randint(1, 60)))
        second = "".join(rng.choice("甲乙丙丁戊") for _ in range(rng.randint(1, 60)))
        expected = brute_force_lcs(first, second)
        assert lcs_length_dp(first, second) == expected
        assert lcs_length(first, second) == expected


def test_case18_large_input_uses_chunked_estimation(monkeypatch):
    """用例 18：超出单元格预算时改走分块估计，结果仍落在合理区间。

    为了不拖慢测试，这里把预算调小以触发该分支；真实的 10 万字基准
    由 tools/bench.py 负责。
    """
    monkeypatch.setattr(similarity, "MAX_EXACT_CELLS", 1_000_000)
    original = random_chinese(seed=31, length=8_000)
    report = similarity_report(original, original[:7_200])          # 删掉 10%
    assert report.estimated is True
    assert 0.85 < report.rate <= 1.0


# ------------------------------------------------------------ 补充的分支用例


def test_normalization_is_the_callers_job():
    """契约用例：直接传未归一化的原文，标点会被算进相似度。

    这是有意的分工——归一化属于 preprocess.normalize 的职责，由 main 先做。
    两条路径结果不同，正是这条契约存在的意义。
    """
    assert plagiarism_rate(SAMPLE_ORIGINAL, SAMPLE_COPY) != pytest.approx(14 / 19)
    assert rate(SAMPLE_ORIGINAL, SAMPLE_COPY) == pytest.approx(14 / 19)


def test_report_fields_are_populated():
    """报告对象的每个字段都要被正确填充。"""
    report = similarity_report("甲" * 10, "甲" * 10)
    assert report.rate == pytest.approx(1.0)
    assert report.common_length == 10
    assert report.base_length == 10
    assert report.metric == METRIC_ORIG_BASE
    assert report.original_length == 10
    assert report.plagiarized_length == 10
    assert report.estimated is False


@pytest.mark.parametrize(
    ("metric", "expected"),
    [(METRIC_ORIG_BASE, 1.0), (METRIC_MAX_BASE, 0.8)],
)
def test_metric_switch(metric, expected):
    """两种口径给出不同结果：原文被 100% 抄走 vs 占较长文本的八成。"""
    original = "甲" * 100
    assert rate(original, original + "乙" * 25, metric) == pytest.approx(expected)


def test_unknown_metric_raises():
    """非法口径必须报 ValueError，而不是悄悄按默认口径算。"""
    with pytest.raises(ValueError, match="未知的重复率口径"):
        plagiarism_rate("甲", "甲", metric="bogus")


def test_is_exact_feasible_boundary(monkeypatch):
    """预算边界：刚好等于预算算可行，超过则不可行。"""
    assert is_exact_feasible("甲" * 10, "甲" * 10) is True
    monkeypatch.setattr(similarity, "MAX_EXACT_CELLS", 100)
    assert is_exact_feasible("甲" * 10, "甲" * 10) is True
    assert is_exact_feasible("甲" * 11, "甲" * 10) is False


def test_chunked_common_length_edges():
    """分块估计的边界：任一方为空得 0；完全相同得满分且不越界。"""
    assert chunked_common_length("", "甲") == 0
    assert chunked_common_length("甲", "") == 0
    text = random_chinese(seed=41, length=3_000)
    assert chunked_common_length(text, text) == len(text)


def test_chunked_common_length_never_exceeds_original():
    """分块估计值天然不超过原文长度（各块互不重叠）。"""
    original = random_chinese(seed=43, length=3_000)
    copy = random_chinese(seed=44, length=2_000)
    assert 0 <= chunked_common_length(original, copy) <= len(original)
