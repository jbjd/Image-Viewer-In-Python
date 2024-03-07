"""
Code for OS specific stuff
"""

import os
from collections.abc import Iterator
from re import Pattern, compile

illegal_char: Pattern[str]
separators: str
kb_size: int
if os.name == "nt":
    from ctypes import windll

    from send2trash.win.legacy import send2trash
    from winshell import undelete, x_winshell

    illegal_char = compile(r'[<>:"|?*]')
    separators = r"[\\/]"
    kb_size = 1024

    MB_YESNO: int = 0x4
    MB_ICONERROR: int = 0x10
    IDYES: int = 6

    def ask_write_on_fatal_error(error_type, error: Exception, error_file: str) -> bool:
        """Show windows message box with error, returns True when user says no"""
        return (
            windll.user32.MessageBoxW(
                0,
                f"{str(error)}\n\nWrite traceback to {error_file}?",
                f"Unhandled {error_type.__name__} Occurred",
                MB_YESNO | MB_ICONERROR,
            )
            != IDYES
        )

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

    def restore_from_bin(original_path: str) -> None:
        try:
            undelete(os.path.normpath(original_path))
        except x_winshell:
            raise OSError  # change error type so catching is not OS specific

else:  # linux / can't determine / unsupported OS
    from send2trash import send2trash

    illegal_char = compile(r"[]")
    separators = r"[/]"
    kb_size = 1000

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b

    def ask_write_on_fatal_error(error_type, error: Exception, error_file: str) -> bool:
        return True  # TODO: add option for linux

    def restore_from_bin(original_path: str) -> None:
        raise NotImplementedError  # TODO: add option for linux


# Setup regex for truncating path
# shrink /./ to /
same_dir: Pattern[str] = compile(rf"{separators}\.({separators}|$)")

# shrink abc/123/../ to abc
previous_dir: Pattern[str] = compile(
    rf"{separators}[^{separators[1:]}+?{separators}\.\.({separators}|$)"
)


def truncate_path(path: str) -> str:
    """Shortens . and .. in paths"""
    return previous_dir.sub("/", same_dir.sub("/", path))


def clean_str_for_OS_path(file_name: str) -> str:
    """Removes characters that file names can't have on this OS"""
    return illegal_char.sub("", file_name)


def get_byte_display(bytes: int) -> str:
    """Given bytes, formats it into a string using kb or mb"""
    size_in_kb: int = bytes // kb_size
    return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


def trash_file(file_path: str) -> None:
    """OS generic send file to trash"""
    send2trash(os.path.normpath(file_path))


def walk_dir(directory_path: str) -> Iterator[str]:
    """Copied from OS module and edited to yield each file
    and only files instead of including dirs/extra info"""

    with os.scandir(directory_path) as scandir_iter:
        while True:
            try:
                entry = next(scandir_iter)
            except (StopIteration, OSError):
                return

            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False

            if not is_dir:
                yield entry.name
