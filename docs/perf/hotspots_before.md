# 消耗最大的函数 Top-N（before）

程序总耗时（cProfile 计时）：**1.3187 秒**。占比 = 该函数耗时 ÷ 程序总耗时。

## 按自身耗时排序（tottime，不含子函数调用）

| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |
|---|---|---|---|---|---|---|
| 1 | `lcs_length_dp` | similarity.py | 1 | 1.2786 | 1.2786 | 97.0% |
| 2 | `<built-in method _io.open>` | ~ | 3 | 0.0133 | 0.0133 | 1.0% |
| 3 | `<built-in method nt.stat>` | ~ | 26 | 0.0026 | 0.0027 | 0.2% |
| 4 | `_optimize_charset` | _compiler.py | 8 | 0.0025 | 0.0026 | 0.2% |
| 5 | `<built-in method _io.open_code>` | ~ | 9 | 0.0010 | 0.0010 | 0.1% |
| 6 | `<method 'findall' of 're.Pattern' objects>` | ~ | 2 | 0.0006 | 0.0006 | 0.0% |
| 7 | `<method 'read' of '_io.BufferedReader' objects>` | ~ | 7 | 0.0005 | 0.0005 | 0.0% |
| 8 | `<method '__exit__' of '_io._IOBase' objects>` | ~ | 8 | 0.0004 | 0.0004 | 0.0% |
| 9 | `<built-in method builtins.__build_class__>` | ~ | 33 | 0.0003 | 0.0003 | 0.0% |
| 10 | `_path_join` | <frozen importlib._bootstrap_external> | 65 | 0.0003 | 0.0004 | 0.0% |
| 11 | `<built-in method nt._path_exists>` | ~ | 3 | 0.0002 | 0.0002 | 0.0% |
| 12 | `__init__` | <frozen codecs>, <frozen importlib._bootstrap>, <frozen importlib._bootstrap_external>, <string>, __future__.py, _local.py, _parser.py, argparse.py, dataclasses.py | 135 | 0.0002 | 0.0015 | 0.1% |

## 按累计耗时排序（cumtime，含子函数调用）

| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |
|---|---|---|---|---|---|---|
| 1 | `main` | main.py | 1 | 0.0000 | 1.2954 | 98.2% |
| 2 | `_run` | main.py | 1 | 0.0000 | 1.2941 | 98.1% |
| 3 | `similarity_report` | similarity.py | 1 | 0.0000 | 1.2787 | 97.0% |
| 4 | `lcs_length` | similarity.py | 1 | 0.0000 | 1.2787 | 97.0% |
| 5 | `lcs_length_dp` | similarity.py | 1 | 1.2786 | 1.2786 | 97.0% |
| 6 | `_find_and_load` | <frozen importlib._bootstrap> | 5 | 0.0000 | 0.0232 | 1.8% |
| 7 | `_find_and_load_unlocked` | <frozen importlib._bootstrap> | 5 | 0.0000 | 0.0229 | 1.7% |
| 8 | `_load_unlocked` | <frozen importlib._bootstrap> | 5 | 0.0000 | 0.0203 | 1.5% |
| 9 | `exec_module` | <frozen importlib._bootstrap_external> | 5 | 0.0001 | 0.0201 | 1.5% |
| 10 | `_call_with_frames_removed` | <frozen importlib._bootstrap> | 14 | 0.0000 | 0.0180 | 1.4% |
| 11 | `get_code` | <frozen importlib._bootstrap_external> | 5 | 0.0001 | 0.0155 | 1.2% |
| 12 | `_load_text` | main.py | 2 | 0.0000 | 0.0138 | 1.0% |
