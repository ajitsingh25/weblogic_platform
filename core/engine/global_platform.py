
from java.io import FileInputStream
from java.util import Properties

import os

def load_global_registry():
    reg = Properties()
    reg_file = 'global_platform.properties'
    if os.path.isfile(reg_file):
        reg_fd = FileInputStream(reg_file)
        reg.load(reg_fd)
        reg_fd.close()
    return reg
