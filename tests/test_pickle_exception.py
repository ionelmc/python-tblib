try:
    import copyreg
except ImportError:
    # Python 2
    import copy_reg as copyreg

import pickle
import sys

import pytest

import tblib.pickling_support

has_python3 = sys.version_info.major >= 3


@pytest.fixture
def clear_dispatch_table():
    bak = copyreg.dispatch_table.copy()
    copyreg.dispatch_table.clear()
    yield
    copyreg.dispatch_table.clear()
    copyreg.dispatch_table.update(bak)


class CustomError(Exception):
    pass


@pytest.mark.parametrize("protocol", [None] + list(range(1, pickle.HIGHEST_PROTOCOL + 1)))
@pytest.mark.parametrize("how", ["global", "instance", "class"])
def test_install(clear_dispatch_table, how, protocol):
    if how == "global":
        tblib.pickling_support.install()
    elif how == "class":
        tblib.pickling_support.install(CustomError, ZeroDivisionError)

    try:
        try:
            1 / 0
        except Exception as e:
            # Python 3 only syntax
            # raise CustomError("foo") from e
            new_e = CustomError("foo")
            if has_python3:
                new_e.__cause__ = e
            raise new_e
    except Exception as e:
        exc = e
    else:
        assert False

    # Populate Exception.__dict__, which is used in some cases
    exc.x = 1
    if has_python3:
        exc.__cause__.x = 2

    if how == "instance":
        tblib.pickling_support.install(exc)
    if protocol:
        exc = pickle.loads(pickle.dumps(exc, protocol=protocol))

    assert isinstance(exc, CustomError)
    assert exc.args == ("foo",)
    assert exc.x == 1
    if has_python3:
        assert exc.__traceback__ is not None
        assert isinstance(exc.__cause__, ZeroDivisionError)
        assert exc.__cause__.__traceback__ is not None
        assert exc.__cause__.x == 2
        assert exc.__cause__.__cause__ is None


@tblib.pickling_support.install
class RegisteredError(Exception):
    pass


def test_install_decorator():
    with pytest.raises(RegisteredError) as ewrap:
        raise RegisteredError("foo")
    exc = ewrap.value
    exc.x = 1
    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, RegisteredError)
    assert exc.args == ("foo",)
    assert exc.x == 1
    if has_python3:
        assert exc.__traceback__ is not None


@pytest.mark.skipif(sys.version_info[0] < 3, reason="No checks done in Python 2")
def test_install_typeerror():
    with pytest.raises(TypeError):
        tblib.pickling_support.install("foo")
