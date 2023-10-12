from viewer import Viewer
from sys import argv

if len(argv) > 1:
    Viewer(argv[1])
else:
    print(
        "An Image Viewer written in Python\n"
        "Run with 'python -m viewer C:/path/to/an/image'"
        ' or convert to an exe and select "open with" on your image'
    )
