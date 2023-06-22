import pickle
import sys

import pytest
import six

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
        six.reraise(*pickle.loads(s))
    except ValueError:
        f = Failure()

    assert f is not None
