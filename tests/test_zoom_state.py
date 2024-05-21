import pytest

from image_viewer.states.zoom_state import ZoomState


@pytest.fixture
def zoom_state() -> ZoomState:
    return ZoomState()


def test_try_update_zoom_level(zoom_state: ZoomState):
    """Should move zoom up or down based on input"""
    assert zoom_state.level == 0

    updated = zoom_state.try_update_zoom_level(-1)
    assert zoom_state.level == 0
    assert not updated

    updated = zoom_state.try_update_zoom_level(1)
    assert zoom_state.level == 1
    assert updated

    updated = zoom_state.try_update_zoom_level(-1)
    assert zoom_state.level == 0
    assert updated
