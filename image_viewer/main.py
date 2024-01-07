import os
from sys import argv

from viewer import ViewerApp

if len(argv) > 1:
    path_to_exe: str = os.path.dirname(argv[0])
    ViewerApp(argv[1], path_to_exe)
