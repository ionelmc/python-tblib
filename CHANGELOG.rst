
Changelog
=========

1.3.1 (unreleased)
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
