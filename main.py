import os
from sys import argv

from viewer import Viewer

if len(argv) > 1:
    path_to_exe: str = os.path.dirname(os.path.realpath(argv[0]))
    Viewer(argv[1], path_to_exe)
