import pytest

from image_viewer.constants import Key
from image_viewer.ui.canvas import CustomCanvas
from tests.test_util.mocks import MockEvent


@pytest.fixture(scope="module")
def left_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym=Key.LEFT)


@pytest.fixture(scope="module")
def right_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym=Key.RIGHT)


def test_create_assets(canvas: CustomCanvas):
    """Ensure creation of buttons, text, and topbar goes well"""

    # Should store id after creation
    canvas.create_name_text(0, 0, "test.png")
    assert canvas.file_name_text_id

    assert canvas.update_file_name("new.png")

    # Should store image after creation, normally a PhotoImage but a None for testing
    canvas.create_topbar(None)  # type: ignore
    assert canvas.topbar is None


def test_clean_long_name():
    long_name: str = "too_long12" * 10 + ".png"
    assert (
        CustomCanvas._clean_long_name(long_name)
        == "too_long12too_long12too_long12too_long(…).png"
    )


def test_widget_visible(canvas: CustomCanvas):
    """Is widget visible functoin should be accurate"""
    widget_id: int = canvas.create_rectangle(0, 0, 10, 10)
    assert canvas.is_widget_visible(widget_id)

    canvas.itemconfigure(widget_id, state="hidden")
    assert not canvas.is_widget_visible(widget_id)
