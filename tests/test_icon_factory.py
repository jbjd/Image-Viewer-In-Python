from tkinter import Tk

import pytest
from PIL.ImageTk import PhotoImage

from image_viewer.factories.icon_factory import IconFactory


@pytest.fixture
def icon_factory() -> IconFactory:
    return IconFactory(32)


def test_create_icons(tk_app: Tk, icon_factory: IconFactory):
    """Ensure all photoimages created successfully"""
    topbar: PhotoImage = icon_factory.make_topbar(1920)
    assert isinstance(topbar, PhotoImage)

    icon, icon_hovered = icon_factory.make_exit_icons()
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)

    icon, icon_hovered = icon_factory.make_minify_icons()
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)

    icon, icon_hovered = icon_factory.make_trash_icons()
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)

    icon, icon_hovered = icon_factory.make_rename_icons()
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)

    icon, icon_hovered, *tmp = icon_factory.make_dropdown_icons()
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)

    icon, icon_hovered = tmp
    assert isinstance(icon, PhotoImage) and isinstance(icon_hovered, PhotoImage)
