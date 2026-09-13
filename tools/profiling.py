#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""性能剖析与性能分析图生成工具。

用法::

    python tools/profiling.py --tag before --out docs/perf/profile_before.png \\
        -- python main.py text_files/orig.txt text_files/orig_0.8_del.txt out.txt

流程：cProfile 采集 → pstats 解析出 Top-N 热点 → matplotlib 出 PNG；
本机若装了 Graphviz，再调用 gprof2dot 额外生成一张调用关系图。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_PY_EXE_NAMES = {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"}

#: 剖析器自身的包装帧，不是被测代码的热点，默认剔除
_HARNESS_FUNCS = {
    "<module>",
    "<built-in method builtins.exec>",
    "<built-in method builtins.compile>",
    "compile",
    "_compile",
    "run_path",
    "run_module",
    "_run_module_as_main",
    "_run_code",
    "runctx",
}


def normalize_target(target: list[str]) -> list[str]:
    """把 ``['python', 'main.py', ...]`` 压成 ``['main.py', ...]``。

    cProfile 只接收脚本文件或 ``-m`` 模块，不能直接跑任意可执行命令。
    """
    if target and os.path.basename(target[0]).lower() in _PY_EXE_NAMES:
        return target[1:]
    return target


def run_profile(target: list[str], prof_path: Path) -> None:
    """用 cProfile 运行目标，把统计数据写入 prof_path。目标非零退出也不中断。"""
    prof_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] 采集: {' '.join(target)}")
    cmd = [sys.executable, "-m", "cProfile", "-o", str(prof_path), *target]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[1/4] 注意: 目标以退出码 {result.returncode} 结束，仍继续解析已采集的数据")


def _merge_stats(stats, keep_harness: bool) -> list[dict]:
    """把 pstats 的原始统计按函数名合并成一行一条记录。"""
    merged: dict[str, dict] = {}
    for (fname, _lineno, func), (_cc, nc, tt, ct, _callers) in stats.stats.items():
        if not keep_harness and func in _HARNESS_FUNCS:
            continue
        rec = merged.setdefault(
            func, {"name": func, "ncalls": 0, "tottime": 0.0, "cumtime": 0.0, "files": set()}
        )
        rec["ncalls"] += nc
        rec["tottime"] += tt
        rec["cumtime"] += ct
        rec["files"].add(os.path.basename(fname))

    rows = []
    for rec in merged.values():
        names = sorted(rec["files"])
        rec["file"] = names[0] if len(names) == 1 else ", ".join(names)
        rows.append(rec)
    return rows


def load_hotspots(prof_path: Path, top_n: int = 15,
                  keep_harness: bool = False) -> tuple[dict[str, list[dict]], float]:
    """解析 prof 文件，返回 ``(按 tottime/cumtime 排序的 Top-N, 程序总耗时)``。

    同名函数跨模块合并，避免同一函数因来源文件不同而在表里重复出现。
    """
    import pstats

    stats = pstats.Stats(str(prof_path))
    stats.strip_dirs()
    rows = _merge_stats(stats, keep_harness)
    return {
        "tottime": sorted(rows, key=lambda r: r["tottime"], reverse=True)[:top_n],
        "cumtime": sorted(rows, key=lambda r: r["cumtime"], reverse=True)[:top_n],
    }, stats.total_tt or 1.0


def write_hotspots_md(hotspots: dict[str, list[dict]], total: float,
                      out_path: Path, tag: str) -> None:
    """把「消耗最大的函数」Top-N 写成 Markdown。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 消耗最大的函数 Top-N（{tag}）",
        "",
        f"程序总耗时（cProfile 计时）：**{total:.4f} 秒**。占比 = 该函数耗时 ÷ 程序总耗时。",
        "",
    ]
    for key, title in (
        ("tottime", "按自身耗时排序（tottime，不含子函数调用）"),
        ("cumtime", "按累计耗时排序（cumtime，含子函数调用）"),
    ):
        lines += [f"## {title}", "",
                  "| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |",
                  "|---|---|---|---|---|---|---|"]
        for i, row in enumerate(hotspots[key], 1):
            lines.append(
                f"| {i} | `{row['name']}` | {row['file']} | {row['ncalls']} | "
                f"{row['tottime']:.4f} | {row['cumtime']:.4f} | {row['cumtime'] / total:.1%} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[2/4] 热点表: {out_path}")


def _pick_cjk_font() -> str | None:
    """找一个本机可用的中文字体；找不到返回 None，此时改用英文标签。"""
    try:
        from matplotlib import font_manager
    except ImportError:
        return None
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                 "Source Han Sans SC", "PingFang SC", "WenQuanYi Micro Hei"):
        if name in available:
            return name
    return None


#: 两栏的标题文案，中文 / 英文各一份
_PANEL_TITLES = {
    "tottime": ("自身耗时 tottime（不含子函数）", "Self time (tottime)"),
    "cumtime": ("累计耗时 cumtime（含子函数）", "Cumulative time (cumtime)"),
}


def _draw_panel(axis, rows: list[dict], key: str, color: str, chinese: bool) -> None:
    """在给定坐标轴上画一栏横向条形图。"""
    values = [row[key] for row in rows]
    positions = list(range(len(rows)))

    axis.barh(positions, values, height=0.68, color=color, alpha=0.9)
    axis.set_yticks(positions)
    axis.set_yticklabels([row["name"] for row in rows], fontsize=9)
    axis.set_xlabel("耗时（秒）" if chinese else "seconds", fontsize=10)
    axis.set_title(_PANEL_TITLES[key][0 if chinese else 1], fontsize=11)
    axis.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.5)
    axis.set_axisbelow(True)
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)

    span = max(values) if values else 1.0
    for position, value in zip(positions, values):
        axis.text(value + span * 0.015, position, f"{value:.3f}", va="center",
                  fontsize=8.5, color="#333333")
    axis.set_xlim(0, span * 1.20)


def plot_performance(hotspots: dict[str, list[dict]], total: float,
                     out_path: Path, tag: str) -> bool:
    """画性能分析图：左右两栏，分别是 tottime 与 cumtime 的横向条形图。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[3/4] 跳过绘图: 未安装 matplotlib（pip install matplotlib 后重跑）")
        return False

    cjk = _pick_cjk_font()
    if cjk:
        plt.rcParams["font.sans-serif"] = [cjk, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    figure, axes = plt.subplots(1, 2, figsize=(15.5, 7.4), dpi=150)
    title_cn = f"性能分析图 · {tag}（cProfile 采集，程序总耗时 {total:.3f}s）"
    title_en = f"Performance profile - {tag} (total {total:.3f}s)"
    figure.suptitle(title_cn if cjk else title_en, fontsize=15, y=0.985)

    for axis, key, color in ((axes[0], "tottime", "#185FA5"), (axes[1], "cumtime", "#0F6E56")):
        _draw_panel(axis, list(reversed(hotspots[key])), key, color, bool(cjk))

    figure.tight_layout(rect=(0, 0, 1, 0.962))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, facecolor="white")
    plt.close(figure)
    print(f"[3/4] 性能分析图: {out_path}")
    return True


def try_gprof2dot(prof_path: Path, out_dir: Path, tag: str) -> None:
    """本机同时具备 gprof2dot 与 Graphviz 时，额外生成一张调用关系图。"""
    missing = [name for name in ("gprof2dot", "dot") if shutil.which(name) is None]
    if missing:
        print(f"[4/4] 跳过调用关系图: 缺少 {', '.join(missing)}（装 Graphviz 后重跑即可自动补上）")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    dot_file = out_dir / f"callgraph_{tag}.dot"
    png_file = out_dir / f"callgraph_{tag}.png"
    try:
        with dot_file.open("w", encoding="utf-8") as handle:
            subprocess.run(["gprof2dot", "-f", "pstats", str(prof_path)],
                           check=True, stdout=handle)
        subprocess.run(["dot", "-Tpng", str(dot_file), "-o", str(png_file)], check=True)
        print(f"[4/4] 调用关系图: {png_file}")
    except subprocess.CalledProcessError as exc:
        print(f"[4/4] 调用关系图生成失败: {exc}")


def main(argv: list[str] | None = None) -> int:
    """命令行入口。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(description="性能剖析与性能分析图生成工具")
    parser.add_argument("--tag", default="run", help="本轮剖析的标签，用于命名产物")
    parser.add_argument("--out", required=True, help="性能分析图输出路径（.png）")
    parser.add_argument("--out-dir", default="docs/perf", help="其余产物的输出目录")
    parser.add_argument("--top", type=int, default=15, help="Top-N 函数个数")
    parser.add_argument("--keep-harness", action="store_true",
                        help="保留剖析器自身的包装帧（默认剔除）")
    parser.add_argument("target", nargs=argparse.REMAINDER,
                        help="被剖析的命令，写成: -- python main.py a.txt b.txt out.txt")
    args = parser.parse_args(argv)

    target = normalize_target([item for item in args.target if item != "--"])
    if not target:
        parser.error("缺少被剖析的目标命令，示例: -- python main.py a.txt b.txt out.txt")

    out_dir = Path(args.out_dir)
    prof_path = out_dir / f"{args.tag}.prof"
    run_profile(target, prof_path)

    hotspots, total = load_hotspots(prof_path, args.top, args.keep_harness)
    write_hotspots_md(hotspots, total, out_dir / f"hotspots_{args.tag}.md", args.tag)
    plot_performance(hotspots, total, Path(args.out), args.tag)
    try_gprof2dot(prof_path, out_dir, args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
