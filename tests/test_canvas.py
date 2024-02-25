import pytest

from image_viewer.ui.canvas import CustomCanvas, _clean_long_name


@pytest.fixture
def canvas(tk_app) -> CustomCanvas:
    return CustomCanvas(tk_app)


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
        _clean_long_name(long_name) == "too_long12too_long12too_long12too_long(…).png"
    )
