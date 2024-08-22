import pickle

from tblib import pickling_support


class HTTPrettyError(Exception):
    pass


class UnmockedError(HTTPrettyError):
    def __init__(self):
        super().__init__('No mocking was registered, and real connections are not allowed (httpretty.allow_net_connect = False).')


def test_65():
    pickling_support.install()

    try:
        raise UnmockedError
    except Exception as e:
        exc = e

    exc = pickle.loads(pickle.dumps(exc))

    assert isinstance(exc, UnmockedError)
    assert exc.args == ('No mocking was registered, and real connections are not allowed (httpretty.allow_net_connect = False).',)
    assert exc.__traceback__ is not None
