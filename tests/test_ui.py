from image_viewer.ui.image import DropdownImageUIElement


def test_dropdown_image():
    """Ensures basic functionality of dropdown image container"""
    dropdown = DropdownImageUIElement(123)
    assert not dropdown.show
    dropdown.toggle_display()
    assert dropdown.show
