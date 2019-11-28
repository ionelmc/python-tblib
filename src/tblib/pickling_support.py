import sys
from types import TracebackType

from . import Frame
from . import Traceback

if sys.version_info.major >= 3:
    import copyreg
    import pickle
else:
    import copy_reg as copyreg
    import cPickle as pickle


def unpickle_traceback(tb_frame, tb_lineno, tb_next):
    ret = object.__new__(Traceback)
    ret.tb_frame = tb_frame
    ret.tb_lineno = tb_lineno
    ret.tb_next = tb_next
    return ret.as_traceback()


def pickle_traceback(tb):
    return unpickle_traceback, (Frame(tb.tb_frame), tb.tb_lineno, tb.tb_next and Traceback(tb.tb_next))


def unpickle_exception(func, args, cause, tb):
    inst = func(*args)
    inst.__cause__ = cause
    inst.__traceback__ = tb
    return inst


def pickle_exception(obj):
    # Check for a __reduce_ex__ method, fall back to __reduce__
    reduce = getattr(obj, "__reduce_ex__", None)
    if reduce is not None:
        # __reduce_ex__(4) should be no different from __reduce_ex__(3).
        # __reduce_ex__(5) could bring benefits in the unlikely case the exception
        # directly contains buffers, but PickleBuffer objects will cause a crash when
        # running on protocol=4, and there's no clean way to figure out the current
        # protocol from here. Note that any object returned by __reduce_ex__(3) will
        # still be pickled with protocol 5 if pickle.dump() is running with it.
        rv = reduce(3)
    else:
        reduce = getattr(obj, "__reduce__", None)
        if reduce is not None:
            rv = reduce()
        else:
            raise pickle.PicklingError(
                "Can't pickle %r object: %r" % (obj.__class__.__name__, obj)
            )
    if isinstance(rv, str):
        raise TypeError("str __reduce__ output is not supported")
    assert isinstance(rv, tuple) and len(rv) >= 2

    return (unpickle_exception, rv[:2] + (obj.__cause__, obj.__traceback__)) + rv[2:]


def _get_subclasses(cls):
    # Depth-first traversal of all direct and indirect subclasses of cls
    to_visit = [cls]
    while to_visit:
        this = to_visit.pop()
        yield this
        to_visit += list(this.__subclasses__())


def install(*exception_instances):
    copyreg.pickle(TracebackType, pickle_traceback)

    if sys.version_info.major < 3:
        return

    if exception_instances:
        for exc in exception_instances:
            while exc is not None:
                copyreg.pickle(type(exc), pickle_exception)
                exc = exc.__cause__

    else:
        for exception_cls in _get_subclasses(BaseException):
            copyreg.pickle(exception_cls, pickle_exception)
