#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计算模块性能剖析与性能分析图生成工具（开发期工具，不参与运行期依赖）。

用法::

    python tools/profiling.py --tag before --out docs/perf/profile_before.png \\
        -- python main.py text_files/orig.txt text_files/orig_0.8_del.txt out.txt

做四件事：

1. 用 ``cProfile`` 采集目标命令的执行数据，落盘为 ``.prof``；
2. 用 ``pstats`` 导出「消耗最大的函数」Top-N，写成 Markdown；
3. 生成性能分析图（自包含，**不依赖 Graphviz**）；
4. 若本机存在 Graphviz 的 ``dot`` 命令，额外调用 ``gprof2dot`` 出经典调用关系图。

只有第 3 步需要 matplotlib；缺失时会跳过并给出提示，不影响其余步骤。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------ cProfile 采集

_PY_EXE_NAMES = {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"}


def normalize_target(target: list[str]) -> list[str]:
    """规范化目标命令。

    ``cProfile`` 只能接收「脚本文件」或「``-m`` 模块」，不能接收任意可执行命令。
    因此把 ``['python', 'main.py', 'a', 'b', 'c']`` 压成 ``['main.py', 'a', 'b', 'c']``，
    统一交给当前解释器执行。
    """
    if target and os.path.basename(target[0]).lower() in _PY_EXE_NAMES:
        return target[1:]
    return target


def run_profile(target: list[str], prof_path: Path) -> None:
    """以 cProfile 运行目标，把统计数据写入 prof_path。目标非零退出时不中断。"""
    prof_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "cProfile", "-o", str(prof_path), *target]
    print(f"[1/4] 采集: {' '.join(target)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[1/4] 注意: 目标以退出码 {result.returncode} 结束，仍继续解析已采集的数据")


# ------------------------------------------------------- pstats 解析与热点导出

#: 剖析器自身的包装帧，不是被测代码的真实热点，默认剔除。
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

#: 调用次数少于该值的内置函数视为噪声，不参与排名。
_NOISE_CALL_FLOOR = 0


def load_hotspots(prof_path: Path, top_n: int = 15,
                  keep_harness: bool = False) -> tuple[dict[str, list[dict]], float]:
    """解析 prof 文件，返回 (Top-N 分组, 程序总耗时)。

    同名函数跨模块合并，避免同一函数因来源文件不同而在表里重复出现。
    """
    import pstats

    stats = pstats.Stats(str(prof_path))
    stats.strip_dirs()

    merged: dict[str, dict] = {}
    for (fname, _lineno, func), (cc, nc, tt, ct, _callers) in stats.stats.items():
        if not keep_harness and func in _HARNESS_FUNCS:
            continue
        if nc <= _NOISE_CALL_FLOOR:
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
        rec["files"] = sorted(rec["files"])
        rec["file"] = rec["files"][0] if len(rec["files"]) == 1 else ", ".join(rec["files"])
        rows.append(rec)

    total = stats.total_tt or 1.0
    return {
        "tottime": sorted(rows, key=lambda r: r["tottime"], reverse=True)[:top_n],
        "cumtime": sorted(rows, key=lambda r: r["cumtime"], reverse=True)[:top_n],
    }, total


def write_hotspots_md(hotspots: dict[str, list[dict]], total: float,
                      out_path: Path, tag: str) -> None:
    """把 Top-N 函数表写成 Markdown（对应题目「展示你程序中消耗最大的函数」）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 消耗最大的函数 Top-N（{tag}）",
        "",
        f"程序总耗时（cProfile 计时）：**{total:.4f} 秒**。",
        "占比 = 该函数耗时 ÷ 程序总耗时。",
        "",
    ]
    for key, title in (
        ("tottime", "按自身耗时排序（tottime，不含子函数调用）"),
        ("cumtime", "按累计耗时排序（cumtime，含子函数调用）"),
    ):
        lines += [
            f"## {title}",
            "",
            "| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |",
            "|---|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(hotspots[key], 1):
            lines.append(
                f"| {i} | `{r['name']}` | {r['file']} | {r['ncalls']} | "
                f"{r['tottime']:.4f} | {r['cumtime']:.4f} | {r['cumtime'] / total:.1%} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[2/4] 热点表: {out_path}")


# ------------------------------------------------------------ 性能分析图绘制

def _pick_cjk_font() -> str | None:
    """返回本机可用的中文字体名，找不到则返回 None（此时改用英文标签）。"""
    try:
        from matplotlib import font_manager
    except ImportError:
        return None
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC",
                 "PingFang SC", "WenQuanYi Micro Hei"):
        if name in available:
            return name
    return None


def plot_performance(hotspots: dict[str, list[dict]], total: float,
                     out_path: Path, tag: str) -> bool:
    """绘制性能分析图。返回是否绘制成功（matplotlib 缺失时返回 False）。"""
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
    t = (lambda cn, en: cn) if cjk else (lambda cn, en: en)

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.4), dpi=150)
    fig.suptitle(t(f"性能分析图 · {tag}（cProfile 采集，程序总耗时 {total:.3f}s）",
                   f"Performance profile - {tag} (total {total:.3f}s)"),
                 fontsize=15, y=0.985)

    for ax, key, subtitle, color in (
        (axes[0], "tottime",
         t("自身耗时 tottime（不含子函数）", "Self time (tottime)"), "#185FA5"),
        (axes[1], "cumtime",
         t("累计耗时 cumtime（含子函数）", "Cumulative time (cumtime)"), "#0F6E56"),
    ):
        rows = list(reversed(hotspots[key]))
        labels = [r["name"] for r in rows]
        values = [r[key] for r in rows]

        ypos = list(range(len(rows)))
        ax.barh(ypos, values, height=0.68, color=color, alpha=0.9)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(t("耗时（秒）", "seconds"), fontsize=10)
        ax.set_title(subtitle, fontsize=11)
        ax.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.5)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

        span = max(values) if values else 1.0
        for y, v in zip(ypos, values):
            ax.text(v + span * 0.015, y, f"{v:.3f}", va="center",
                    fontsize=8.5, color="#333333")
        ax.set_xlim(0, span * 1.20)

    fig.tight_layout(rect=(0, 0, 1, 0.962))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor="white")
    plt.close(fig)
    print(f"[3/4] 性能分析图: {out_path}")
    return True


# ------------------------------------------------- 可选：gprof2dot 经典调用图

def try_gprof2dot(prof_path: Path, out_dir: Path, tag: str) -> None:
    """若本机同时具备 gprof2dot 与 Graphviz，则额外生成一张调用关系图。"""
    missing = [n for n in ("gprof2dot", "dot") if shutil.which(n) is None]
    if missing:
        print(f"[4/4] 跳过调用关系图: 缺少 {', '.join(missing)}"
              f"（装 Graphviz 后重跑即可自动补上）")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    dot_file = out_dir / f"callgraph_{tag}.dot"
    png_file = out_dir / f"callgraph_{tag}.png"
    try:
        with dot_file.open("w", encoding="utf-8") as fh:
            subprocess.run(["gprof2dot", "-f", "pstats", str(prof_path)],
                           check=True, stdout=fh)
        subprocess.run(["dot", "-Tpng", str(dot_file), "-o", str(png_file)], check=True)
        print(f"[4/4] 调用关系图: {png_file}")
    except subprocess.CalledProcessError as exc:
        print(f"[4/4] 调用关系图生成失败: {exc}")


# ------------------------------------------------------------------ 命令行入口

def main(argv: list[str] | None = None) -> int:
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

    target = normalize_target([t for t in args.target if t != "--"])
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
