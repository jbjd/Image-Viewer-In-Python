from unittest.mock import patch

import pytest
from PIL.Image import Image
from PIL.ImageTk import PhotoImage

from image_viewer.constants import Key
from image_viewer.ui.canvas import CustomCanvas
from tests.test_util.mocks import MockEvent


@pytest.fixture(scope="module")
def left_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym_num=Key.LEFT)


@pytest.fixture(scope="module")
def right_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym_num=Key.RIGHT)


def test_create_assets(canvas: CustomCanvas):
    """Ensure creation of buttons, text, and topbar goes well"""

    # Should store id after creation
    canvas.create_name_text(0, 0, "test.png")
    assert canvas.file_name_text_id

    assert canvas.update_file_name("new.png")

    # Should store image after creation, normally a PhotoImage but a None for testing
    canvas.create_topbar(None)  # type: ignore
    assert canvas.topbar is None


def test_widget_visible(canvas: CustomCanvas):
    """Is widget visible functoin should be accurate"""
    widget_id: int = canvas.create_rectangle(0, 0, 10, 10)
    assert canvas.is_widget_visible(widget_id)

    canvas.itemconfigure(widget_id, state="hidden")
    assert not canvas.is_widget_visible(widget_id)


@pytest.mark.parametrize(
    "start_coords, end_coords, expected_move_amount",
    [
        ((0, 0), (10, 10), (10, 10)),
        ((0, 0), (9999, 9999), (1920, 1080)),
        ((0, 0), (-99, -99), (-10, -10)),  # example_image is 10x10
    ],
)
def test_drag(
    canvas: CustomCanvas,
    example_image: Image,
    start_coords: tuple[int, int],
    end_coords: tuple[int, int],
    expected_move_amount: tuple[int, int],
):
    """Should move image amount dragged"""
    canvas.screen_width = 1920
    canvas.screen_height = 1080
    canvas.update_image_display(PhotoImage(example_image))

    start_x, start_y = start_coords
    event_origin = MockEvent(x=start_x, y=start_y)
    end_x, end_y = end_coords
    event_end = MockEvent(x=end_x, y=end_y)

    canvas.moveto(canvas.image_display.id, 0, 0)
    with patch.object(CustomCanvas, "move") as mock_move:
        canvas._move_from(event_origin)
        canvas._move_to(event_end)

        mock_move.assert_called_once_with(
            canvas.image_display.id, *expected_move_amount
        )
