from unittest.mock import patch

import pytest

from image_viewer.constants import Key
from image_viewer.ui.canvas import CustomCanvas
from test_util.mocks import MockEvent


@pytest.fixture(scope="module")
def left_key_event(tk_app):
    return MockEvent(widget=tk_app, keycode=Key.LEFT)


@pytest.fixture(scope="module")
def right_key_event(tk_app):
    return MockEvent(widget=tk_app, keycode=Key.RIGHT)


@pytest.fixture(scope="module")
def up_key_event(tk_app):
    return MockEvent(widget=tk_app, keycode=Key.UP)


@pytest.fixture(scope="module")
def down_key_event(tk_app):
    return MockEvent(widget=tk_app, keycode=Key.DOWN)


def test_create_assets(canvas: CustomCanvas):
    """Ensure creation of buttons, text, and topbar goes well"""
    assert canvas.make_topbar_button(None, None, "ne", 0, lambda: None)  # type: ignore

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


def test_center_image(canvas: CustomCanvas):
    """Ensure centering image works correctly"""
    canvas.move_x = 10
    canvas.move_y = 10

    with patch.object(CustomCanvas, "move") as mock_move:
        canvas.center_image()
        assert canvas.move_x == 0
        assert canvas.move_y == 0
        mock_move.assert_called_once()


def test_widget_visible(canvas: CustomCanvas):
    """Is widget visible functoin should be accurate"""
    canvas.itemconfigure(canvas.image_display_id, state="normal")
    assert canvas.is_widget_visible(canvas.image_display_id)

    canvas.itemconfigure(canvas.image_display_id, state="hidden")
    assert not canvas.is_widget_visible(canvas.image_display_id)


@patch.object(CustomCanvas, "bbox", lambda *_: (100, 100, 100, 100))
@patch.object(CustomCanvas, "move", lambda *_: None)
def test_alt_arrow_keys(
    canvas: CustomCanvas, left_key_event, right_key_event, up_key_event, down_key_event
):
    """When clicking alt + arrow keys, image should move"""

    # move x and y axis are reversed
    canvas.handle_alt_arrow_keys(left_key_event)
    assert canvas.move_x == 10
    canvas.handle_alt_arrow_keys(right_key_event)
    assert canvas.move_x == 0
    canvas.handle_alt_arrow_keys(up_key_event)
    assert canvas.move_y == 10
    canvas.handle_alt_arrow_keys(down_key_event)
    assert canvas.move_y == 0

    # random key will not move
    bad_key = MockEvent(keycode=-1)
    canvas.handle_alt_arrow_keys(bad_key)
    assert canvas.move_x == 0
    assert canvas.move_y == 0


@patch.object(CustomCanvas, "move", lambda *_: None)
def test_alt_arrow_keys_on_edge(
    canvas: CustomCanvas, left_key_event, right_key_event, up_key_event, down_key_event
):
    """When image reaches the edge of the screen, it should not move anymore
    unless the other side is still offscreen"""

    mock_bbox: tuple[int, int, int, int] = (0, 100, 100, 100)

    with patch.object(CustomCanvas, "bbox", lambda *_: mock_bbox):
        # Image at left edge of screen
        canvas.handle_alt_arrow_keys(left_key_event)
        assert canvas.move_x == 0

        # Image at left edge of screen, but image is offscreen to the right
        mock_bbox = (0, 100, 9999, 100)
        canvas.handle_alt_arrow_keys(left_key_event)
        assert canvas.move_x == 10

        # Image at right edge of screen
        mock_bbox = (100, 100, 1920, 100)
        canvas.handle_alt_arrow_keys(right_key_event)
        assert canvas.move_x == 10

        # Image at top edge of screen, but image is offscreen to the left
        mock_bbox = (-1, 100, 1920, 100)
        canvas.handle_alt_arrow_keys(right_key_event)
        assert canvas.move_x == 0

        # Image at top edge of screen
        mock_bbox = (100, 0, 100, 100)
        canvas.handle_alt_arrow_keys(up_key_event)
        assert canvas.move_y == 0

        # Image at top edge of screen, but image is offscreen on the bottom
        mock_bbox = (100, 0, 100, 9999)
        canvas.handle_alt_arrow_keys(up_key_event)
        assert canvas.move_y == 10

        # Image at bottom edge of screen
        mock_bbox = (100, 100, 100, 1080)
        canvas.handle_alt_arrow_keys(down_key_event)
        assert canvas.move_y == 10

        # Image at bottom edge of screen, but image is offscreen on the top
        mock_bbox = (100, -1, 100, 1080)
        canvas.handle_alt_arrow_keys(down_key_event)
        assert canvas.move_y == 0
