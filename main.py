import os
from sys import argv

from viewer import Viewer

if len(argv) > 1:
    path_to_exe: str = os.path.dirname(os.path.realpath(argv[0]))
    Viewer(argv[1], path_to_exe)
else:
    print(
        "An Image Viewer written in Python\n"
        "Run with 'python -m viewer C:/path/to/an/image'"
        ' or convert to an exe and select "open with" on your image'
    )
