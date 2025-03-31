import pickle
import sys

import pytest

from tblib import pickling_support

pytest.importorskip('twisted')


def test_30():
    from twisted.python.failure import Failure

    pickling_support.install()

    try:
        raise ValueError
    except ValueError:
        s = pickle.dumps(sys.exc_info())

    f = None
    try:
        etype, evalue, etb = pickle.loads(s)  # noqa: S301
        raise evalue.with_traceback(etb)
    except ValueError:
        f = Failure()

    assert f is not None
