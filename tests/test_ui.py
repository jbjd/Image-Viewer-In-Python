from image_viewer.ui.image import DropdownImage


def test_dropdown_image():
    """Ensures basic functionality of dropdown image container"""
    dropdown = DropdownImage(123)
    assert not dropdown.showing
    dropdown.toggle_display()
    assert dropdown.showing
