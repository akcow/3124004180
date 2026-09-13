# 论文查重

一个用 Python 3 实现的论文查重程序：给定原文与经过增删改的抄袭版论文，计算抄袭版相对原文的**重复率**。

[![tests](https://github.com/akcow/3124004180/actions/workflows/tests.yml/badge.svg)](https://github.com/akcow/3124004180/actions)

## 快速开始

```bash
python main.py <原文文件绝对路径> <抄袭版论文文件绝对路径> <答案文件绝对路径>
```

例子（仓库自带样例文本）：

```bash
python main.py text_files/orig.txt text_files/orig_0.8_del.txt out.txt
```

答案文件内容形如 `0.80`——一个 0~1 的浮点，精确到小数点后两位，文件里只有数字本身。

## 环境要求

- Python 3.10 或更高（开发环境为 3.13）
- **运行期零第三方依赖**，只用标准库。评测机不需要 `pip install` 任何东西。

## 算法说明

### 重复率的定义

```
重复率 = LCS(原文, 抄袭版) / len(原文)
```

即：**原文中有多大比例的内容，在抄袭版里被原样、按序保留了下来**。

其中 LCS 是最长公共子序列。这个口径的好处是语义直接、结果可解释：

- 抄袭版在原文基础上**新增**内容 → 原文被 100% 抄走 → `1.00`
- 抄袭版**删掉**两成内容 → `0.80`
- 内容被打乱重排 → 按重排程度递减

程序另提供 `--metric max_base` 切换到 `LCS / max(len(原文), len(抄袭版))` 口径。

### 文本处理

只保留汉字，丢弃标点、空白、数字与字母。标点几乎不承载语义，却会在字符级噪声下大量误判。

### 性能

核心相似度计算使用**位并行 LCS**：把模式串的每个字符映射到大整数的某一位，从而把
O(n·m) 次 Python 层循环压缩成 O(n·m/64) 次大整数位运算。实测 10 万字输入约 0.7 秒
（朴素动态规划要数百秒）。

性能改进的完整记录（剖析图、消耗最大的函数、改进前后对比）见
[`docs/performance.md`](docs/performance.md) 与 [`docs/perf/`](docs/perf/)。

## 测试与质量

| 指标 | 结果 |
|---|---|
| 单元测试 | 54 个用例全部通过 |
| 语句覆盖率 | 100%（192 条语句） |
| pylint | 10.00 / 10 |
| flake8 | 零告警 |

测试设计与充分性自评见 [`docs/test-report.md`](docs/test-report.md)。
每次 push 都会由 GitHub Actions 自动跑全量测试与静态检查。

## 开发

```bash
# 1. 建虚拟环境并装开发期依赖（运行程序本身不需要）
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt

# 2. 跑测试
.venv/Scripts/python -m pytest

# 3. 静态检查（要求零警告）
.venv/Scripts/python -m pylint main.py similarity.py preprocess.py io_utils.py tools

# 4. 生成性能分析图
.venv/Scripts/python tools/profiling.py --tag before \
    --out docs/perf/profile_before.png \
    -- python main.py text_files/orig.txt text_files/orig_0.8_del.txt out.txt
```

## 目录结构

```
3124004180/
├── main.py                  # 命令行入口
├── similarity.py            # 相似度计算（LCS + 重复率）
├── preprocess.py            # 文本归一化
├── io_utils.py              # 编码自适应读写
├── requirements-dev.txt     # 仅开发期依赖
├── plan.md                  # 开发计划
├── .github/workflows/       # 每次 push 自动跑测试与静态检查
├── docs/
│   ├── test-report.md       # 测试设计与充分性评估
│   ├── performance.md       # 性能改进总结
│   └── perf/                # 性能改进的证据（图、数据、工时）
├── tests/                   # 单元测试
├── tools/                   # 开发期工具（造数据、基准、剖析出图）
└── text_files/              # 样例文本
```

## 许可

课程作业，仅用于学习。
