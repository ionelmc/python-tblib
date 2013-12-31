import sys
from functools import wraps

from six import reraise

from . import Traceback

class Error(object):
    def __init__(self, exc_type, exc_value, traceback):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.__traceback = Traceback(traceback)

    @property
    def traceback(self):
        return self.__traceback.as_traceback()

    def reraise(self):
        reraise(self.exc_type, self.exc_value, self.traceback)

def return_errors(func, exc_type=Exception):
    @wraps(func)
    def return_exceptions_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exc_type as exc:
            return Error(*sys.exc_info())
    return return_exceptions_wrapper
