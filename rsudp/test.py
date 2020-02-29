import os, sys
from rsudp.client import default_settings, run
from rsudp import printM, default_loc, init_dirs, output_dir, add_debug_handler

add_debug_handler()
printM('Logging for test module initialized successfully.', sender='test.py')
