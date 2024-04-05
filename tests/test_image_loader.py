from unittest.mock import mock_open, patch

from PIL import UnidentifiedImageError
from PIL.Image import Image

from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.helpers.image_resizer import ImageResizer
from image_viewer.util.image import CachedImage
from test_util.mocks import MockPhotoImage, MockStatResult


def test_next_frame(image_loader: ImageLoader):
    """Test expected behavior from getting next frame and resetting"""

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

    # program may try to get a frame when the animation frame list is empty
    assert image_loader.get_next_frame() == (None, 0)


def test_get_ms_until_next_frame(image_loader: ImageLoader):
    """Should get ms until next frame in animated images without erroring"""
    # non-animated image gets default
    default_speed: int = image_loader.DEFAULT_ANIMATION_SPEED
    assert image_loader.get_ms_until_next_frame() == default_speed

    image_loader.PIL_image.info["duration"] = 0
    assert image_loader.get_ms_until_next_frame() == default_speed

    image_loader.PIL_image.info["duration"] = 66
    assert image_loader.get_ms_until_next_frame() == 66


def test_load_image_error_on_open(image_loader: ImageLoader):
    """An image might error on open when its not a valid image or not found"""

    with patch("builtins.open", side_effect=FileNotFoundError):
        assert image_loader.load_image("") is None

    with patch("builtins.open", mock_open(read_data="abcd")):
        with patch(
            "image_viewer.helpers.image_loader.open_image",
            side_effect=UnidentifiedImageError(),
        ):
            assert image_loader.load_image("") is None


@patch("builtins.open", mock_open(read_data="abcd"))
@patch("image_viewer.helpers.image_loader.open_image", lambda *_: Image())
def test_load_image_in_cache(image_loader: ImageLoader):
    """When an image of the same name is in cache, don't load from disk"""

    # setup cache for test
    image_byte_size: int = 10
    cached_image = MockPhotoImage()
    cached_data = CachedImage(cached_image, (10, 10), "10kb", image_byte_size, "RGB")
    image_loader.image_cache["some/path"] = cached_data

    mock_os_stat = MockStatResult(image_byte_size)
    with patch("image_viewer.helpers.image_loader.stat", lambda _: mock_os_stat):
        assert image_loader.load_image("some/path") is cached_image


def test_load_image_resize_error(image_loader: ImageLoader):
    """Should get placeholder image when resize errors"""
    with patch.object(ImageResizer, "get_image_fit_to_screen", side_effect=OSError):
        with patch(
            "image_viewer.helpers.image_loader.get_placeholder_for_errored_image"
        ) as mock_get_placeholder:
            image_loader._load_image_from_disk()
            mock_get_placeholder.assert_called_once()
