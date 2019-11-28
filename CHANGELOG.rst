
Changelog
=========

1.6.0 (unreleased)
~~~~~~~~~~~~~~~~~~
* When pickling an Exception, also pickle its traceback and the Exception chain
  (``raise ... from ...``). Contributed by Guido Imperiale in
  `#53 <https://github.com/ionelmc/python-tblib/issues/53>`_.

1.5.0 (2019-10-23)
~~~~~~~~~~~~~~~~~~

* Added support for Python 3.8. Contributed by Victor Stinner in
  `#42 <HTTPS://GITHUB.COM/IONELMC/PYTHON-TBLIB/ISSUES/42>`_.
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
  issue `#2532 <https://bitbucket.org/pypy/pypy/issues/2532/pypy3-attributeerror-frame-object-has-no>`_.

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
