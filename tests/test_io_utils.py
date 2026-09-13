"""文件读写模块的单元测试。"""

import pytest

from io_utils import decode_bytes, read_text, read_text_file, write_answer
from preprocess import normalize


def test_case13_gbk_encoded_file(tmp_path):
    """用例 13：GBK 编码的中文文件能正确读出。"""
    path = tmp_path / "gbk.txt"
    path.write_bytes("今天是星期天。".encode("gb18030"))
    decoded = read_text_file(path)
    assert decoded.encoding == "gb18030"
    assert decoded.text == "今天是星期天。"


def test_case14_utf8_with_bom(tmp_path):
    """用例 14：带 BOM 的 UTF-8，读出来不残留 \\ufeff。"""
    path = tmp_path / "bom.txt"
    path.write_bytes(b"\xef\xbb\xbf" + "天气晴".encode("utf-8"))
    decoded = read_text_file(path)
    assert decoded.encoding == "utf-8-sig"
    assert decoded.text == "天气晴"
    assert "\ufeff" not in decoded.text


def test_utf16_bom_is_detected(tmp_path):
    """UTF-16 的 BOM 也要能识别。"""
    path = tmp_path / "utf16.txt"
    path.write_bytes("晚上去看电影".encode("utf-16"))
    assert read_text(path) == "晚上去看电影"


def test_case15_crlf_and_lf_are_equivalent(tmp_path):
    """用例 15：CRLF 与 LF 只是换行差异，归一化后完全一致。"""
    crlf = tmp_path / "crlf.txt"
    lf = tmp_path / "lf.txt"
    crlf.write_bytes("今天是星期天。\r\n天气晴。".encode("utf-8"))
    lf.write_bytes("今天是星期天。\n天气晴。".encode("utf-8"))
    assert normalize(read_text(crlf)) == normalize(read_text(lf))


def test_undecodable_bytes_fall_back_to_replace():
    """UTF-8 与 GB18030 都解不了时用 replace 兜底，而不是抛异常。"""
    text, encoding = decode_bytes(b"\xff\xff")
    assert encoding == "utf-8(replace)"
    assert isinstance(text, str)


def test_read_text_file_returns_size(tmp_path):
    """字节数是文件原始大小，不受编码影响。"""
    path = tmp_path / "size.txt"
    path.write_text("中文", encoding="utf-8")
    assert read_text_file(path).size == len("中文".encode("utf-8"))


def test_read_text_file_on_directory_raises(tmp_path):
    """目录路径必须报 IsADirectoryError（Windows 上原生报的是权限错误）。"""
    with pytest.raises(IsADirectoryError):
        read_text_file(tmp_path)


def test_write_answer_on_directory_raises(tmp_path):
    """答案路径是目录时也要报 IsADirectoryError。"""
    with pytest.raises(IsADirectoryError):
        write_answer(tmp_path, 0.5)


@pytest.mark.parametrize(("rate", "expected"), [(0.8048, "0.80"), (1.0, "1.00"), (0.0, "0.00")])
def test_write_answer_keeps_two_decimals(tmp_path, rate, expected):
    """答案文件只有两位小数的数字本身。"""
    path = tmp_path / "answer.txt"
    write_answer(path, rate)
    assert path.read_text(encoding="utf-8").strip() == expected
