"""论文查重程序 · 命令行入口。

用法::

    python main.py <原文文件> <抄袭版文件> <答案文件> [--metric ...] [--keep-latin] [--verbose]

成功时不产生任何标准输出；--verbose 的信息走标准错误，答案只写入文件。
本模块只做参数解析与流程编排，不含算法。
"""

from __future__ import annotations

import argparse
import sys
import time

from io_utils import DecodedText, read_text_file, write_answer
from preprocess import normalize
from similarity import METRIC_ORIG_BASE, METRICS, SimilarityReport, similarity_report

#: 参数错误或文件不可用时的退出码
EXIT_USAGE_ERROR = 2


class InputError(Exception):
    """输入文件不可用（不存在、是目录、无权限等）。"""


def build_parser() -> argparse.ArgumentParser:
    """构造参数解析器。前三个位置参数是题目规定的调用契约。"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="计算抄袭版论文相对原文的重复率。",
    )
    parser.add_argument("original", metavar="原文文件", help="论文原文的绝对路径")
    parser.add_argument("plagiarized", metavar="抄袭版文件", help="抄袭版论文的绝对路径")
    parser.add_argument("answer", metavar="答案文件", help="输出重复率的答案文件路径")
    parser.add_argument("--metric", choices=METRICS, default=METRIC_ORIG_BASE,
                        help=f"重复率口径（默认 {METRIC_ORIG_BASE}）")
    parser.add_argument("--keep-latin", action="store_true",
                        help="归一化时一并保留拉丁字母，用于英文论文")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="把中间信息打印到标准错误；答案文件不受影响")
    return parser


def _describe_os_error(exc: OSError) -> str:
    """把 OSError 翻译成一句人话。"""
    if isinstance(exc, FileNotFoundError):
        return "文件不存在"
    if isinstance(exc, IsADirectoryError):
        return "该路径是目录，不是文件"
    if isinstance(exc, PermissionError):
        return "没有访问权限"
    return exc.strerror or str(exc)


def _fail(message: str) -> int:
    """打印一条友好错误信息并返回失败退出码，不抛异常。"""
    print(f"错误：{message}", file=sys.stderr)
    return EXIT_USAGE_ERROR


def _configure_stderr() -> None:
    """让标准错误在 GBK 控制台下也不会因编码问题抛异常。"""
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _load_text(path: str, label: str, keep_latin: bool) -> tuple[str, DecodedText]:
    """读取并归一化一个输入文件。

    Raises:
        InputError: 文件不可读。
    """
    try:
        decoded = read_text_file(path)
    except OSError as exc:
        raise InputError(f"无法读取{label}文件：{path}（{_describe_os_error(exc)}）") from exc
    return normalize(decoded.text, keep_latin=keep_latin), decoded


def _print_verbose(original_file: DecodedText, plagiarized_file: DecodedText,
                   report: SimilarityReport, elapsed: float) -> None:
    """把中间信息打印到标准错误，便于排查问题。"""
    lines = [
        f"原文    {original_file.size} 字节  编码 {original_file.encoding}"
        f"  归一化后 {report.original_length} 字",
        f"抄袭版  {plagiarized_file.size} 字节  编码 {plagiarized_file.encoding}"
        f"  归一化后 {report.plagiarized_length} 字",
        f"口径    {report.metric}",
        f"分块估计 {'是' if report.estimated else '否'}",
        f"LCS     {report.common_length}  /  分母 {report.base_length}",
        f"重复率  {report.rate:.6f}  ->  写入 {report.rate:.2f}",
        f"耗时    {elapsed:.3f} 秒",
    ]
    for line in lines:
        print(f"[verbose] {line}", file=sys.stderr)


def _run(args: argparse.Namespace) -> int:
    """执行一次完整的查重流程。"""
    original, original_file = _load_text(args.original, "原文", args.keep_latin)
    plagiarized, plagiarized_file = _load_text(args.plagiarized, "抄袭版", args.keep_latin)

    started = time.perf_counter()
    report = similarity_report(original, plagiarized, args.metric)
    elapsed = time.perf_counter() - started

    try:
        write_answer(args.answer, report.rate)
    except OSError as exc:
        return _fail(f"无法写入答案文件：{args.answer}（{_describe_os_error(exc)}）")

    if args.verbose:
        _print_verbose(original_file, plagiarized_file, report, elapsed)
    return 0


def main(argv: list[str] | None = None) -> int:
    """程序入口。返回退出码：0 成功，2 参数或文件错误。"""
    _configure_stderr()
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except InputError as exc:
        return _fail(str(exc))
    except Exception as exc:  # pylint: disable=broad-except
        # 兜底：宁可给一句人话，也不要让评测看到 traceback 和异常退出
        return _fail(f"未预期的错误：{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
