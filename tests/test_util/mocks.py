from __future__ import annotations

from tkinter import Event, Tk
from typing import Self
from unittest.mock import MagicMock

from PIL.Image import Image


class MockStatResult:
    """Mocks OS's stat_result"""

    st_birthtime: int = 1649709119
    st_ctime: int = 1649709119
    st_mtime: int = 1649709119

    def __init__(self, st_size: int) -> None:
        self.st_size: int = st_size


class MockEvent(Event):
    """Mocks Tk Event"""

    def __init__(
        self, widget: Tk | None = None, keysym_num: int = 0, x: int = 0, y: int = 0
    ) -> None:
        self.widget: Tk | None = widget
        self.keysym_num: int = keysym_num
        self.x: int = x
        self.y: int = y


class MockImage(Image):
    """Mocks PIL Image for testing"""

    mode: str = "P"
    info: dict = {}
    _size: tuple[int, int] = (0, 0)

    def __init__(self, n_frames: int = 1, format: str = "") -> None:
        self.format: str = format
        self.n_frames: int = n_frames
        self.closed: bool = False

        if n_frames > 1:  # Like PIL, only set for animtions
            self.is_animated: bool = True

    def convert(self, new_mode: str) -> Self:  # type: ignore
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def close(self, *_) -> None:
        self.closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_) -> None:
        self.close()


class MockWindll:

    __slots__ = ("shell32", "user32")

    def __init__(self) -> None:
        self.shell32 = _MockShell32()
        self.user32 = _MockUser32()


class _MockShell32:
    __slots__ = ("SHOpenWithDialog",)

    def __init__(self) -> None:
        self.SHOpenWithDialog = MagicMock()


class _MockUser32:
    __slots__ = ("MessageBoxW",)

    def __init__(self) -> None:
        self.MessageBoxW = MagicMock()
