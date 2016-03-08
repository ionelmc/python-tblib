import re
import sys
from types import CodeType
from types import TracebackType

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

__version__ = '1.3.0'
__all__ = 'Traceback',

PY3 = sys.version_info[0] == 3
FRAME_RE = re.compile(r'^\s*File "(?P<co_filename>.+)", line (?P<tb_lineno>\d+)(, in (?P<co_name>.+))?$')


class _AttrDict(dict):
    __slots__ = ()
    __getattr__ = dict.__getitem__


# noinspection PyPep8Naming
class __traceback_maker(Exception):
    pass


class TracebackParseError(Exception):
    pass


class Code(object):
    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name


class Frame(object):
    def __init__(self, frame):
        self.f_globals = dict([
            (k, v)
            for k, v in frame.f_globals.items()
            if k in ("__file__", "__name__")
        ])
        self.f_code = Code(frame.f_code)


class Traceback(object):
    def __init__(self, tb):
        self.tb_frame = Frame(tb.tb_frame)
        # noinspection SpellCheckingInspection
        self.tb_lineno = int(tb.tb_lineno)
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
                    0, code.co_kwonlyargcount,
                    code.co_nlocals, code.co_stacksize, code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename, f_code.co_name,
                    code.co_firstlineno, code.co_lnotab, (), ()
                )
            else:
                code = CodeType(
                    0,
                    code.co_nlocals, code.co_stacksize, code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename.encode(), f_code.co_name.encode(),
                    code.co_firstlineno, code.co_lnotab, (), ()
                )

            # noinspection PyBroadException
            try:
                exec(code, self.tb_frame.f_globals, {})
            except:
                tb = sys.exc_info()[2].tb_next
                tb_set_next(tb, self.tb_next and self.tb_next.as_traceback())
                return tb
        else:
            raise RuntimeError("Cannot re-create traceback !")

    # noinspection SpellCheckingInspection
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
            'co_filename': self.tb_frame.f_code.co_filename,
            'co_name': self.tb_frame.f_code.co_name,
        }
        frame = {
            'f_globals': self.tb_frame.f_globals,
            'f_code': code,
        }
        return {
            'tb_frame': frame,
            'tb_lineno': self.tb_lineno,
            'tb_next': tb_next,
        }

    @classmethod
    def from_dict(cls, dct):
        if dct['tb_next']:
            tb_next = cls.from_dict(dct['tb_next'])
        else:
            tb_next = None

        code = _AttrDict(
            co_filename=dct['tb_frame']['f_code']['co_filename'],
            co_name=dct['tb_frame']['f_code']['co_name'],
        )
        frame = _AttrDict(
            f_globals=dct['tb_frame']['f_globals'],
            f_code=code,
        )
        tb = _AttrDict(
            tb_frame=frame,
            tb_lineno=dct['tb_lineno'],
            tb_next=tb_next,
        )
        return cls(tb)

    @classmethod
    def from_string(cls, string, strict=True):
        frames = []
        header = strict

        for line in string.splitlines():
            line = line.rstrip()
            if header:
                if line == 'Traceback (most recent call last):':
                    header = False
                continue
            frame_match = FRAME_RE.match(line)
            if frame_match:
                frames.append(frame_match.groupdict())
            elif line.startswith('  '):
                pass
            elif strict:
                break  # traceback ended

        if frames:
            previous = None
            for frame in reversed(frames):
                previous = _AttrDict(
                    frame,
                    tb_frame=_AttrDict(
                        frame,
                        f_globals=_AttrDict(
                            __file__=frame['co_filename'],
                            __name__='?',
                        ),
                        f_code=_AttrDict(frame),
                    ),
                    tb_next=previous,
                )
            return cls(previous)
        else:
            raise TracebackParseError("Could not find any frames in %r." % string)
