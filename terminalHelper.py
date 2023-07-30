import os

# 清空终端
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


# 清空终端
def set_workdir_to_here():
    os.system('cd ' + os.path.dirname(os.path.realpath(__file__)))