from unittest.mock import MagicMock, patch

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


def test_create_assets(canvas: CustomCanvas, example_image: Image):
    """Ensure creation of buttons, text, and topbar goes well"""

    # Should store id after creation
    canvas.create_name_text(0, 0, "test.png")
    assert canvas.file_name_text_id

    assert canvas.update_file_name("new.png")

    # Should store image after creation or garbage collector kills topbar
    display_image = PhotoImage(example_image)
    canvas.create_topbar(display_image)
    assert canvas.topbar is display_image


def test_update_image_display(canvas: CustomCanvas, example_image: Image):
    """Should center images on update_image_display and
    preserve coords on update_existing_image_display"""
    display_image = PhotoImage(example_image)
    canvas.update_image_display(display_image)
    image_id: int = canvas.image_display.id

    assert image_id != -1

    # Move, update existing, and assert image was not moved
    canvas.moveto(image_id, -1, -1)
    original_coords: list[float] = canvas.coords(image_id)

    canvas.update_existing_image_display(display_image)
    assert image_id == canvas.image_display.id
    assert original_coords == canvas.coords(image_id)

    # When updating a new image, should re-center
    canvas.update_image_display(display_image)
    assert image_id != canvas.image_display.id
    assert original_coords != canvas.coords(image_id)


def test_widget_visible(canvas: CustomCanvas):
    """Is widget visible function should be accurate"""
    widget_id: int = canvas.create_rectangle(0, 0, 10, 10)
    assert canvas.is_widget_visible(widget_id)

    canvas.itemconfigure(widget_id, state="hidden")
    assert not canvas.is_widget_visible(widget_id)


@pytest.mark.parametrize(
    "start_coords,end_coords,expected_move_amount",
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


def test_get_button_id(canvas: CustomCanvas, example_image: Image):
    """Should keep track of buttons and correctly return their id"""

    mock_button = MagicMock()
    mock_button.id = 1234
    button_name: str = "my_button"

    canvas.create_button(mock_button, button_name, 0, 0, PhotoImage(example_image))

    assert canvas.get_button_id(button_name) == mock_button.id


def test_mock_button_click(canvas: CustomCanvas, example_image: Image):
    """Should call on_click and on_leave functions of button"""

    mock_button = MagicMock()
    button_name: str = "my_button"
    mock_on_click = MagicMock()
    mock_on_leave = MagicMock()
    mock_button.on_click = mock_on_click
    mock_button.on_leave = mock_on_leave

    canvas.create_button(mock_button, button_name, 0, 0, PhotoImage(example_image))

    canvas.mock_button_click(button_name)

    mock_on_click.assert_called_once_with(None)
    mock_on_leave.assert_called_once_with(None)
