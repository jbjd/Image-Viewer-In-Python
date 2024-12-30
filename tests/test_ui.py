from image_viewer.ui.image import DropdownImageUIElement, ImageUIElement


def test_ui_element_update():
    some_ui_element = ImageUIElement(None, id=1)

    new_id = 99
    some_ui_element.update(id=new_id)

    assert some_ui_element.id == new_id


def test_dropdown_image():
    """Ensures basic functionality of dropdown image container"""
    dropdown = DropdownImageUIElement(123)
    assert not dropdown.show
    dropdown.toggle_display()
    assert dropdown.show
