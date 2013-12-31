try:
    from __pypy__ import tproxy
except ImportError:
    tproxy = None
try:
    from .cpython import tb_set_next
except ImportError:
    tb_set_next = None

if not tb_set_next and not tproxy:
    raise ImportError("Cannot use tblib. Runtime not supported.")

import sys

from types import CodeType
from types import TracebackType

PY3 = sys.version_info[0] == 3

class __traceback_maker(Exception):
    pass

class Code(object):
    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name
        self.co_nlocals = code.co_nlocals
        self.co_stacksize = code.co_stacksize
        self.co_flags = code.co_flags
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab

class Frame(object):
    def __init__(self, frame):
        self.f_globals = {
            k: v for k, v in frame.f_globals.items() if k in ("__file__", "__name__")
        }
        self.f_code = Code(frame.f_code)

class Traceback(object):
    def __init__(self, tb):
        self.tb_frame = Frame(tb.tb_frame)
        self.tb_lineno = tb.tb_lineno
        if tb.tb_next is None:
            self.tb_next = None
        else:
            self.tb_next = Traceback(tb.tb_next)

    def as_traceback(self):
        if tproxy:
            return tproxy(TracebackType, self.__tproxy_handler)
        elif tb_set_next:
            f_code = self.tb_frame.f_code
            code = compile('\n' * (self.tb_lineno - 1) + 'raise __traceback_maker', self.tb_frame.f_code.co_filename, 'exec')
            if PY3:
                code = CodeType(
                    0, 0,
                    f_code.co_nlocals, f_code.co_stacksize, f_code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename, f_code.co_name,
                    code.co_firstlineno, code.co_lnotab,
                    (), ()
                )
            else:
                code = CodeType(
                    0,
                    f_code.co_nlocals, f_code.co_stacksize, f_code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename, f_code.co_name,
                    code.co_firstlineno, code.co_lnotab,
                    (), ()
                )

            try:
                exec(code, self.tb_frame.f_globals, {})
            except:
                tb = sys.exc_info()[2].tb_next
                tb_set_next(tb, self.tb_next and self.tb_next.as_traceback())
                return tb
        else:
            raise RuntimeError("Cannot re-create traceback !")

    def __tproxy_handler(self, operation, *args, **kwargs):
        if operation in ('__getattribute__', '__getattr__'):
            if args[0] == 'tb_next':
                return self.tb_next and self.tb_next.as_traceback()
            else:
                return getattr(self, args[0])
        else:
            return getattr(self, operation)(*args, **kwargs)
