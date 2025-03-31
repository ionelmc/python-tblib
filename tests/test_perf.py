from tblib import Traceback

EXAMPLE = """
Traceback (most recent call last):
  File "file1", line 9999, in <module>
    code1
  File "file2", line 9999, in <module>
    code2
  File "file3", line 9999, in <module>
    code3
  File "file4", line 9999, in <module>
    code4
  File "file5", line 9999, in <module>
    code5
  File "file6", line 9999, in <module>
    code6
  File "file7", line 9999, in <module>
    code7
  File "file8", line 9999, in <module>
    code8
  File "file9", line 9999, in <module>
    code9
"""


def test_perf(benchmark):
    @benchmark
    def run():
        Traceback.from_string(EXAMPLE).as_traceback()
