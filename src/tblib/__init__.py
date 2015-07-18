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


class _AttrDict(dict):
    def __getattr__(self, attr):
        return self[attr]


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
        
        # Extras
        self.co_lnotab = getattr(code, 'co_lnotab', None)


class Frame(object):
    def __init__(self, frame):
        self.f_code = Code(frame.f_code)
        self.f_locals = {}
        self.f_globals = {}
        
        for local, value in getattr(frame, 'f_locals', {}).items():
            if can_pickle(value):
                self.f_locals[local] = value
                
        for local, value in getattr(frame, 'f_globals', {}).items():
            if can_pickle(value):
                self.f_globals[local] = value


class Traceback(object):
    def __init__(self, tb):
        self.tb_frame = Frame(tb.tb_frame)
        self.tb_lineno = tb.tb_lineno
        if tb.tb_next is None:
            self.tb_next = None
        else:
            self.tb_next = Traceback(tb.tb_next)
            
        # Extras
        self.tb_lasti = getattr(tb, 'tb_lasti', None)

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
                    code.co_firstlineno, b"",
                    (), ()
                )
            else:
                code = CodeType(
                    0,
                    f_code.co_nlocals, f_code.co_stacksize, f_code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename.encode(), f_code.co_name.encode(),
                    code.co_firstlineno, b"",
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

    def to_dict(self):
        """Convert a Traceback into a dictionary representation"""
        if self.tb_next is None:
            tb_next = None
        else:
            tb_next = self.tb_next.to_dict()

        code = {
            k: v
            for k, v in self.tb_frame.f_code.__dict__.items()
            if k.startswith('co_')
        }
        code['co_lnotab'] = code['co_lnotab'].decode("utf-8")
        frame = {
            'f_locals': {k:v for k,v in self.tb_frame.f_locals.items() if can_jsonify(v)},
            'f_globals': {k:v for k,v in self.tb_frame.f_globals.items() if can_jsonify(v)},
            'f_code': code
        }
        return {
            'tb_frame': frame,
            'tb_lineno': self.tb_lineno,
            'tb_next': tb_next,
            'tb_lasti': self.tb_lasti
        }

    @classmethod
    def from_dict(cls, dct):
        if dct['tb_next']:
            tb_next = cls.from_dict(dct['tb_next'])
        else:
            tb_next = None
        
        dct['tb_frame']['f_code']['co_lnotab'] = dct['tb_frame']['f_code']['co_lnotab'].encode("utf-8")
        frame = _AttrDict((
            ('f_globals', dct['tb_frame']['f_globals']),
            ('f_locals', dct['tb_frame']['f_locals']),
            ('f_code', _AttrDict((k, v) for k, v in dct['tb_frame']['f_code'].items()))
        ))
        tb = _AttrDict((
            ('tb_frame', frame),
            ('tb_lasti', dct['tb_lasti']),
            ('tb_lineno', dct['tb_lineno']),
            ('tb_next', tb_next)
        ))
        return cls(tb)

def can_pickle(val):
    import pickle
    if isinstance(val, TracebackType):
        return True
    try:
        pickle.dumps(val)
    except:
        return False
    else:
        return True
        
def can_jsonify(val):
    import json
    try:
        json.dumps(val)
    except:
        return False
    else:
        return True
