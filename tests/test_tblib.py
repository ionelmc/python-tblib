import sys
import doctest
#if sys.version_info[0] == 2 and sys.version_info[1] == 6:
#    import pth
#    pth.PathError.__name__           = 'pth.' + pth.PathError.__name__
#    pth.PathMustBeFile.__name__      = 'pth.' + pth.PathMustBeFile.__name__
#    pth.PathMustBeDirectory.__name__ = 'pth.' + pth.PathMustBeDirectory.__name__
#    pth.PathDoesNotExist.__name__    = 'pth.' + pth.PathDoesNotExist.__name__

results = doctest.testfile('../README.rst', optionflags=doctest.ELLIPSIS)
print(results)
if results.failed:
    sys.exit(1)
