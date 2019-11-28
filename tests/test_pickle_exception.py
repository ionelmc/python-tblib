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


def setup_function():
    copyreg.dispatch_table.clear()


def teardown_function():
    copyreg.dispatch_table.clear()


class CustomError(Exception):
    pass


@pytest.mark.parametrize(
    "protocol", [None] + list(range(1, pickle.HIGHEST_PROTOCOL + 1))
)
@pytest.mark.parametrize("global_install", [False, True])
def test_pickle_exceptions(global_install, protocol):
    if global_install:
        tblib.pickling_support.install()

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

    if not global_install:
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
