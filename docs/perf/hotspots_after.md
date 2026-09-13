# 消耗最大的函数 Top-N（after）

程序总耗时（cProfile 计时）：**0.2772 秒**。占比 = 该函数耗时 ÷ 程序总耗时。

## 按自身耗时排序（tottime，不含子函数调用）

| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |
|---|---|---|---|---|---|---|
| 1 | `lcs_length_bitparallel` | similarity.py | 50 | 0.1122 | 0.1482 | 53.5% |
| 2 | `<built-in method _io.open>` | ~ | 3 | 0.0716 | 0.0716 | 25.8% |
| 3 | `<method 'get' of 'dict' objects>` | ~ | 385750 | 0.0358 | 0.0358 | 12.9% |
| 4 | `<method 'findall' of 're.Pattern' objects>` | ~ | 2 | 0.0290 | 0.0290 | 10.4% |
| 5 | `_optimize_charset` | _compiler.py | 8 | 0.0029 | 0.0030 | 1.1% |
| 6 | `<built-in method nt.stat>` | ~ | 26 | 0.0020 | 0.0021 | 0.8% |
| 7 | `normalize` | locale.py, preprocess.py | 8 | 0.0016 | 0.0319 | 11.5% |
| 8 | `<method 'join' of 'str' objects>` | ~ | 127 | 0.0013 | 0.0013 | 0.5% |
| 9 | `<built-in method _io.open_code>` | ~ | 9 | 0.0008 | 0.0008 | 0.3% |
| 10 | `<method 'read' of '_io.BufferedReader' objects>` | ~ | 7 | 0.0006 | 0.0006 | 0.2% |
| 11 | `<built-in method _codecs.utf_8_decode>` | ~ | 2 | 0.0004 | 0.0004 | 0.1% |
| 12 | `<method '__exit__' of '_io._IOBase' objects>` | ~ | 8 | 0.0003 | 0.0003 | 0.1% |

## 按累计耗时排序（cumtime，含子函数调用）

| 排名 | 函数 | 来源文件 | 调用次数 | tottime(s) | cumtime(s) | 占比 |
|---|---|---|---|---|---|---|
| 1 | `main` | main.py | 1 | 0.0001 | 0.2551 | 92.0% |
| 2 | `_run` | main.py | 1 | 0.0000 | 0.2538 | 91.6% |
| 3 | `similarity_report` | similarity.py | 1 | 0.0000 | 0.1485 | 53.6% |
| 4 | `chunked_common_length` | similarity.py | 1 | 0.0002 | 0.1485 | 53.6% |
| 5 | `lcs_length` | similarity.py | 50 | 0.0000 | 0.1482 | 53.5% |
| 6 | `lcs_length_bitparallel` | similarity.py | 50 | 0.1122 | 0.1482 | 53.5% |
| 7 | `_load_text` | main.py | 2 | 0.0001 | 0.1036 | 37.4% |
| 8 | `read_text_file` | io_utils.py | 2 | 0.0001 | 0.0716 | 25.8% |
| 9 | `open` | _local.py | 3 | 0.0000 | 0.0716 | 25.8% |
| 10 | `<built-in method _io.open>` | ~ | 3 | 0.0716 | 0.0716 | 25.8% |
| 11 | `read_bytes` | _abc.py | 2 | 0.0000 | 0.0708 | 25.5% |
| 12 | `<method 'get' of 'dict' objects>` | ~ | 385750 | 0.0358 | 0.0358 | 12.9% |
