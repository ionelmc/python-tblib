import pickle
import traceback

from tblib import Traceback
from tblib import pickling_support

pickling_support.install()

pytest_plugins = ('pytester',)


def test_get_locals():
    def get_locals(frame):
        print(frame, frame.f_locals)
        if 'my_variable' in frame.f_locals:
            return {'my_variable': int(frame.f_locals['my_variable'])}
        else:
            return {}

    def func(my_arg='2'):
        my_variable = '1'
        raise ValueError(my_variable)

    try:
        func()
    except Exception as e:
        exc = e
    else:
        raise AssertionError

    f_locals = exc.__traceback__.tb_next.tb_frame.f_locals
    assert 'my_variable' in f_locals
    assert f_locals['my_variable'] == '1'

    value = Traceback(exc.__traceback__, get_locals=get_locals).as_dict()
    lineno = exc.__traceback__.tb_lineno
    assert value == {
        'tb_frame': {
            'f_globals': {'__name__': 'test_tblib', '__file__': __file__},
            'f_locals': {},
            'f_code': {'co_filename': __file__, 'co_name': 'test_get_locals'},
            'f_lineno': lineno + 10,
        },
        'tb_lineno': lineno,
        'tb_next': {
            'tb_frame': {
                'f_globals': {'__name__': 'test_tblib', '__file__': __file__},
                'f_locals': {'my_variable': 1},
                'f_code': {'co_filename': __file__, 'co_name': 'func'},
                'f_lineno': lineno - 3,
            },
            'tb_lineno': lineno - 3,
            'tb_next': None,
        },
    }

    assert Traceback.from_dict(value).tb_next.tb_frame.f_locals == {'my_variable': 1}


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
        'tb_frame': {
            'f_code': {'co_filename': 'file1', 'co_name': '<module>'},
            'f_globals': {'__file__': 'file1', '__name__': '?'},
            'f_locals': {},
            'f_lineno': 123,
        },
        'tb_lineno': 123,
        'tb_next': {
            'tb_frame': {
                'f_code': {'co_filename': 'file2', 'co_name': '???'},
                'f_globals': {'__file__': 'file2', '__name__': '?'},
                'f_locals': {},
                'f_lineno': 234,
            },
            'tb_lineno': 234,
            'tb_next': {
                'tb_frame': {
                    'f_code': {'co_filename': 'file3', 'co_name': 'function3'},
                    'f_globals': {'__file__': 'file3', '__name__': '?'},
                    'f_locals': {},
                    'f_lineno': 345,
                },
                'tb_lineno': 345,
                'tb_next': None,
            },
        },
    }
    tb3 = Traceback.from_dict(expected_dict)
    tb4 = pickle.loads(pickle.dumps(tb3))
    assert tb4.as_dict() == tb3.as_dict() == tb2.as_dict() == tb1.as_dict() == expected_dict


def test_large_line_number():
    line_number = 2**31 - 1
    tb1 = Traceback.from_string(
        f"""
Traceback (most recent call last):
  File "file1", line {line_number}, in <module>
    code1
"""
    ).as_traceback()
    assert tb1.tb_lineno == line_number


def test_pytest_integration(testdir):
    test = testdir.makepyfile(
        """
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
    raise RuntimeError().with_traceback(pytb)
"""
    )

    # mode(auto / long / short / line / native / no).

    result = testdir.runpytest_subprocess('--tb=long', '-vv', test)
    result.stdout.fnmatch_lines(
        [
            '_ _ _ _ _ _ _ _ *',
            '',
            '>   [?][?][?]',
            '',
            'file1:123:*',
            '_ _ _ _ _ _ _ _ *',
            '',
            '>   [?][?][?]',
            '',
            'file2:234:*',
            '_ _ _ _ _ _ _ _ *',
            '',
            '>   [?][?][?]',
            '',
            'file3:345:*',
            '_ _ _ _ _ _ _ _ *',
            '',
            '>   [?][?][?]',
            'E   RuntimeError',
            '',
            'file4:456: RuntimeError',
            '===*=== 1 failed in * ===*===',
        ]
    )

    result = testdir.runpytest_subprocess('--tb=short', '-vv', test)
    result.stdout.fnmatch_lines(
        [
            'test_pytest_integration.py:*: in test_raise',
            '    raise RuntimeError().with_traceback(pytb)',
            'file1:123: in <module>',
            '    ???',
            'file2:234: in ???',
            '    ???',
            'file3:345: in function3',
            '    ???',
            'file4:456: in ""',
            '    ???',
            'E   RuntimeError',
        ]
    )

    result = testdir.runpytest_subprocess('--tb=line', '-vv', test)
    result.stdout.fnmatch_lines(
        [
            '===*=== FAILURES ===*===',
            'file4:456: RuntimeError',
            '===*=== 1 failed in * ===*===',
        ]
    )

    result = testdir.runpytest_subprocess('--tb=native', '-vv', test)
    result.stdout.fnmatch_lines(
        [
            'Traceback (most recent call last):',
            '  File "*test_pytest_integration.py", line *, in test_raise',
            '    raise RuntimeError().with_traceback(pytb)',
            '  File "file1", line 123, in <module>',
            '  File "file2", line 234, in ???',
            '  File "file3", line 345, in function3',
            '  File "file4", line 456, in ""',
            'RuntimeError',
        ]
    )
