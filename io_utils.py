# -*- coding: utf-8 -*-
"""文件读写模块。

本模块负责两件事：把文本文件读成字符串、把重复率写成答案文件。
读写范围**严格限定在命令行传入的路径**上——程序不访问任何其他文件，
也不访问网络。
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass
from pathlib import Path

#: 答案文件的小数位数。题目要求精确到小数点后两位。
RATE_DECIMALS = 2

#: 带 BOM 的编码，按 BOM 前缀判定。
#: 注意 UTF-32 的 BOM 以 UTF-16 的 BOM 为前缀，所以必须先长后短。
_BOM_ENCODINGS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)

#: 没有 BOM 时依次尝试的编码。
#: utf-8-sig 放在最前：它能同时正确处理「纯 UTF-8」与「带 BOM 的 UTF-8」。
#: gb18030 是 gbk 的超集，用来兜住 Windows 上常见的老式中文文件。
_FALLBACK_ENCODINGS = ("utf-8-sig", "gb18030")


@dataclass(frozen=True)
class DecodedText:
    """一个文本文件的解码结果。

    Attributes:
        text: 解码后的文本内容。
        encoding: 实际生效的编码名。
        size: 文件字节数。
    """

    text: str
    encoding: str
    size: int


def decode_bytes(raw: bytes) -> tuple[str, str]:
    """把字节串解码成文本，自动识别常见编码。

    策略：先按 BOM 判定，再依次尝试 UTF-8 与 GB18030，全都不行时用
    ``errors="replace"`` 兜底——**绝不因为编码问题抛异常**，因为这会让
    程序异常退出、直接丢掉测试点。

    Args:
        raw: 文件原始字节。

    Returns:
        ``(文本, 实际使用的编码名)``。
    """
    for bom, encoding in _BOM_ENCODINGS:
        if raw.startswith(bom):
            return raw.decode(encoding), encoding

    for encoding in _FALLBACK_ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace"), "utf-8(replace)"


def read_text_file(path: str | Path) -> DecodedText:
    """读取文本文件，返回解码结果与元信息。

    Args:
        path: 文件路径（由命令行参数给出）。

    Returns:
        :class:`DecodedText`。

    Raises:
        OSError: 文件不存在、是目录或没有读取权限。
    """
    target = Path(path)
    if target.is_dir():
        # Windows 上对目录调用 read_bytes 抛的是 PermissionError，
        # 错误信息会误导人，所以这里显式转成"是目录"。
        raise IsADirectoryError(f"路径是目录，不是文件：{target}")
    raw = target.read_bytes()
    text, encoding = decode_bytes(raw)
    return DecodedText(text=text, encoding=encoding, size=len(raw))


def read_text(path: str | Path) -> str:
    """读取文本文件内容（:func:`read_text_file` 的便捷封装）。

    Args:
        path: 文件路径。

    Returns:
        文件内容字符串。

    Raises:
        OSError: 文件不存在、是目录或没有读取权限。
    """
    return read_text_file(path).text


def write_answer(path: str | Path, rate: float) -> None:
    """把重复率写入答案文件。

    文件内容只有数字本身（形如 ``0.80``），不含任何说明文字。

    Args:
        path: 答案文件路径（由命令行参数给出）。
        rate: 重复率，取值 0.0 ~ 1.0。

    Raises:
        OSError: 目标目录不存在或没有写入权限。
    """
    target = Path(path)
    if target.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件：{target}")
    target.write_text(f"{rate:.{RATE_DECIMALS}f}\n", encoding="utf-8")
