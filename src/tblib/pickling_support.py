try:
    import copy_reg
except ImportError:
    import copyreg as copy_reg
from types import TracebackType

from . import Frame
from . import Traceback


def unpickle_traceback(*tb):
    ret = object.__new__(Traceback)
    if len(tb) == 3:
        ret.tb_frame, ret.tb_lineno, ret.tb_next = tb
    else:
        ret.tb_frame, ret.tb_lineno, ret.tb_lasti, ret.tb_next = tb
    return ret.as_traceback()


def pickle_traceback(tb):
    return unpickle_traceback, (Frame(tb.tb_frame), tb.tb_lineno, tb.tb_lasti, tb.tb_next and Traceback(tb.tb_next))


def install():
    copy_reg.pickle(TracebackType, pickle_traceback)
