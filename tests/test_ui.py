from image_viewer.ui.image import DropdownImage


def test_dropdown_image():
    """Ensures basic functionality of dropdown image container"""
    dropdown = DropdownImage(123)
    assert not dropdown.show
    dropdown.toggle_display()
    assert dropdown.show
