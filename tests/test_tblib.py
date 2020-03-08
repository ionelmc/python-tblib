import traceback

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from _pytest._code import ExceptionInfo

from tblib import pickling_support, Traceback, _AttrDict

pickling_support.install()


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
        },
        "tb_lineno": 123,
        "tb_next": {
            "tb_frame": {
                "f_code": {"co_filename": "file2", "co_name": "???"},
                "f_globals": {"__file__": "file2", "__name__": "?"},
            },
            "tb_lineno": 234,
            "tb_next": {
                "tb_frame": {
                    "f_code": {"co_filename": "file3", "co_name": "function3"},
                    "f_globals": {"__file__": "file3", "__name__": "?"},
                },
                "tb_lineno": 345,
                "tb_next": None,
            },
        },
    }

    ei = ExceptionInfo.from_exc_info((KeyboardInterrupt, KeyboardInterrupt(), pytb))
    out = StringIO()
    tw = _AttrDict(
        line=lambda string, **_: out.write(string + '\n'),
        write=lambda string, **_: out.write(string),
        sep=lambda string: out.write(string),
    )
    ei.getrepr(style='long').toterminal(tw)
    print(out.getvalue())
    assert out.getvalue() == """
>   ???

file1:123:{0}
_{0}
>   ???

file2:234:{0}
_{0}
>   ???
E   KeyboardInterrupt

file3:345: KeyboardInterrupt
""".format(' ')

    tb3 = Traceback.from_dict(expected_dict)
    assert tb3.as_dict() == tb2.as_dict() == tb1.as_dict() == expected_dict
