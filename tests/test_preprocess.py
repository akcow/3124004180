"""文本归一化模块的单元测试。"""

from preprocess import normalize


def test_drops_punctuation_and_whitespace():
    """标点、空白、数字、字母一律丢弃。"""
    assert normalize("今天是星期天，天气 晴！\n2026年 abc") == "今天是星期天天气晴年"


def test_keeps_cjk_extension_area():
    """扩展 A 区的汉字也要保留。"""
    assert normalize("㐀㐁测试") == "㐀㐁测试"


def test_keep_latin_flag():
    """打开 keep_latin 后拉丁字母保留，汉字仍然保留，标点仍丢弃。"""
    assert normalize("Hello, 世界!", keep_latin=True) == "Hello世界"
    assert normalize("Hello, 世界!", keep_latin=False) == "世界"


def test_empty_input():
    """没有任何有效字符时返回空串。"""
    assert normalize("") == ""
    assert normalize("，。！？ \t\n") == ""
