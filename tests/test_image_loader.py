import pytest

from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.helpers.image_resizer import ImageResizer


@pytest.fixture
def image_loader(image_resizer: ImageResizer) -> ImageLoader:
    image_loader = ImageLoader(None, image_resizer, lambda *_: None)  # type: ignore
    return image_loader


def test_next_frame(image_loader: ImageLoader):
    """Test expected behavior from getting next frame and reseting"""

    # normally has tuples with (PhotoImage, int) but just (int, int) for testing
    image_loader.animation_frames = [(1, 1), (2, 2), (3, 3)]  # type: ignore

    example_frame: tuple | None = image_loader.get_next_frame()
    assert example_frame == (2, 2)
    example_frame = image_loader.get_next_frame()
    assert example_frame == (3, 3)
    example_frame = image_loader.get_next_frame()
    assert example_frame == (1, 1)
    example_frame = image_loader.get_next_frame()

    # if next is None, should return None but not increment internal frame index
    image_loader.animation_frames[2] = None  # type: ignore
    example_frame = image_loader.get_next_frame()
    assert example_frame is None
    assert image_loader.frame_index == 1

    # reset should set all animation variables to defaults
    image_loader.reset_and_setup()
    assert len(image_loader.animation_frames) == 0
    assert image_loader.frame_index == 0
