
Changelog
=========

3.2.2 (2025-11-12)
~~~~~~~~~~~~~~~~~~

* Fixed regression occurring with ``TimeoutError`` exceptions. They should be represented now exactly as the original when unpickling.
  Contributed by Jacob Tomlinson in `#85 <https://github.com/ionelmc/python-tblib/pull/85>`_.

3.2.1 (2025-10-31)
~~~~~~~~~~~~~~~~~~

* Fixed regression occurring with ``ExceptionGroup`` exceptions. That exception type is now handled specifically in the new ``unpickle_exception_with_attrs`` function (just like ``OSError``).

3.2.0 (2025-10-21)
~~~~~~~~~~~~~~~~~~

* Changed ``tblib.pickling_support.install`` to support exceptions with ``__init__`` that does match the default
  ``BaseException.__reduce__`` (as it expects the positional arguments to ``__init__`` to match the ``args`` attribute).

  Special handling for OSError (and subclasses) is also included. The errno, strerror, winerror, filename and filename2 attributes will be added in the reduce structure (if set).

  This will support exception subclasses that do this without defining a custom ``__reduce__``:

  .. code-block:: python

    def __init__(self):
        super().__init__('mistery argument')

    def __init__(self, mistery_argument):
        super().__init__()
        self.mistery_argument = mistery_argument

  Tests and POC contributed by Oldřich Jedlička in `#73 <https://github.com/ionelmc/python-tblib/pull/73>`_.
* Fixed some doctest and coverage config. Contributed by Colin Watson in `#79 <https://github.com/ionelmc/python-tblib/pull/79>`_.


3.1.0 (2025-03-31)
~~~~~~~~~~~~~~~~~~

* Improved performance of ``as_traceback`` by a large factor.
  Contributed by Haoyu Weng in `#81 <https://github.com/ionelmc/python-tblib/pull/81>`_.
* Dropped support for now-EOL Python 3.8 and added 3.13 in the test grid.

3.0.0 (2023-10-22)
~~~~~~~~~~~~~~~~~~

* Added support for  ``__context__``, ``__suppress_context__`` and ``__notes__``.
  Contributed by Tim Maxwell in `#72 <https://github.com/ionelmc/python-tblib/pull/72>`_.
* Added the ``get_locals`` argument to ``tblib.pickling_support.install()``, ``tblib.Traceback`` and ``tblib.Frame``.
  Fixes `#41 <https://github.com/ionelmc/python-tblib/issues/41>`_.
* Dropped support for now-EOL Python 3.7 and added 3.12 in the test grid.

2.0.0 (2023-06-22)
~~~~~~~~~~~~~~~~~~

* Removed support for legacy Pythons (2.7 and 3.6) and added Python 3.11 in the test grid.
* Some cleanups and refactors (mostly from ruff).

1.7.0 (2020-07-24)
~~~~~~~~~~~~~~~~~~

* Add more attributes to ``Frame`` and ``Code`` objects for pytest compatibility. Contributed by Ivanq in
  `#58 <https://github.com/ionelmc/python-tblib/pull/58>`_.

1.6.0 (2019-12-07)
~~~~~~~~~~~~~~~~~~

* When pickling an Exception, also pickle its traceback and the Exception chain
  (``raise ... from ...``). Contributed by Guido Imperiale in
  `#53 <https://github.com/ionelmc/python-tblib/issues/53>`_.

1.5.0 (2019-10-23)
~~~~~~~~~~~~~~~~~~

* Added support for Python 3.8. Contributed by Victor Stinner in
  `#42 <https://github.com/ionelmc/python-tblib/issues/42>`_.
* Removed support for end of life Python 3.4.
* Few CI improvements and fixes.

1.4.0 (2019-05-02)
~~~~~~~~~~~~~~~~~~

* Removed support for end of life Python 3.3.
* Fixed tests for Python 3.7. Contributed by Elliott Sales de Andrade in
  `#36 <https://github.com/ionelmc/python-tblib/issues/36>`_.
* Fixed compatibility issue with Twised (``twisted.python.failure.Failure`` expected a ``co_code`` attribute).

1.3.2 (2017-04-09)
~~~~~~~~~~~~~~~~~~

* Add support for PyPy3.5-5.7.1-beta. Previously ``AttributeError:
  'Frame' object has no attribute 'clear'``  could be raised. See PyPy
  issue `#2532 <https://github.com/pypy/pypy/issues/2532>`_.

1.3.1 (2017-03-27)
~~~~~~~~~~~~~~~~~~

* Fixed handling for tracebacks due to exceeding the recursion limit.
  Fixes `#15 <https://github.com/ionelmc/python-tblib/issues/15>`_.

1.3.0 (2016-03-08)
~~~~~~~~~~~~~~~~~~

* Added ``Traceback.from_string``.

1.2.0 (2015-12-18)
~~~~~~~~~~~~~~~~~~

* Fixed handling for tracebacks from generators and other internal improvements
  and optimizations. Contributed by DRayX in `#10 <https://github.com/ionelmc/python-tblib/issues/10>`_
  and `#11 <https://github.com/ionelmc/python-tblib/pull/11>`_.

1.1.0 (2015-07-27)
~~~~~~~~~~~~~~~~~~

* Added support for Python 2.6. Contributed by Arcadiy Ivanov in
  `#8 <https://github.com/ionelmc/python-tblib/pull/8>`_.

1.0.0 (2015-03-30)
~~~~~~~~~~~~~~~~~~

* Added ``to_dict`` method and ``from_dict`` classmethod on Tracebacks.
  Contributed by beckjake in `#5 <https://github.com/ionelmc/python-tblib/pull/5>`_.
