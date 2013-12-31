def func_a(_):
    func_b()

def func_b():
    func_c()

def func_c():
    func_d()

def func_d():
    raise Exception("Guessing time !")

