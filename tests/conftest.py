"""测试共用夹具。"""

import pytest

from helpers import SAMPLE_COPY, SAMPLE_ORIGINAL


@pytest.fixture
def text_pair(tmp_path):
    """一对输入文件与答案文件的路径，用于端到端测试。"""
    original = tmp_path / "orig.txt"
    copy = tmp_path / "copy.txt"
    answer = tmp_path / "answer.txt"
    original.write_text(SAMPLE_ORIGINAL, encoding="utf-8")
    copy.write_text(SAMPLE_COPY, encoding="utf-8")
    return original, copy, answer
