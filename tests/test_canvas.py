from unittest.mock import patch

from image_viewer.ui.canvas import CustomCanvas


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
