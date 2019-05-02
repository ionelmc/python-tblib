def test_30():
    from tblib import pickling_support
    pickling_support.install()

    import six, pickle, sys
    from twisted.python.failure import Failure

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
