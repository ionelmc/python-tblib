import sys
from types import TracebackType

from . import Frame
from . import Traceback

if sys.version_info.major >= 3:
    import copyreg
else:
    import copy_reg as copyreg


def unpickle_traceback(tb_frame, tb_lineno, tb_next):
    ret = object.__new__(Traceback)
    ret.tb_frame = tb_frame
    ret.tb_lineno = tb_lineno
    ret.tb_next = tb_next
    return ret.as_traceback()


def pickle_traceback(tb):
    return unpickle_traceback, (Frame(tb.tb_frame), tb.tb_lineno, tb.tb_next and Traceback(tb.tb_next))


# unpickle_exception_3_11() / pickle_exception_3_11() are used in Python 3.11 and newer

def unpickle_exception_3_11(func, args, cause, context, notes, suppress_context, tb):
    inst = func(*args)
    inst.__cause__ = cause
    inst.__context__ = context
    if notes is not None:
        inst.__notes__ = notes
    inst.__suppress_context__ = suppress_context
    inst.__traceback__ = tb
    return inst


def pickle_exception_3_11(obj):
    # All exceptions, unlike generic Python objects, define __reduce_ex__
    # __reduce_ex__(4) should be no different from __reduce_ex__(3).
    # __reduce_ex__(5) could bring benefits in the unlikely case the exception
    # directly contains buffers, but PickleBuffer objects will cause a crash when
    # running on protocol=4, and there's no clean way to figure out the current
    # protocol from here. Note that any object returned by __reduce_ex__(3) will
    # still be pickled with protocol 5 if pickle.dump() is running with it.
    rv = obj.__reduce_ex__(3)
    if isinstance(rv, str):
        raise TypeError('str __reduce__ output is not supported')
    assert isinstance(rv, tuple)
    assert len(rv) >= 2

    return (
        unpickle_exception_3_11,
        rv[:2] + (
            obj.__cause__,
            obj.__context__,
            getattr(obj, "__notes__", None),
            obj.__suppress_context__,
            obj.__traceback__,
        ),
    ) + rv[2:]


# unpickle_exception() / pickle_exception() are used on Python 3.10 and older; or when deserializing
# old Pickle archives created by Python 3.10 and older.

def unpickle_exception(func, args, cause, tb):
    inst = func(*args)
    inst.__cause__ = cause
    inst.__traceback__ = tb
    return inst


def pickle_exception(obj):
    rv = obj.__reduce_ex__(3)
    if isinstance(rv, str):
        raise TypeError('str __reduce__ output is not supported')
    assert isinstance(rv, tuple)
    assert len(rv) >= 2

    # NOTE: The __context__ and __suppress_context__ attributes actually existed prior to Python
    # 3.11, so in theory we should support them here. But existing Pickle archives might refer to
    # unpickle_exception(), so we need to keep it around anyway; and it's not worth the trouble
    # introducing a third pair of pickling/unpickling functions.

    return (unpickle_exception, rv[:2] + (obj.__cause__, obj.__traceback__)) + rv[2:]


if sys.version_info >= (3, 11):
    pickle_exception_latest = pickle_exception_3_11
else:
    pickle_exception_latest = pickle_exception


def _get_subclasses(cls):
    # Depth-first traversal of all direct and indirect subclasses of cls
    to_visit = [cls]
    while to_visit:
        this = to_visit.pop()
        yield this
        to_visit += list(this.__subclasses__())


def install(*exc_classes_or_instances):
    copyreg.pickle(TracebackType, pickle_traceback)

    if sys.version_info.major < 3:
        # Dummy decorator?
        if len(exc_classes_or_instances) == 1:
            exc = exc_classes_or_instances[0]
            if isinstance(exc, type) and issubclass(exc, BaseException):
                return exc
        return

    if not exc_classes_or_instances:
        for exception_cls in _get_subclasses(BaseException):
            copyreg.pickle(exception_cls, pickle_exception_latest)
        return

    for exc in exc_classes_or_instances:
        if isinstance(exc, BaseException):
            _install_for_instance(exc, set())
        elif isinstance(exc, type) and issubclass(exc, BaseException):
            copyreg.pickle(exc, pickle_exception_latest)
            # Allow using @install as a decorator for Exception classes
            if len(exc_classes_or_instances) == 1:
                return exc
        else:
            raise TypeError('Expected subclasses or instances of BaseException, got %s' % (type(exc)))

def _install_for_instance(exc, seen):
    assert isinstance(exc, BaseException)

    # Prevent infinite recursion if we somehow get a self-referential exception. (Self-referential
    # exceptions should never normally happen, but if it did somehow happen, we want to pickle the
    # exception faithfully so the developer can troubleshoot why it happened.)
    if id(exc) in seen:
        return
    seen.add(id(exc))

    copyreg.pickle(type(exc), pickle_exception_latest)

    if exc.__cause__ is not None:
        _install_for_instance(exc.__cause__, seen)
    if exc.__context__ is not None:
        _install_for_instance(exc.__context__, seen)

    # This case is meant to cover BaseExceptionGroup on Python 3.11 as well as backports like the
    # exceptiongroup module
    if hasattr(exc, "exceptions") and isinstance(exc.exceptions, (tuple, list)):
        for subexc in exc.exceptions:
            if isinstance(subexc, BaseException):
                _install_for_instance(subexc, seen)