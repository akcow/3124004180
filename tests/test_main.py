"""命令行入口的单元测试：参数校验、退出码与端到端流程。"""

import sys

import pytest

import main as main_module
from main import _describe_os_error, main


def test_end_to_end_writes_rounded_answer(text_pair):
    """端到端：读两个文件、算出重复率、写出两位小数。"""
    original, copy, answer = text_pair
    assert main([str(original), str(copy), str(answer)]) == 0
    assert answer.read_text(encoding="utf-8").strip() == "0.74"


def test_success_produces_no_stdout(text_pair, capsys):
    """正常路径不向标准输出写任何内容。"""
    original, copy, answer = text_pair
    main([str(original), str(copy), str(answer)])
    assert capsys.readouterr().out == ""


def test_verbose_goes_to_stderr_only(text_pair, capsys):
    """--verbose 只写标准错误，答案文件不受影响。"""
    original, copy, answer = text_pair
    main([str(original), str(copy), str(answer), "--verbose"])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[verbose]" in captured.err
    assert answer.read_text(encoding="utf-8").strip() == "0.74"


def test_metric_max_base_changes_answer(tmp_path):
    """切换到 max_base 口径后答案不同：抄袭版更长时以它作分母。"""
    original = tmp_path / "orig.txt"
    copy = tmp_path / "copy.txt"
    answer = tmp_path / "answer.txt"
    original.write_text("甲" * 100, encoding="utf-8")
    copy.write_text("甲" * 100 + "乙" * 25, encoding="utf-8")

    assert main([str(original), str(copy), str(answer)]) == 0
    assert answer.read_text(encoding="utf-8").strip() == "1.00"

    assert main([str(original), str(copy), str(answer), "--metric", "max_base"]) == 0
    assert answer.read_text(encoding="utf-8").strip() == "0.80"


def test_keep_latin_flag(tmp_path):
    """--keep-latin 让英文文本也能算出重复率。"""
    original = tmp_path / "en_a.txt"
    copy = tmp_path / "en_b.txt"
    answer = tmp_path / "answer.txt"
    original.write_text("the quick brown fox jumps over the lazy dog", encoding="utf-8")
    copy.write_text("the quick brown fox leaps over a lazy dog", encoding="utf-8")

    assert main([str(original), str(copy), str(answer), "--keep-latin"]) == 0
    assert float(answer.read_text(encoding="utf-8")) > 0.5


def test_case16_wrong_argument_count_exits_with_2(text_pair):
    """用例 16：参数个数不对 → 退出码 2。"""
    original, copy, _ = text_pair
    with pytest.raises(SystemExit) as excinfo:
        main([str(original), str(copy)])
    assert excinfo.value.code == 2


def test_case17_missing_file_exits_with_2(tmp_path, capsys):
    """用例 17：输入文件不存在 → 友好提示 + 退出码 2，不打印 traceback。"""
    missing = tmp_path / "nope.txt"
    answer = tmp_path / "answer.txt"
    assert main([str(missing), str(missing), str(answer)]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_input_directory_exits_with_2(tmp_path):
    """输入路径是目录 → 退出码 2。"""
    copy = tmp_path / "copy.txt"
    copy.write_text("天气晴", encoding="utf-8")
    assert main([str(tmp_path), str(copy), str(tmp_path / "a.txt")]) == 2


def test_unwritable_answer_exits_with_2(text_pair):
    """答案路径不可写（指向目录）→ 退出码 2。"""
    original, copy, _ = text_pair
    assert main([str(original), str(copy), str(original.parent)]) == 2


def test_invalid_metric_exits_with_2(text_pair):
    """非法口径取值由 argparse 拦下，退出码 2。"""
    original, copy, answer = text_pair
    with pytest.raises(SystemExit) as excinfo:
        main([str(original), str(copy), str(answer), "--metric", "bogus"])
    assert excinfo.value.code == 2


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (FileNotFoundError(), "文件不存在"),
        (IsADirectoryError(), "该路径是目录，不是文件"),
        (PermissionError(), "没有访问权限"),
        # 注意不能用 OSError(1, ...)：errno 1 会被 Python 自动映射成 PermissionError
        (OSError(9999, "自定义错误"), "自定义错误"),
    ],
)
def test_describe_os_error_branches(exc, expected):
    """四种 OSError 都要翻译成人话。"""
    assert _describe_os_error(exc) == expected


def test_unexpected_exception_is_caught(monkeypatch, capsys):
    """兜底分支：未预期异常也只给一句人话 + 退出码 2，不抛 traceback。"""

    def boom(_args):
        raise RuntimeError("boom")

    monkeypatch.setattr(main_module, "_run", boom)
    assert main(["a", "b", "c"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_stderr_reconfigure_failure_is_tolerated(monkeypatch):
    """stderr 没有 reconfigure 方法时也不应报错。"""
    monkeypatch.setattr(sys, "stderr", object())
    main_module._configure_stderr()
