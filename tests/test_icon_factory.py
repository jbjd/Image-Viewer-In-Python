from tkinter import Tk

import pytest
from PIL.ImageTk import PhotoImage

from image_viewer.ui.button import IconImages
from image_viewer.factories.icon_factory import IconFactory


@pytest.fixture
def icon_factory() -> IconFactory:
    return IconFactory(32)


def _validate_icon_type(icons: IconImages):
    icon, icon_hovered = icons
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)


def test_create_icons(tk_app: Tk, icon_factory: IconFactory):
    """Ensure all photoimages created successfully"""
    topbar: PhotoImage = icon_factory.make_topbar_image(1920)
    assert isinstance(topbar, PhotoImage)

    _validate_icon_type(icon_factory.make_exit_icons())

    _validate_icon_type(icon_factory.make_minify_icons())

    _validate_icon_type(icon_factory.make_trash_icons())

    _validate_icon_type(icon_factory.make_rename_icons())

    down_icons, up_icons = icon_factory.make_dropdown_icons()

    _validate_icon_type(down_icons)
    _validate_icon_type(up_icons)
