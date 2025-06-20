"""
A lightweight image viewer app to be called like "python image_viewer path/to/image"
"""

import os
import sys
from types import TracebackType


def exception_hook(
    error_type: type[BaseException],
    error: BaseException,
    trace: TracebackType | None,
    destination_path: str,
) -> None:
    """Writes unhandled fatal exception to file"""
    error_file: str = os.path.join(destination_path, "ERROR.log")

    import traceback

    try:  # Try to write, but don't allow another exception since that may be confusing
        with open(error_file, "w", encoding="utf-8") as fp:
            traceback.print_exception(error_type, error, trace, file=fp)
    except OSError:
        pass


if __name__ == "__main__" and len(sys.argv) > 1:  # pragma: no cover
    from functools import partial

    from util.os import get_path_to_exe_folder
    from viewer import ViewerApp

    path_to_exe_folder: str = get_path_to_exe_folder()

    if not __debug__:
        sys.excepthook = partial(exception_hook, destination_path=path_to_exe_folder)

    ViewerApp(sys.argv[1], path_to_exe_folder)
