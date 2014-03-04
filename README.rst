==========================
        python-tblib
==========================

.. image:: https://secure.travis-ci.org/ionelmc/python-tblib.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/ionelmc/python-tblib

.. image:: https://coveralls.io/repos/ionelmc/python-tblib/badge.png?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-tblib

.. image:: https://badge.fury.io/py/tblib.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/tblib

Traceback fiddling library. For now allows you to pickle tracebacks and raise exceptions with pickled tracebacks in different processes.
This allows better error handling when running code over multiple processes (imagine multiprocessing, billiard, futures, celery etc).

Requirements
============

:OS: Any
:Runtime: Python 2.6, 2.7, 3.2, 3.3, 3.4 and PyPy.

Pickling tracebacks
===================

**Note**: The traceback objects that come out are stripped of some attributes (like variables). But you'll be able to raise exceptions with
those tracebacks or print them - that should cover 99% of the usecases.

::

    >>> from tblib import pickling_support
    >>> pickling_support.install()
    >>> import pickle, sys
    >>> def inner_0():
    ...     raise Exception('fail')
    ...
    >>> def inner_1():
    ...     inner_0()
    ...
    >>> def inner_2():
    ...     inner_1()
    ...
    >>> try:
    ...     inner_2()
    ... except:
    ...     s1 = pickle.dumps(sys.exc_info())
    ...
    >>> len(s1) > 1
    True
    >>> try:
    ...     inner_2()
    ... except:
    ...     s2 = pickle.dumps(sys.exc_info(), protocol=pickle.HIGHEST_PROTOCOL)
    ...
    >>> len(s2) > 1
    True

    >>> try:
    ...     import cPickle
    ... except ImportError:
    ...     import pickle as cPickle
    >>> try:
    ...     inner_2()
    ... except:
    ...     s3 = cPickle.dumps(sys.exc_info(), protocol=pickle.HIGHEST_PROTOCOL)
    ...
    >>> len(s3) > 1
    True

Unpickling
----------

::

    >>> pickle.loads(s1)
    (<...Exception'>, Exception('fail',), <traceback object at ...>)

    >>> pickle.loads(s2)
    (<...Exception'>, Exception('fail',), <traceback object at ...>)

    >>> pickle.loads(s3)
    (<...Exception'>, Exception('fail',), <traceback object at ...>)

Raising
-------

::

    >>> from six import reraise
    >>> reraise(*pickle.loads(s1))
    Traceback (most recent call last):
      ...
      File "<doctest README.rst[14]>", line 1, in <module>
        reraise(*pickle.loads(s2))
      File "<doctest README.rst[8]>", line 2, in <module>
        inner_2()
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail
    >>> reraise(*pickle.loads(s2))
    Traceback (most recent call last):
      ...
      File "<doctest README.rst[14]>", line 1, in <module>
        reraise(*pickle.loads(s2))
      File "<doctest README.rst[8]>", line 2, in <module>
        inner_2()
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail
    >>> reraise(*pickle.loads(s3))
    Traceback (most recent call last):
      ...
      File "<doctest README.rst[14]>", line 1, in <module>
        reraise(*pickle.loads(s2))
      File "<doctest README.rst[8]>", line 2, in <module>
        inner_2()
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail

What if we have a local stack, does it show correctly ?
```````````````````````````````````````````````````````

Yes it does::

    >>> exc_info = pickle.loads(s3)
    >>> def local_0():
    ...     reraise(*exc_info)
    ...
    >>> def local_1():
    ...     local_0()
    ...
    >>> def local_2():
    ...     local_1()
    ...
    >>> local_2()
    Traceback (most recent call last):
      File "...doctest.py", line ..., in __run
        compileflags, 1) in test.globs
      File "<doctest README.rst[24]>", line 1, in <module>
        local_2()
      File "<doctest README.rst[23]>", line 2, in local_2
        local_1()
      File "<doctest README.rst[22]>", line 2, in local_1
        local_0()
      File "<doctest README.rst[21]>", line 2, in local_0
        reraise(*exc_info)
      File "<doctest README.rst[11]>", line 2, in <module>
        inner_2()
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail



The tblib.Traceback object
==========================

It is used by the ``pickling_support``. You can use it too if you want more flexibility::

    >>> from tblib import Traceback
    >>> try:
    ...     inner_2()
    ... except:
    ...     et, ev, tb = sys.exc_info()
    ...     tb = Traceback(tb)
    ...     reraise(et, ev, tb.as_traceback())
    ...
    Traceback (most recent call last):
      ...
      File "<doctest README.rst[21]>", line 6, in <module>
        reraise(et, ev, tb.as_traceback())
      File "<doctest README.rst[21]>", line 2, in <module>
        inner_2()
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail

Decorators
==========

return_error
------------

::

    >>> from tblib.decorators import return_error
    >>> inner_2r = return_error(inner_2)
    >>> e = inner_2r()
    >>> e
    <tblib.decorators.Error object at ...>
    >>> e.reraise()
    Traceback (most recent call last):
      ...
      File "<doctest README.rst[26]>", line 1, in <module>
        e.reraise()
      File "...tblib...decorators.py", line 19, in reraise
        reraise(self.exc_type, self.exc_value, self.traceback)
      File "...tblib...decorators.py", line 25, in return_exceptions_wrapper
        return func(*args, **kwargs)
      File "<doctest README.rst[5]>", line 2, in inner_2
        inner_1()
      File "<doctest README.rst[4]>", line 2, in inner_1
        inner_0()
      File "<doctest README.rst[3]>", line 2, in inner_0
        raise Exception('fail')
    Exception: fail

How's this useful ? Imagine you're using multiprocessing like this::

    >>> import traceback
    >>> from multiprocessing import Pool
    >>> import multiprocessing.pool
    >>> from examples import func_a
    >>> # Undo the fix for http://bugs.python.org/issue13831 so that we can
    >>> # see the effects of our change.
    >>> multiprocessing.pool.ExceptionWithTraceback = lambda e, t: e
    >>> pool = Pool()
    >>> try:
    ...     for i in pool.map(func_a, range(5)):
    ...         print(i)
    ... except:
    ...     print(traceback.format_exc())
    ...
    Traceback (most recent call last):
      File "<doctest README.rst[38]>", line 2, in <module>
        for i in pool.map(func_a, range(5)):
      File "...multiprocessing...pool.py", line ..., in map
        ...
      File "...multiprocessing...pool.py", line ..., in get
        ...
    Exception: Guessing time !
    <BLANKLINE>
    >>> pool.terminate()

Not very useful is it? Let's sort this out::

    >>> from tblib.decorators import apply_with_return_error, Error
    >>> from itertools import repeat
    >>> pool = Pool()
    >>> try:
    ...     for i in pool.map(apply_with_return_error, zip(repeat(func_a), range(5))):
    ...         if isinstance(i, Error):
    ...             i.reraise()
    ...         else:
    ...             print(i)
    ... except:
    ...     print(traceback.format_exc())
    ...
    Traceback (most recent call last):
      File "<doctest README.rst[43]>", line 4, in <module>
        i.reraise()
      File "...tblib...decorators.py", line ..., in reraise
        reraise(self.exc_type, self.exc_value, self.traceback)
      File "...tblib...decorators.py", line ..., in return_exceptions_wrapper
        return func(*args, **kwargs)
      File "...tblib...decorators.py", line ..., in apply_with_return_error
        return args[0](*args[1:])
      File "...examples.py", line 2, in func_a
        func_b()
      File "...examples.py", line 5, in func_b
        func_c()
      File "...examples.py", line 8, in func_c
        func_d()
      File "...examples.py", line 11, in func_d
        raise Exception("Guessing time !")
    Exception: Guessing time !
    <BLANKLINE>
    >>> pool.terminate()

Much better !

What if we have a local call stack ?
````````````````````````````````````

::

    >>> def local_0():
    ...     pool = Pool()
    ...     for i in pool.map(apply_with_return_error, zip(repeat(func_a), range(5))):
    ...         if isinstance(i, Error):
    ...             i.reraise()
    ...         else:
    ...             print(i)
    ...
    >>> def local_1():
    ...     local_0()
    ...
    >>> def local_2():
    ...     local_1()
    ...
    >>> try:
    ...     local_2()
    ... except:
    ...     print(traceback.format_exc())
    Traceback (most recent call last):
      File "<doctest README.rst[48]>", line 2, in <module>
        local_2()
      File "<doctest README.rst[47]>", line 2, in local_2
        local_1()
      File "<doctest README.rst[46]>", line 2, in local_1
        local_0()
      File "<doctest README.rst[45]>", line 5, in local_0
        i.reraise()
      File "...tblib...decorators.py", line 19, in reraise
        reraise(self.exc_type, self.exc_value, self.traceback)
      File "...tblib...decorators.py", line 25, in return_exceptions_wrapper
        return func(*args, **kwargs)
      File "...tblib...decorators.py", line 42, in apply_with_return_error
        return args[0](*args[1:])
      File "...tests...examples.py", line 2, in func_a
        func_b()
      File "...tests...examples.py", line 5, in func_b
        func_c()
      File "...tests...examples.py", line 8, in func_c
        func_d()
      File "...tests...examples.py", line 11, in func_d
        raise Exception("Guessing time !")
    Exception: Guessing time !
    <BLANKLINE>


Credits
=======

* `mitsuhiko/jinja2 <https://github.com/mitsuhiko/jinja2>`_ for figuring a way to create traceback objects.

