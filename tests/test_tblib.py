import io
import pickle
import sys
import traceback
import types

import pytest

from tblib import Traceback
from tblib import TracebackParseError
from tblib import _get_code_position
from tblib import _make_linetable_with_positions
from tblib import _make_pypy_linetable_with_positions
from tblib import pickling_support

pickling_support.install()

pytest_plugins = ('pytester',)

# Column position info requires Python 3.11+
has_column_positions = hasattr(types.CodeType, 'co_positions')


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

    # Check structure (excluding column fields which depend on source formatting)
    assert value['tb_frame'] == {
        'f_globals': {'__name__': 'test_tblib', '__file__': __file__},
        'f_locals': {},
        'f_code': {'co_filename': __file__, 'co_name': 'test_get_locals'},
        'f_lineno': lineno + 10,
    }
    assert value['tb_lineno'] == lineno
    assert value['tb_next']['tb_frame'] == {
        'f_globals': {'__name__': 'test_tblib', '__file__': __file__},
        'f_locals': {'my_variable': 1},
        'f_code': {'co_filename': __file__, 'co_name': 'func'},
        'f_lineno': lineno - 3,
    }
    assert value['tb_next']['tb_lineno'] == lineno - 3
    assert value['tb_next']['tb_next'] is None

    # On Python 3.11+, column position info should be present
    if has_column_positions:
        assert 'tb_colno' in value
        assert 'tb_end_colno' in value
        assert isinstance(value['tb_colno'], int)
        assert isinstance(value['tb_end_colno'], int)
        assert 'tb_colno' in value['tb_next']
        assert 'tb_end_colno' in value['tb_next']

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

    # Expected structure without column fields (parsed from string has no column info)
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

    # tb1 (from string) has no column info
    assert tb1.as_dict() == expected_dict

    # tb3, tb4 (from dict without column info) have no column info
    assert tb3.as_dict() == expected_dict
    assert tb4.as_dict() == expected_dict

    # tb2 (wrapped from reconstructed traceback) has column info on Python 3.11+
    # because it extracts positions from the stub code object
    tb2_dict = tb2.as_dict()
    if has_column_positions:
        # Column info should be present
        assert 'tb_colno' in tb2_dict

        # Remove column fields to compare structure
        def without_columns(d):
            if d is None:
                return None
            result = {k: v for k, v in d.items() if k not in ('tb_colno', 'tb_end_colno', 'tb_end_lineno')}
            if 'tb_next' in result:
                result['tb_next'] = without_columns(result['tb_next'])
            return result

        assert without_columns(tb2_dict) == expected_dict
    else:
        assert tb2_dict == expected_dict


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


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_caret_position_preserved():
    """Test that caret positions are preserved through reconstruction."""

    def inner():
        x = {'a': 1}
        return x['b']  # KeyError here - caret should point to x['b']

    try:
        inner()
    except KeyError:
        original_tb = sys.exc_info()[2]

        tb_wrapper = Traceback(original_tb)

        inner_frame = tb_wrapper.tb_next
        assert inner_frame.tb_colno is not None, 'tb_colno should be captured'
        assert inner_frame.tb_end_colno is not None, 'tb_end_colno should be captured'

        reconstructed_tb = tb_wrapper.as_traceback()

        original_output = io.StringIO()
        traceback.print_exception(KeyError, KeyError('b'), original_tb, file=original_output)

        reconstructed_output = io.StringIO()
        traceback.print_exception(KeyError, KeyError('b'), reconstructed_tb, file=reconstructed_output)

        original_lines = original_output.getvalue().splitlines()
        reconstructed_lines = reconstructed_output.getvalue().splitlines()

        assert len(original_lines) == len(reconstructed_lines), (
            f'Different number of lines: {len(original_lines)} vs {len(reconstructed_lines)}'
        )

        for i, (orig, recon) in enumerate(zip(original_lines, reconstructed_lines)):
            assert orig == recon, f'Line {i} differs:\n  Original:      {orig!r}\n  Reconstructed: {recon!r}'


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_caret_position_in_dict():
    """Test that caret positions are preserved in dictionary serialization."""

    def inner():
        x = {'a': 1}
        return x['b']

    try:
        inner()
    except KeyError:
        original_tb = sys.exc_info()[2]

        tb_wrapper = Traceback(original_tb)
        tb_dict = tb_wrapper.as_dict()

        inner_dict = tb_dict['tb_next']
        assert 'tb_colno' in inner_dict, 'tb_colno should be in dict'
        assert 'tb_end_colno' in inner_dict, 'tb_end_colno should be in dict'
        assert inner_dict['tb_colno'] is not None
        assert inner_dict['tb_end_colno'] is not None

        tb_from_dict = Traceback.from_dict(tb_dict)
        assert tb_from_dict.tb_next.tb_colno == inner_dict['tb_colno']
        assert tb_from_dict.tb_next.tb_end_colno == inner_dict['tb_end_colno']


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_caret_position_pickle():
    """Test that caret positions are preserved through pickling."""

    def inner():
        x = {'a': 1}
        return x['b']

    try:
        inner()
    except KeyError:
        original_tb = sys.exc_info()[2]

        tb_wrapper = Traceback(original_tb)
        original_colno = tb_wrapper.tb_next.tb_colno
        original_end_colno = tb_wrapper.tb_next.tb_end_colno

        # Pickle and unpickle
        pickled = pickle.dumps(tb_wrapper)
        unpickled = pickle.loads(pickled)

        assert unpickled.tb_next.tb_colno == original_colno
        assert unpickled.tb_next.tb_end_colno == original_end_colno


def test_caret_position_without_column_info():
    """Test that reconstruction works when column info is not available."""
    tb = Traceback.from_string(
        """
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    foo()
ValueError: test
"""
    )

    assert tb.tb_colno is None
    assert tb.tb_end_colno is None

    reconstructed = tb.as_traceback()
    assert reconstructed is not None
    assert reconstructed.tb_lineno == 10


def test_caret_position_chained_exceptions():
    """Test caret positions with chained exceptions."""

    def outer():
        inner()

    def inner():
        x = [1, 2, 3]
        return x[10]  # IndexError here

    try:
        outer()
    except IndexError:
        original_tb = sys.exc_info()[2]

        tb_wrapper = Traceback(original_tb)
        reconstructed_tb = tb_wrapper.as_traceback()

        # Walk both chains and compare
        orig = original_tb
        recon = reconstructed_tb
        while orig is not None:
            assert recon is not None, 'Reconstructed chain is shorter'
            assert orig.tb_lineno == recon.tb_lineno
            orig = orig.tb_next
            recon = recon.tb_next
        assert recon is None, 'Reconstructed chain is longer'


def test_traceback_from_string_invalid():
    """Test TracebackParseError is raised for invalid input."""
    with pytest.raises(TracebackParseError, match='Could not find any frames'):
        Traceback.from_string('Not a valid traceback')


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_get_code_position_edge_cases():
    """Test _get_code_position edge cases for coverage."""
    class FakeCode:
        pass

    result = _get_code_position(FakeCode(), 0)
    assert result == (None, None, None, None)

    code = compile('x = 1', '<test>', 'exec')
    result = _get_code_position(code, -1)
    assert result == (None, None, None, None)


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_linetable_functions_with_none():
    """Test linetable creation functions handle None values correctly."""
    if sys.implementation.name == 'pypy':
        result = _make_pypy_linetable_with_positions(None, 10, 5)
        assert isinstance(result, bytes)

        result = _make_pypy_linetable_with_positions(5, None, 5)
        assert isinstance(result, bytes)
    else:
        result = _make_linetable_with_positions(None, 10)
        assert isinstance(result, bytes)

        result = _make_linetable_with_positions(5, None)
        assert isinstance(result, bytes)


@pytest.mark.skipif(not has_column_positions, reason='Column positions require Python 3.11+')
def test_traceback_maker_in_globals():
    """
    Test that __traceback_maker is properly defined in globals during reconstruction.

    Without __traceback_maker in globals, LOAD_NAME would raise NameError at
    tb_lasti=2 (column 6-23), instead of RAISE_VARARGS executing at tb_lasti=4
    (column 0-23). This would capture column positions from the wrong instruction,
    showing only '__traceback_maker' instead of the full 'raise __traceback_maker'
    expression.
    """

    def cause_error():
        result = 1 / 0  # Division at specific columns
        return result

    try:
        cause_error()
    except ZeroDivisionError:
        original_tb = sys.exc_info()[2]

        # Get original column info
        tb_wrapper = Traceback(original_tb)
        original_colno = tb_wrapper.tb_next.tb_colno
        original_end_colno = tb_wrapper.tb_next.tb_end_colno

        # These should be non-None if captured correctly
        assert original_colno is not None, 'Should capture column start'
        assert original_end_colno is not None, 'Should capture column end'

        # Reconstruct traceback
        reconstructed_tb = tb_wrapper.as_traceback()
        assert reconstructed_tb.tb_next is not None

        # Verify the code object has the correct column positions
        code = reconstructed_tb.tb_next.tb_frame.f_code
        if hasattr(code, 'co_positions'):
            # Get positions for the RAISE_VARARGS instruction (should be last)
            positions = list(code.co_positions())
            last_pos = positions[-1]

            # The last position should match our captured columns
            assert last_pos[2] == original_colno, f'Column start mismatch: {last_pos[2]} != {original_colno}'
            assert last_pos[3] == original_end_colno, f'Column end mismatch: {last_pos[3]} != {original_end_colno}'

            # Critically: column start should be 0 (full expression), not 6 (just '__traceback_maker')
            # If __traceback_maker wasn't in globals, we'd get column 6 from LOAD_NAME instruction
            assert last_pos[2] != 6, 'Column positions from wrong instruction (LOAD_NAME instead of RAISE_VARARGS)'
