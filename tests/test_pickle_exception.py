import os
from traceback import format_exception

try:
    import copyreg
except ImportError:
    # Python 2
    import copy_reg as copyreg

import pickle
import sys

import pytest

import tblib.pickling_support

has_python311 = sys.version_info >= (3, 11)


@pytest.fixture
def clear_dispatch_table():
    bak = copyreg.dispatch_table.copy()
    copyreg.dispatch_table.clear()
    yield None
    copyreg.dispatch_table.clear()
    copyreg.dispatch_table.update(bak)


class CustomError(Exception):
    pass


def strip_locations(tb_text):
    return tb_text.replace('    ~~^~~\n', '').replace('    ^^^^^^^^^^^^^^^^^\n', '')


@pytest.mark.parametrize('protocol', [None, *list(range(1, pickle.HIGHEST_PROTOCOL + 1))])
@pytest.mark.parametrize('how', ['global', 'instance', 'class'])
def test_install(clear_dispatch_table, how, protocol):
    if how == 'global':
        tblib.pickling_support.install()
    elif how == 'class':
        tblib.pickling_support.install(CustomError, ValueError, ZeroDivisionError)

    try:
        try:
            try:
                1 / 0  # noqa: B018
            finally:
                # The ValueError's __context__ will be the ZeroDivisionError
                raise ValueError('blah')
        except Exception as e:
            # Python 3 only syntax
            # raise CustomError("foo") from e
            new_e = CustomError('foo')
            new_e.__cause__ = e
            if has_python311:
                new_e.add_note('note 1')
                new_e.add_note('note 2')
            raise new_e from e
    except Exception as e:
        exc = e
    else:
        raise AssertionError

    expected_format_exception = strip_locations(''.join(format_exception(type(exc), exc, exc.__traceback__)))

    # Populate Exception.__dict__, which is used in some cases
    exc.x = 1
    exc.__cause__.x = 2
    exc.__cause__.__context__.x = 3

    if how == 'instance':
        tblib.pickling_support.install(exc)
    if protocol:
        exc = pickle.loads(pickle.dumps(exc, protocol=protocol))

    assert isinstance(exc, CustomError)
    assert exc.args == ('foo',)
    assert exc.x == 1
    assert exc.__traceback__ is not None

    assert isinstance(exc.__cause__, ValueError)
    assert exc.__cause__.__traceback__ is not None
    assert exc.__cause__.x == 2
    assert exc.__cause__.__cause__ is None

    assert isinstance(exc.__cause__.__context__, ZeroDivisionError)
    assert exc.__cause__.__context__.x == 3
    assert exc.__cause__.__context__.__cause__ is None
    assert exc.__cause__.__context__.__context__ is None

    if has_python311:
        assert exc.__notes__ == ['note 1', 'note 2']

    assert expected_format_exception == strip_locations(''.join(format_exception(type(exc), exc, exc.__traceback__)))


@tblib.pickling_support.install
class RegisteredError(Exception):
    pass


def test_install_decorator():
    with pytest.raises(RegisteredError) as ewrap:
        raise RegisteredError('foo')
    exc = ewrap.value
    exc.x = 1
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, RegisteredError)
    assert exc.args == ('foo',)
    assert exc.x == 1
    assert exc.__traceback__ is not None


@pytest.mark.skipif(not has_python311, reason='no BaseExceptionGroup before Python 3.11')
def test_install_instance_recursively(clear_dispatch_table):
    exc = BaseExceptionGroup('test', [ValueError('foo'), CustomError('bar')])  # noqa: F821
    exc.exceptions[0].__cause__ = ZeroDivisionError('baz')
    exc.exceptions[0].__cause__.__context__ = AttributeError('quux')

    tblib.pickling_support.install(exc)

    installed = {c for c in copyreg.dispatch_table if issubclass(c, BaseException)}
    assert installed == {ExceptionGroup, ValueError, CustomError, ZeroDivisionError, AttributeError}  # noqa: F821


def test_install_typeerror():
    with pytest.raises(TypeError):
        tblib.pickling_support.install('foo')


@pytest.mark.parametrize('protocol', [None, *list(range(1, pickle.HIGHEST_PROTOCOL + 1))])
@pytest.mark.parametrize('how', ['global', 'instance', 'class'])
def test_get_locals(clear_dispatch_table, how, protocol):
    def get_locals(frame):
        if 'my_variable' in frame.f_locals:
            return {'my_variable': int(frame.f_locals['my_variable'])}
        else:
            return {}

    if how == 'global':
        tblib.pickling_support.install(get_locals=get_locals)
    elif how == 'class':
        tblib.pickling_support.install(CustomError, ValueError, ZeroDivisionError, get_locals=get_locals)

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

    if how == 'instance':
        tblib.pickling_support.install(exc, get_locals=get_locals)

    exc = pickle.loads(pickle.dumps(exc, protocol=protocol))
    assert exc.__traceback__.tb_next.tb_frame.f_locals == {'my_variable': 1}


class CustomWithAttributesException(Exception):
    def __init__(self, message, arg1, arg2, arg3):
        super().__init__(message)
        self.values12 = (arg1, arg2)
        self.value3 = arg3


def test_custom_with_attributes():
    try:
        raise CustomWithAttributesException('bar', 1, 2, 3)
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, CustomWithAttributesException)
    assert exc.args == ('bar',)
    assert exc.values12 == (1, 2)
    assert exc.value3 == 3
    assert exc.__traceback__ is not None


class CustomOSError(OSError):
    def __init__(self, message, errno, strerror: str, filename, none: None, filename2):
        super().__init__(errno, strerror, filename, none, filename2)
        self.message = message


def test_custom_oserror():
    try:
        raise CustomOSError('bar', 2, 'err', 3, None, 5)
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, CustomOSError)
    assert exc.message == 'bar'
    assert exc.errno == 2
    assert exc.strerror == 'err'
    assert exc.filename == 3
    assert exc.filename2 == 5
    assert exc.__traceback__ is not None


def test_oserror():
    try:
        raise OSError(2, 'err', 3, None, 5)
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, OSError)
    assert exc.errno == 2
    assert exc.strerror == 'err'
    assert exc.filename == 3
    assert exc.filename2 == 5
    assert exc.__traceback__ is not None


class OpenError(Exception):
    pass


def bad_open():
    try:
        raise PermissionError(13, 'Booboo', 'filename', None, None)
    except Exception as e:
        raise OpenError(e) from e


def test_permissionerror():
    try:
        bad_open()
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, OpenError)
    assert exc.__traceback__ is not None
    assert repr(exc) == "OpenError(PermissionError(13, 'Booboo'))"
    assert str(exc) == "[Errno 13] Booboo: 'filename'"
    assert exc.args[0].errno == 13
    assert exc.args[0].strerror == 'Booboo'
    assert exc.args[0].filename == 'filename'


class BadError(Exception):
    def __init__(self):
        super().__init__('Bad Bad Bad!')


def test_baderror():
    try:
        raise BadError
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, BadError)
    assert exc.args == ('Bad Bad Bad!',)
    assert exc.__traceback__ is not None


class BadError2(Exception):
    def __init__(self, stuff):
        super().__init__()
        self.stuff = stuff


def test_baderror2():
    try:
        raise BadError2('123')
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, BadError2)
    assert exc.args == ()
    assert exc.stuff == '123'
    assert exc.__traceback__ is not None


class CustomReduceException(Exception):
    def __init__(self, message, arg1, arg2, arg3):
        super().__init__(message)
        self.values12 = (arg1, arg2)
        self.value3 = arg3

    def __reduce__(self):
        return self.__class__, self.args + self.values12 + (self.value3,)


def test_custom_reduce():
    try:
        raise CustomReduceException('foo', 1, 2, 3)
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, CustomReduceException)
    assert exc.args == ('foo',)
    assert exc.values12 == (1, 2)
    assert exc.value3 == 3
    assert exc.__traceback__ is not None


class CustomReduceExException(Exception):
    def __init__(self, message, arg1, arg2, protocol):
        super().__init__(message)
        self.values12 = (arg1, arg2)
        self.value3 = protocol

    def __reduce_ex__(self, protocol):
        return self.__class__, self.args + self.values12 + (self.value3,)


@pytest.mark.parametrize('protocol', [None, *list(range(1, pickle.HIGHEST_PROTOCOL + 1))])
def test_custom_reduce_ex(protocol):
    try:
        raise CustomReduceExException('foo', 1, 2, 3)
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc, protocol=protocol))

    assert isinstance(exc, CustomReduceExException)
    assert exc.args == ('foo',)
    assert exc.values12 == (1, 2)
    assert exc.value3 == 3
    assert exc.__traceback__ is not None


def test_oserror_simple():
    try:
        raise OSError(13, 'Permission denied')
    except Exception as e:
        exc = e

    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, OSError)
    assert exc.args == (13, 'Permission denied')
    assert exc.errno == 13
    assert exc.strerror == 'Permission denied'
    assert exc.__traceback__ is not None


def test_real_oserror():
    try:
        os.open('non-existing-file', os.O_RDONLY)
    except Exception as e:
        exc = e
    else:
        pytest.fail('os.open should have raised an OSError')

    str_output = str(exc)
    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, OSError)
    assert exc.errno == 2
    assert str_output == str(exc)


def test_timeouterror():
    try:
        raise TimeoutError('stuff')
    except Exception as e:
        exc = e
    else:
        pytest.fail('os.open should have raised an TimeoutError')

    str_output = str(exc)
    tblib.pickling_support.install(exc)
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, TimeoutError)
    assert exc.errno is None
    assert str_output == str(exc)


@pytest.mark.skipif(not has_python311, reason='ExceptionGroup needs Python 3.11')
def test_exception_group():
    errors = []
    try:
        e = CustomWithAttributesException('bar', 1, 2, 3)
        e.add_note('test_custom_with_attributes')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        e = CustomOSError('bar', 2, 'err', 3, None, 5)
        e.add_note('test_custom_oserror')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        e = OSError(2, 'err', 3, None, 5)
        e.add_note('test_oserror')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        bad_open()
    except Exception as e:
        e.add_note('test_permissionerror')
        errors.append(e)

    try:
        raise BadError
    except Exception as e:
        e.add_note('test_baderror')
        errors.append(e)

    try:
        e = BadError2('123')
        e.add_note('test_baderror2')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        e = CustomReduceException('foo', 1, 2, 3)
        e.add_note('test_custom_reduce')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        e = OSError(13, 'Permission denied')
        e.add_note('test_oserror_simple')
        raise e
    except Exception as e:
        errors.append(e)

    try:
        os.open('non-existing-file', os.O_RDONLY)
    except Exception as e:
        e.add_note('test_real_oserror')
        real_oserror_str = str(e)
        errors.append(e)
    else:
        pytest.fail('os.open should have raised an OSError')

    try:
        raise ExceptionGroup('group error', errors)  # noqa: F821
    except Exception as e:
        exc = e

    assert len(exc.exceptions) == 9  # before pickling

    tblib.pickling_support.install()
    exc = pickle.loads(pickle.dumps(exc))

    assert len(exc.exceptions) == 9  # after unpickling

    assert exc.exceptions[0].__notes__ == ['test_custom_with_attributes']
    assert isinstance(exc.exceptions[0], CustomWithAttributesException)
    assert exc.exceptions[0].args == ('bar',)
    assert exc.exceptions[0].values12 == (1, 2)
    assert exc.exceptions[0].value3 == 3
    assert exc.exceptions[0].__traceback__ is not None

    assert exc.exceptions[1].__notes__ == ['test_custom_oserror']
    assert isinstance(exc.exceptions[1], CustomOSError)
    assert exc.exceptions[1].message == 'bar'
    assert exc.exceptions[1].errno == 2
    assert exc.exceptions[1].strerror == 'err'
    assert exc.exceptions[1].filename == 3
    assert exc.exceptions[1].filename2 == 5
    assert exc.exceptions[1].__traceback__ is not None

    assert exc.exceptions[2].__notes__ == ['test_oserror']
    assert isinstance(exc.exceptions[2], OSError)
    assert exc.exceptions[2].errno == 2
    assert exc.exceptions[2].strerror == 'err'
    assert exc.exceptions[2].filename == 3
    assert exc.exceptions[2].filename2 == 5
    assert exc.exceptions[2].__traceback__ is not None

    assert exc.exceptions[3].__notes__ == ['test_permissionerror']
    assert isinstance(exc.exceptions[3], OpenError)
    assert exc.exceptions[3].__traceback__ is not None
    assert repr(exc.exceptions[3]) == "OpenError(PermissionError(13, 'Booboo'))"
    assert str(exc.exceptions[3]) == "[Errno 13] Booboo: 'filename'"
    assert exc.exceptions[3].args[0].errno == 13
    assert exc.exceptions[3].args[0].strerror == 'Booboo'
    assert exc.exceptions[3].args[0].filename == 'filename'

    assert exc.exceptions[4].__notes__ == ['test_baderror']
    assert isinstance(exc.exceptions[4], BadError)
    assert exc.exceptions[4].args == ('Bad Bad Bad!',)
    assert exc.exceptions[4].__traceback__ is not None

    assert exc.exceptions[5].__notes__ == ['test_baderror2']
    assert isinstance(exc.exceptions[5], BadError2)
    assert exc.exceptions[5].args == ()
    assert exc.exceptions[5].stuff == '123'
    assert exc.exceptions[5].__traceback__ is not None

    assert exc.exceptions[6].__notes__ == ['test_custom_reduce']
    assert isinstance(exc.exceptions[6], CustomReduceException)
    assert exc.exceptions[6].args == ('foo',)
    assert exc.exceptions[6].values12 == (1, 2)
    assert exc.exceptions[6].value3 == 3
    assert exc.exceptions[6].__traceback__ is not None

    assert exc.exceptions[7].__notes__ == ['test_oserror_simple']
    assert isinstance(exc.exceptions[7], OSError)
    assert exc.exceptions[7].args == (13, 'Permission denied')
    assert exc.exceptions[7].errno == 13
    assert exc.exceptions[7].strerror == 'Permission denied'
    assert exc.exceptions[7].__traceback__ is not None

    assert exc.exceptions[8].__notes__ == ['test_real_oserror']
    assert isinstance(exc.exceptions[8], OSError)
    assert exc.exceptions[8].errno == 2
    assert str(exc.exceptions[8]) == real_oserror_str
