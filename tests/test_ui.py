from unittest.mock import MagicMock

from image_viewer.constants import ButtonName
from image_viewer.ui.button import (
    HoverableButtonUIElement,
    IconImages,
    ToggleableButtonUIElement,
)
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.ui.image import DropdownImageUIElement


def test_show_dropdown_image():
    """Should toggle between being shown and not"""
    dropdown = DropdownImageUIElement(123)
    assert not dropdown.show
    dropdown.toggle_display()
    assert dropdown.show


def test_button(canvas: CustomCanvas, button_icons: IconImages):
    """Ensure buttons can add themselves to canvas and
    on click/enter/leave events work as expected"""
    function_to_bind = MagicMock()
    button = HoverableButtonUIElement(canvas, button_icons, function_to_bind)

    button.add_to_canvas(ButtonName.EXIT, 0, 0)
    assert button.id != -1

    button.on_click()
    function_to_bind.assert_called_once()

    default_image_tag: str = canvas.itemcget(button.id, option="image")

    button.on_enter()
    current_image_tag = canvas.itemcget(button.id, option="image")
    assert current_image_tag != default_image_tag

    button.on_leave()
    current_image_tag = canvas.itemcget(button.id, option="image")
    assert current_image_tag == default_image_tag


# TODO: add checks for using different images in active/inactive states
def test_toggleable_button(canvas: CustomCanvas, button_icons: IconImages):
    """Ensure toggleable button goes between active/inactive states"""
    function_to_bind = MagicMock()
    button = ToggleableButtonUIElement(
        canvas, button_icons, button_icons, function_to_bind
    )
    button.add_to_canvas(ButtonName.EXIT, 0, 0)

    assert not button.is_active

    button.on_click()

    assert button.is_active
