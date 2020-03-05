import traceback

from tblib import Traceback
from tblib import pickling_support

pickling_support.install()

pytest_plugins = 'pytester',


def test_parse_traceback():
    tb1 = Traceback.from_string(
        """
Traceback (most recent call last):
  File "file1", line 123, in <module>
    code1
  File "file2", line 234, in ???
    code2
  File "file3", line 345, in function3
  File "file4", line 456, in
    code4
KeyboardInterrupt"""
    )
    pytb = tb1.as_traceback()
    assert traceback.format_tb(pytb) == [
        '  File "file1", line 123, in <module>\n',
        '  File "file2", line 234, in ???\n',
        '  File "file3", line 345, in function3\n',
    ]
    tb2 = Traceback(pytb)

    expected_dict = {
        "tb_frame": {
            "f_code": {"co_filename": "file1", "co_name": "<module>"},
            "f_globals": {"__file__": "file1", "__name__": "?"},
            "f_lineno": 123,
        },
        "tb_lineno": 123,
        "tb_next": {
            "tb_frame": {
                "f_code": {"co_filename": "file2", "co_name": "???"},
                "f_globals": {"__file__": "file2", "__name__": "?"},
                "f_lineno": 234,
            },
            "tb_lineno": 234,
            "tb_next": {
                "tb_frame": {
                    "f_code": {"co_filename": "file3", "co_name": "function3"},
                    "f_globals": {"__file__": "file3", "__name__": "?"},
                    "f_lineno": 345,
                },
                "tb_lineno": 345,
                "tb_next": None,
            },
        },
    }
    tb3 = Traceback.from_dict(expected_dict)
    assert tb3.as_dict() == tb2.as_dict() == tb1.as_dict() == expected_dict


def test_pytest_integration(testdir):
    test = testdir.makepyfile("""
import six

from tblib import Traceback

def test_raise():
    tb1 = Traceback.from_string('''
Traceback (most recent call last):
  File "file1", line 123, in <module>
    code1
  File "file2", line 234, in ???
    code2
  File "file3", line 345, in function3
  File "file4", line 456, in ""
''')
    pytb = tb1.as_traceback()
    six.reraise(RuntimeError, RuntimeError(), pytb)
""")

    # mode(auto / long / short / line / native / no).

    result = testdir.runpytest_subprocess('--tb=long', '-vv', test)
    result.stdout.fnmatch_lines([
        "_ _ _ _ _ _ _ _ *",
        "",
        ">   [?][?][?]",
        "",
        "file1:123:*",
        "_ _ _ _ _ _ _ _ *",
        "",
        ">   [?][?][?]",
        "",
        "file2:234:*",
        "_ _ _ _ _ _ _ _ *",
        "",
        ">   [?][?][?]",
        "",
        "file3:345:*",
        "_ _ _ _ _ _ _ _ *",
        "",
        ">   [?][?][?]",
        "E   RuntimeError",
        "",
        "file4:456: RuntimeError",
        "===*=== 1 failed in * ===*===",
    ])

    result = testdir.runpytest_subprocess('--tb=short', '-vv', test)
    result.stdout.fnmatch_lines([
        'test_pytest_integration.py:*: in test_raise',
        '    six.reraise(RuntimeError, RuntimeError(), pytb)',
        'file1:123: in <module>',
        '    ???',
        'file2:234: in ???',
        '    ???',
        'file3:345: in function3',
        '    ???',
        'file4:456: in ""',
        '    ???',
        'E   RuntimeError',
    ])

    result = testdir.runpytest_subprocess('--tb=line', '-vv', test)
    result.stdout.fnmatch_lines([
        "===*=== FAILURES ===*===",
        "file4:456: RuntimeError",
        "===*=== 1 failed in * ===*===",
    ])

    result = testdir.runpytest_subprocess('--tb=native', '-vv', test)
    result.stdout.fnmatch_lines([
        'Traceback (most recent call last):',
        '  File "*test_pytest_integration.py", line *, in test_raise',
        '    six.reraise(RuntimeError, RuntimeError(), pytb)',
        '  File "file1", line 123, in <module>',
        '  File "file2", line 234, in ???',
        '  File "file3", line 345, in function3',
        '  File "file4", line 456, in ""',
        'RuntimeError',

    ])
