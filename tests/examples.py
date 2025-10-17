def func_a(_):
    func_b()


def func_b():
    func_c()


def func_c():
    func_d()


def func_d():
    raise Exception('Guessing time !')


def bad_syntax():
    import badsyntax  # noqa: PLC0415

    badsyntax()


def bad_module():
    import badmodule  # noqa: PLC0415

    badmodule()
