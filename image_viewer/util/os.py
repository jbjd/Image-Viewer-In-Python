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

    illegal_char = compile(r'[<>:"|?*]')
    separators = r"[\\/]"
    kb_size = 1024

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:  # linux / can't determine / unsupported OS
    illegal_char = compile(r"[]")
    separators = r"[/]"
    kb_size = 1000

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b


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
    size_in_kb: int = bytes // kb_size
    return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


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
