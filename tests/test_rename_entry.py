from tkinter import Tk
from unittest.mock import patch

import pytest
from conftest import should_not_be_called

from image_viewer.constants import TEXT_RGB
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.ui.rename_entry import RenameEntry


class MockEvent:
    def __init__(self, x: int) -> None:
        self.x: int = x


@pytest.fixture
def rename_entry(tk_app: Tk, canvas: CustomCanvas) -> RenameEntry:
    rename_id: int = canvas.create_window(
        0,
        0,
        width=250,
        height=20,
        anchor="nw",
    )
    return RenameEntry(tk_app, canvas, rename_id, 250, "arial 18")


def test_get(rename_entry: RenameEntry):
    rename_entry.insert(0, "  Test   ")
    assert rename_entry.get() == "Test"


def test_error_flash(rename_entry: RenameEntry):
    """Ensure error flash called correctly"""

    # If we disable the callback that error_flash normally calls after a delay
    # It should be an error red color
    rename_entry.master.after = lambda *_: None  # type: ignore
    rename_entry.error_flash()
    current_background: str = rename_entry.config()["background"][4]  # type: ignore
    assert current_background == rename_entry.ERROR_COLOR

    # If we force no delay for testing, it should go back to beign white immediately
    rename_entry.master.after = lambda _, callback: callback()  # type: ignore
    rename_entry.error_flash()
    current_background = rename_entry.config()["background"][4]  # type: ignore
    assert current_background == TEXT_RGB


def test_resize(rename_entry: RenameEntry, canvas: CustomCanvas):
    """Ensure correct behaviour when user resizes the entry"""

    with patch.object(RenameEntry, "cget", lambda *_: 250):
        rename_entry._start_resize(MockEvent(250))  # type: ignore
        assert rename_entry.being_resized

        rename_entry._resize(canvas, 251)

        config: dict = rename_entry.config()  # type: ignore
        assert config["state"][4] == "disabled"
        assert config["width"][4] == 251

        rename_entry._stop_resize(None)  # type: ignore
        assert not rename_entry.being_resized

        assert rename_entry.config()["state"][4] == "normal"  # type: ignore


def test_resize_hover(rename_entry: RenameEntry, canvas: CustomCanvas):
    """Cursor should update when user can resize entry"""

    canvas.itemconfig = should_not_be_called  # type: ignore

    with patch.object(RenameEntry, "cget", lambda *_: 250):
        # If able to resize, change cursor
        rename_entry._resize(canvas, 251)
        assert rename_entry.config()["cursor"][4] == "sb_h_double_arrow"  # type: ignore

        # When the cursor is now far away, go back to normal
        rename_entry._resize(canvas, 1)
        assert rename_entry.config()["cursor"][4] == ""  # type: ignore
