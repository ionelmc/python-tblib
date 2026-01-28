import itertools
import re
import sys

__version__ = '3.2.2'
__all__ = 'Code', 'Frame', 'Traceback', 'TracebackParseError'

FRAME_RE = re.compile(r'^\s*File "(?P<co_filename>.+)", line (?P<tb_lineno>\d+)(, in (?P<co_name>.+))?$')

# PyPy uses a different linetable format than CPython, so we can't use custom
# linetables for column position info on PyPy
_is_pypy = sys.implementation.name == 'pypy'


def _get_code_position(code, instruction_index):
    """
    Get position information (line, end_line, col, end_col) for a bytecode instruction.
    Returns (None, None, None, None) if position info is not available.
    """
    if not hasattr(code, 'co_positions'):
        return (None, None, None, None)
    if instruction_index < 0:
        return (None, None, None, None)
    positions_gen = code.co_positions()
    return next(itertools.islice(positions_gen, instruction_index // 2, None), (None, None, None, None))


def _make_linetable_with_positions(colno, end_colno):
    """
    Create a co_linetable bytes object for the 'raise __traceback_maker' stub
    with the specified column positions.

    The stub code has 3 instructions:
    - Instruction 0: RESUME (no location)
    - Instruction 1: LOAD_NAME __traceback_maker
    - Instruction 2: RAISE_VARARGS (this is where the exception occurs)

    We need to set the column positions for instruction 2 (the RAISE instruction).
    """
    # The linetable format for Python 3.11+:
    # Each entry starts with a byte: (code << 3) | (instruction_count - 1)
    # Code 10 (0xa) = ONE_LINE0: same line, followed by col and end_col bytes
    # Code 11 (0xb) = ONE_LINE1: line+1, followed by col and end_col bytes
    # Code 14 (0xe) = LONG: complex variable-length format
    # Code 15 (0xf) = NONE: no location info

    if colno is None:
        colno = 0
    if end_colno is None:
        end_colno = 0

    # Clamp values to valid range (0-255 for simple encoding)
    colno = max(0, min(255, colno))
    end_colno = max(0, min(255, end_colno))

    # Build the linetable:
    # Entry 0: LONG format for instruction 0 (RESUME at line 0->1)
    #   0xf0 = (14 << 3) | 0 = LONG, 1 instruction
    #   followed by: line_delta=1 (as signed varint), end_line_delta=0, col+1=1, end_col+1=1
    # Entry 1: ONE_LINE1 for instruction 1 (LOAD_NAME, same line)
    #   0xd8 = (11 << 3) | 0 = ONE_LINE1, 1 instruction
    #   We keep original columns for LOAD_NAME (not critical)
    # Entry 2: ONE_LINE0 for instruction 2 (RAISE_VARARGS)
    #   0xd0 = (10 << 3) | 0 = ONE_LINE0, 1 instruction
    #   followed by: col, end_col

    linetable = bytes(
        [
            0xF0,
            0x03,
            0x01,
            0x01,
            0x01,  # Entry 0: LONG format (original header)
            0xD8,
            0x06,
            0x17,  # Entry 1: ONE_LINE1, col=6, end_col=23 (for LOAD_NAME)
            0xD0,
            colno,
            end_colno,  # Entry 2: ONE_LINE0, col=colno, end_col=end_colno
        ]
    )
    return linetable


def _make_pypy_linetable_with_positions(colno, end_colno, lineno):
    """
    Create a co_linetable for PyPy with the specified column positions.

    PyPy uses a different linetable format than CPython:
    - Each instruction gets a variable-length entry
    - Format: varint(lineno_delta) + optional(col_offset+1, end_col_offset+1, end_line_delta)
    - lineno_delta is relative to co_firstlineno, encoded as (lineno - firstlineno + 1)
    - Column offsets are stored +1 to distinguish from "no info" (single 0 byte)

    The stub 'raise __traceback_maker' has 2 instructions on PyPy:
    - Instruction 0: LOAD_NAME __traceback_maker (col 6-23)
    - Instruction 1: RAISE_VARARGS (col from colno-end_colno)
    """
    if colno is None:
        colno = 0
    if end_colno is None:
        end_colno = 0

    # Clamp to valid range (0-254 since we store +1)
    colno = max(0, min(254, colno))
    end_colno = max(0, min(254, end_colno))

    firstlineno = lineno
    lineno_delta = lineno - firstlineno + 1
    end_line_delta = 0

    # Encode as varint (lineno_delta=1 fits in 1 byte: 0x01)
    # For small values (<128), varint is just the value itself
    lineno_varint = bytes([lineno_delta])

    # Entry for instruction 0 (LOAD_NAME): original position (col 6-23)
    entry0 = lineno_varint + bytes([7, 24, 0])  # col_offset=6 (+1=7), end_col_offset=23 (+1=24), end_line_delta=0

    # Entry for instruction 1 (RAISE_VARARGS): our custom position
    entry1 = lineno_varint + bytes([colno + 1, end_colno + 1, end_line_delta])

    return entry0 + entry1


class _AttrDict(dict):
    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None


# noinspection PyPep8Naming
class __traceback_maker(Exception):
    pass


# Alias without leading underscores to avoid name mangling when used inside class methods
_tb_maker = __traceback_maker


class TracebackParseError(Exception):
    pass


class Code:
    """
    Class that replicates just enough of the builtin Code object to enable serialization and traceback rendering.
    """

    co_code = None

    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name
        self.co_argcount = 0
        self.co_kwonlyargcount = 0
        self.co_varnames = ()
        self.co_nlocals = 0
        self.co_stacksize = 0
        self.co_flags = 64
        self.co_firstlineno = 0


class Frame:
    """
    Class that replicates just enough of the builtin Frame object to enable serialization and traceback rendering.

    Args:

        get_locals (callable): A function that take a frame argument and returns a dict.

            See :class:`Traceback` class for example.
    """

    def __init__(self, frame, *, get_locals=None):
        self.f_locals = {} if get_locals is None else get_locals(frame)
        self.f_globals = {k: v for k, v in frame.f_globals.items() if k in ('__file__', '__name__')}
        self.f_code = Code(frame.f_code)
        self.f_lineno = frame.f_lineno

    def clear(self):
        """
        For compatibility with PyPy 3.5;
        clear() was added to frame in Python 3.4
        and is called by traceback.clear_frames(), which
        in turn is called by unittest.TestCase.assertRaises
        """


class Traceback:
    """
    Class that wraps builtin Traceback objects.

    Args:
        get_locals (callable): A function that take a frame argument and returns a dict.

            Ideally you will only return exactly what you need, and only with simple types that can be json serializable.

            Example:

            .. code:: python

                def get_locals(frame):
                    if frame.f_locals.get("__tracebackhide__"):
                        return {"__tracebackhide__": True}
                    else:
                        return {}
    """

    tb_next = None

    def __init__(self, tb, *, get_locals=None):
        self.tb_frame = Frame(tb.tb_frame, get_locals=get_locals)
        self.tb_lineno = int(tb.tb_lineno)

        # Capture column position information if available (Python 3.11+ on CPython)
        # This is used to reconstruct the caret position in tracebacks
        if hasattr(tb, 'tb_colno') and tb.tb_colno is not None:
            # Input already has column info (e.g., from from_dict)
            self.tb_colno = tb.tb_colno
            self.tb_end_colno = getattr(tb, 'tb_end_colno', None)
            self.tb_end_lineno = getattr(tb, 'tb_end_lineno', None)
        else:
            # Try to extract from the code object
            tb_lasti = getattr(tb, 'tb_lasti', -1)
            if tb_lasti >= 0 and hasattr(tb, 'tb_frame') and hasattr(tb.tb_frame, 'f_code'):
                _, end_lineno, colno, end_colno = _get_code_position(tb.tb_frame.f_code, tb_lasti)
                self.tb_end_lineno = end_lineno
                self.tb_colno = colno
                self.tb_end_colno = end_colno
            else:
                self.tb_end_lineno = None
                self.tb_colno = None
                self.tb_end_colno = None

        # Build in place to avoid exceeding the recursion limit
        tb = tb.tb_next
        prev_traceback = self
        cls = type(self)
        while tb is not None:
            traceback = object.__new__(cls)
            traceback.tb_frame = Frame(tb.tb_frame, get_locals=get_locals)
            traceback.tb_lineno = int(tb.tb_lineno)

            # Capture column position information for each frame
            if hasattr(tb, 'tb_colno') and tb.tb_colno is not None:
                traceback.tb_colno = tb.tb_colno
                traceback.tb_end_colno = getattr(tb, 'tb_end_colno', None)
                traceback.tb_end_lineno = getattr(tb, 'tb_end_lineno', None)
            else:
                tb_lasti = getattr(tb, 'tb_lasti', -1)
                if tb_lasti >= 0 and hasattr(tb, 'tb_frame') and hasattr(tb.tb_frame, 'f_code'):
                    _, end_lineno, colno, end_colno = _get_code_position(tb.tb_frame.f_code, tb_lasti)
                    traceback.tb_end_lineno = end_lineno
                    traceback.tb_colno = colno
                    traceback.tb_end_colno = end_colno
                else:
                    traceback.tb_end_lineno = None
                    traceback.tb_colno = None
                    traceback.tb_end_colno = None

            prev_traceback.tb_next = traceback
            prev_traceback = traceback
            tb = tb.tb_next

    def as_traceback(self):
        """
        Convert to a builtin Traceback object that is usable for raising or rendering a stacktrace.
        """
        current = self
        top_tb = None
        tb = None
        stub = compile(
            'raise __traceback_maker',
            '<string>',
            'exec',
        )
        while current:
            f_code = current.tb_frame.f_code

            # Build replace kwargs - include linetable with column positions if available
            replace_kwargs = {
                'co_firstlineno': current.tb_lineno,
                'co_argcount': 0,
                'co_filename': f_code.co_filename,
                'co_name': f_code.co_name,
                'co_freevars': (),
                'co_cellvars': (),
            }

            # If we have column position info, create a custom linetable
            # Both CPython 3.10+ and PyPy 3.10+ support co_linetable (but use different formats)
            if hasattr(stub, 'co_linetable'):
                colno = getattr(current, 'tb_colno', None)
                end_colno = getattr(current, 'tb_end_colno', None)
                if colno is not None or end_colno is not None:
                    if _is_pypy:
                        replace_kwargs['co_linetable'] = _make_pypy_linetable_with_positions(colno, end_colno, current.tb_lineno)
                    else:
                        replace_kwargs['co_linetable'] = _make_linetable_with_positions(colno, end_colno)

            code = stub.replace(**replace_kwargs)

            # noinspection PyBroadException
            try:
                # Must include __traceback_maker in globals so the LOAD_NAME succeeds
                # and the exception is raised by RAISE_VARARGS (at tb_lasti=4), not by
                # NameError from LOAD_NAME (at tb_lasti=2). This is important for
                # correct column position information.
                globals_dict = dict(current.tb_frame.f_globals)
                globals_dict['__traceback_maker'] = _tb_maker
                exec(code, globals_dict, dict(current.tb_frame.f_locals))  # noqa: S102
            except Exception:
                next_tb = sys.exc_info()[2].tb_next
                if top_tb is None:
                    top_tb = next_tb
                if tb is not None:
                    tb.tb_next = next_tb
                tb = next_tb
                del next_tb

            current = current.tb_next
        try:
            return top_tb
        finally:
            del top_tb
            del tb

    to_traceback = as_traceback

    def as_dict(self):
        """
        Converts to a dictionary representation. You can serialize the result to JSON as it only has
        builtin objects like dicts, lists, ints or strings.
        """
        if self.tb_next is None:
            tb_next = None
        else:
            tb_next = self.tb_next.as_dict()

        code = {
            'co_filename': self.tb_frame.f_code.co_filename,
            'co_name': self.tb_frame.f_code.co_name,
        }
        frame = {
            'f_globals': self.tb_frame.f_globals,
            'f_locals': self.tb_frame.f_locals,
            'f_code': code,
            'f_lineno': self.tb_frame.f_lineno,
        }
        result = {
            'tb_frame': frame,
            'tb_lineno': self.tb_lineno,
            'tb_next': tb_next,
        }
        # Include column position info if available (Python 3.11+)
        if getattr(self, 'tb_colno', None) is not None:
            result['tb_colno'] = self.tb_colno
        if getattr(self, 'tb_end_colno', None) is not None:
            result['tb_end_colno'] = self.tb_end_colno
        if getattr(self, 'tb_end_lineno', None) is not None:
            result['tb_end_lineno'] = self.tb_end_lineno
        return result

    to_dict = as_dict

    @classmethod
    def from_dict(cls, dct):
        """
        Creates an instance from a dictionary with the same structure as ``.as_dict()`` returns.
        """
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
            f_locals=dct['tb_frame'].get('f_locals', {}),
            f_code=code,
            f_lineno=dct['tb_frame']['f_lineno'],
        )
        tb = _AttrDict(
            tb_frame=frame,
            tb_lineno=dct['tb_lineno'],
            tb_next=tb_next,
            # Include column position info if present in the dict
            tb_colno=dct.get('tb_colno'),
            tb_end_colno=dct.get('tb_end_colno'),
            tb_end_lineno=dct.get('tb_end_lineno'),
        )
        instance = cls(tb, get_locals=get_all_locals)
        # Restore column position info from dict
        instance.tb_colno = dct.get('tb_colno')
        instance.tb_end_colno = dct.get('tb_end_colno')
        instance.tb_end_lineno = dct.get('tb_end_lineno')
        return instance

    @classmethod
    def from_string(cls, string, strict=True):
        """
        Creates an instance by parsing a stacktrace. Strict means that parsing stops when lines are not indented by at least two spaces
        anymore.
        """
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
                        f_locals={},
                        f_code=_AttrDict(frame),
                        f_lineno=int(frame['tb_lineno']),
                    ),
                    tb_next=previous,
                )
            return cls(previous)
        else:
            raise TracebackParseError(f'Could not find any frames in {string!r}.')


def get_all_locals(frame):
    return dict(frame.f_locals)
