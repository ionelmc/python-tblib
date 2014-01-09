import sys
import doctest

if __name__ == '__main__':
    results = doctest.testfile('../README.rst', optionflags=doctest.ELLIPSIS)
    print(results)
    if results.failed:
        sys.exit(1)
