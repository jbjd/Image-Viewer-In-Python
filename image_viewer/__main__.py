"""
A lightweight image viewer app to be called like "python image_viewer path/to/image"

"""

import os
from sys import argv

from viewer import ViewerApp

if len(argv) > 1:
    path_to_exe: str = os.path.abspath(argv[0])

    # This will always be true when compiled
    # But if called like 'python image_viewer path' it will pass dir not file
    if not os.path.isdir(path_to_exe):
        path_to_exe = os.path.dirname(path_to_exe)

    ViewerApp(argv[1], path_to_exe)
