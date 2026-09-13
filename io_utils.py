"""文件读写：编码自适应的文本读取与答案写出。

读写范围严格限定在命令行传入的路径上，不访问其他文件。
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass
from pathlib import Path

#: 答案文件的小数位数，题目要求两位
RATE_DECIMALS = 2

#: 带 BOM 的编码。UTF-32 的 BOM 以 UTF-16 的 BOM 为前缀，故必须先长后短。
_BOM_ENCODINGS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)

#: 无 BOM 时依次尝试。utf-8-sig 兼顾纯 UTF-8 与带 BOM 的 UTF-8；
#: gb18030 是 gbk 的超集，用来兜住 Windows 上常见的老式中文文件。
_FALLBACK_ENCODINGS = ("utf-8-sig", "gb18030")


@dataclass(frozen=True)
class DecodedText:
    """一个文本文件的解码结果：正文、实际编码名、字节数。"""

    text: str
    encoding: str
    size: int


def decode_bytes(raw: bytes) -> tuple[str, str]:
    """解码字节串，返回 ``(文本, 实际使用的编码名)``。

    先按 BOM 判定，再依次试 UTF-8 与 GB18030，全失败时用 replace 兜底
    ——绝不因为编码问题抛异常，那会导致程序异常退出。
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
    """读取文本文件并解码。

    目录路径显式转成 IsADirectoryError——Windows 上对目录读字节抛的是
    PermissionError，报错信息会误导人。
    """
    target = Path(path)
    if target.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件：{target}")
    raw = target.read_bytes()
    text, encoding = decode_bytes(raw)
    return DecodedText(text=text, encoding=encoding, size=len(raw))


def read_text(path: str | Path) -> str:
    """读取文本文件内容。"""
    return read_text_file(path).text


def write_answer(path: str | Path, rate: float) -> None:
    """把重复率写入答案文件，内容只有数字本身（形如 ``0.80``）。"""
    target = Path(path)
    if target.is_dir():
        raise IsADirectoryError(f"路径是目录，不是文件：{target}")
    target.write_text(f"{rate:.{RATE_DECIMALS}f}\n", encoding="utf-8")
