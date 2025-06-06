import pytest

from image_viewer.constants import ZoomDirection
from image_viewer.state.zoom_state import ZoomState


@pytest.fixture
def zoom_state() -> ZoomState:
    return ZoomState()


def test_try_update_zoom_level(zoom_state: ZoomState):
    """Should move zoom up or down based on input"""
    assert zoom_state.level == 0

    updated = zoom_state.try_update_zoom_level(ZoomDirection.OUT)
    assert zoom_state.level == 0
    assert not updated

    updated = zoom_state.try_update_zoom_level(ZoomDirection.IN)
    assert zoom_state.level == 1
    assert updated

    updated = zoom_state.try_update_zoom_level(ZoomDirection.OUT)
    assert zoom_state.level == 0
    assert updated


def test_utility_functions(zoom_state: ZoomState):
    """Ensure zoom cap sets correctly and reset goes to default values"""
    zoom_state.level = 5
    zoom_state.set_current_zoom_level_as_max()

    assert zoom_state._max_level == 5

    zoom_state.reset()

    default_zoom_state = ZoomState()
    assert zoom_state.level == default_zoom_state.level
    assert zoom_state._max_level == default_zoom_state._max_level
