import sys
from types import TracebackType

from tblib import Traceback


def test_deep_traceback_as_dict():
    depth = sys.getrecursionlimit() + 10
    frame = sys._getframe()
    native = None
    for lineno in range(depth, 0, -1):
        native = TracebackType(native, frame, -1, lineno)
    converted = Traceback(native).as_dict()
    for lineno in range(1, depth + 1):
        assert converted['tb_lineno'] == lineno
        assert converted['tb_frame']['f_code']['co_name'] == 'test_deep_traceback_as_dict'
        converted = converted['tb_next']
    assert converted is None


def test_deep_traceback_from_dict():
    depth = sys.getrecursionlimit() + 10
    serialized = None
    for lineno in range(depth, 0, -1):
        serialized = {
            'tb_frame': {
                'f_globals': {'__name__': 'deep_example', '__file__': 'deep.py'},
                'f_locals': {'value': lineno},
                'f_code': {'co_filename': 'deep.py', 'co_name': 'recursive'},
                'f_lineno': lineno,
            },
            'tb_lineno': lineno,
            'tb_next': serialized,
        }
    converted = Traceback.from_dict(serialized)
    for lineno in range(1, depth + 1):
        assert converted.tb_lineno == lineno
        assert converted.tb_frame.f_lineno == lineno
        assert converted.tb_frame.f_locals == {'value': lineno}
        assert converted.tb_frame.f_globals == {'__name__': 'deep_example', '__file__': 'deep.py'}
        assert converted.tb_frame.f_code.co_name == 'recursive'
        converted = converted.tb_next
    assert converted is None
