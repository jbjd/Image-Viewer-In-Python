"""
A lightweight image viewer app to be called like "python image_viewer path/to/image"

"""

import os
import sys
from functools import partial
from viewer import ViewerApp


def exception_hook(error_type, error: Exception, trace, path_to_exe: str):
    """Writes unhandled fatal exception to file"""
    from util.os import show_error_with_yes_no

    error_file: str = os.path.join(path_to_exe, "ERROR.log")

    if show_error_with_yes_no(error_type, error, error_file):
        return

    import traceback

    try:  # Try to write, but don't allow another exception since that may be confusing
        with open(error_file, "w") as fp:
            traceback.print_exception(error_type, error, trace, file=fp)  # type: ignore
    except Exception:
        pass


if len(sys.argv) > 1:
    path_to_exe: str = os.path.abspath(sys.argv[0])

    # This will always be true when compiled
    # But if called like 'python image_viewer path' it will pass dir not file
    if not os.path.isdir(path_to_exe):
        path_to_exe = os.path.dirname(path_to_exe)

    sys.excepthook = partial(exception_hook, path_to_exe=path_to_exe)

    ViewerApp(sys.argv[1], path_to_exe)
