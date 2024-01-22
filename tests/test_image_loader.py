import pytest
from PIL import Image

from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.helpers.image_resizer import ImageResizer


@pytest.fixture
def image_loader(image_resizer: ImageResizer) -> ImageLoader:
    image_loader = ImageLoader(None, image_resizer, lambda *_: None)  # type: ignore
    # file_pointer will (and must) exist before calling reset
    # since first thing done is loading an image where its normally set
    image_loader.file_pointer = Image.new("RGB", (10, 10))
    return image_loader


def test_next_frame(image_loader: ImageLoader):
    """Test expected behavior from getting next frame and reseting"""

    # normally has tuples with (PhotoImage, int) but just (int, int) for testing
    image_loader.aniamtion_frames = [(1, 1), (2, 2), (3, 3)]

    example_frame: tuple | None = image_loader.get_next_frame()
    assert example_frame == (2, 2)
    example_frame = image_loader.get_next_frame()
    assert example_frame == (3, 3)
    example_frame = image_loader.get_next_frame()
    assert example_frame == (1, 1)
    example_frame = image_loader.get_next_frame()

    # if next is None, should return None but not increment internal frame index
    image_loader.aniamtion_frames[2] = None
    example_frame = image_loader.get_next_frame()
    assert example_frame is None
    assert image_loader.frame_index == 1

    # reset should set all animation variables to defaults
    image_loader.reset()
    assert len(image_loader.aniamtion_frames) == 0
    assert image_loader.frame_index == 0
