from collections import namedtuple
from collections.abc import Callable
from io import BytesIO
from os import stat
from threading import Thread

from PIL import UnidentifiedImageError
from PIL.Image import Image
from PIL.Image import open as open_image

from animation.frame import Frame
from constants import Rotation, ZoomDirection
from image.resizer import ImageResizer
from state.rotation_state import RotationState
from state.zoom_state import ZoomState
from util.image import ImageCache, ImageCacheEntry, magic_number_guess
from util.os import get_byte_display
from util.PIL import get_placeholder_for_errored_image, rotate_image


class ReadImageResponse(namedtuple("_ReadImageResponse", ["image", "format"])):
    """Response when reading an image from disk"""

    image: Image
    format: str


class ImageLoader:
    """Handles loading images from disk"""

    DEFAULT_ANIMATION_SPEED: int = 100  # in milliseconds

    __slots__ = (
        "_rotation_state",
        "_zoom_state",
        "animation_frames",
        "animation_callback",
        "current_load_id",
        "frame_index",
        "image_cache",
        "image_resizer",
        "PIL_image",
        "zoomed_image_cache",
    )

    def __init__(
        self,
        image_resizer: ImageResizer,
        image_cache: ImageCache,
        animation_callback: Callable[[int, int], None],
    ) -> None:
        self.image_cache: ImageCache = image_cache
        self.image_resizer: ImageResizer = image_resizer

        self.animation_callback: Callable[[int, int], None] = animation_callback

        self.PIL_image = Image()
        self.current_load_id: int = 0

        self.animation_frames: list[Frame | None] = []
        self.frame_index: int = 0
        self._rotation_state = RotationState()
        self._zoom_state = ZoomState()
        self.zoomed_image_cache: list[Image] = []

    def get_next_frame(self) -> Frame | None:
        """Gets next frame of animated image or empty frame while its being loaded"""
        try:
            self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
            current_frame = self.animation_frames[self.frame_index]
        except (ZeroDivisionError, IndexError):
            return None

        if current_frame is None:
            self.frame_index -= 1

        return current_frame

    def begin_animation(
        self, original_image: Image, resized_image: Image, frame_count: int
    ) -> None:
        """Begins new thread to load frames of an animated image"""
        self.animation_frames = [None] * frame_count

        first_frame: Frame = Frame(resized_image)
        self.animation_frames[0] = first_frame

        Thread(
            target=self.load_remaining_frames,
            args=(original_image, frame_count, self.current_load_id),
            daemon=True,
        ).start()

        ms_until_next_frame: int = first_frame.ms_until_next_frame
        backoff: int = ms_until_next_frame + 50
        self.animation_callback(ms_until_next_frame, backoff)

    def read_image(self, path_to_image: str) -> ReadImageResponse | None:
        """Tries to open file on disk as PIL Image
        Returns Image or None on failure"""
        try:
            with open(path_to_image, "rb") as fp:
                expected_format: str = magic_number_guess(fp.read(4))

                fp.seek(0)
                image_bytes: BytesIO = BytesIO(fp.read())
                image: Image = open_image(image_bytes, "r", (expected_format,))

                return ReadImageResponse(image, expected_format)
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            return None

    def load_image(self, path_to_image: str) -> Image | None:
        """Loads an image, resizes it to screen, and caches it.
        Returns Image or None on failure"""
        read_image_response: ReadImageResponse | None = self.read_image(path_to_image)
        if read_image_response is None:
            return None

        original_image: Image = read_image_response.image
        self.current_load_id += 1
        self.PIL_image = original_image
        byte_size: int = stat(path_to_image).st_size

        # check if was cached and not changed outside of program
        resized_image: Image
        cached_image_data = self.image_cache.get(path_to_image)
        if cached_image_data is not None and byte_size == cached_image_data.byte_size:
            resized_image = cached_image_data.image
        else:
            original_mode: str = original_image.mode
            resized_image = self._resize_or_get_placeholder()
            size_display: str = get_byte_display(byte_size)

            self.image_cache[path_to_image] = ImageCacheEntry(
                resized_image,
                original_image.size,
                size_display,
                byte_size,
                original_mode,
                read_image_response.format,
            )

        frame_count: int = getattr(original_image, "n_frames", 1)
        if frame_count > 1:
            self.begin_animation(original_image, resized_image, frame_count)

        # first zoom level is just the image as is
        self.zoomed_image_cache = [resized_image]

        return resized_image

    def _resize_or_get_placeholder(self) -> Image:
        """Resizes PIL image or returns placeholder if corrupted in some way"""
        current_image: Image
        try:
            current_image = self.image_resizer.get_image_fit_to_screen(self.PIL_image)
        except OSError as e:
            current_image = get_placeholder_for_errored_image(
                e,
                self.image_resizer.screen_width,
                self.image_resizer.screen_height,
            )

        return current_image

    # TODO: This was a messy join of zoom and rotation. It should be refactored
    # For instance, its weird rotation can be passed as None while zoom can't
    def get_zoomed_or_rotated_image(
        self, direction: ZoomDirection, rotation: Rotation | None = None
    ) -> Image | None:
        """Gets current image with orientation changes like zoom and rotation"""
        if not self._zoom_state.try_update_zoom_level(direction) and (
            rotation is None or rotation == self._rotation_state.orientation
        ):
            return None

        if rotation is not None:
            self._rotation_state.orientation = rotation
            rotation_angle = rotation
        else:
            rotation_angle = self._rotation_state.orientation

        zoom_level: int = self._zoom_state.level
        if zoom_level < len(self.zoomed_image_cache):
            return rotate_image(self.zoomed_image_cache[zoom_level], rotation_angle)

        # Not in cache, resize to new zoom
        try:
            zoomed_image, hit_zoom_cap = self.image_resizer.get_zoomed_image(
                self.PIL_image, zoom_level
            )
            if hit_zoom_cap:
                self._zoom_state.hit_cap()

            self.zoomed_image_cache.append(zoomed_image)

            return rotate_image(zoomed_image, rotation_angle)
        except ValueError:
            # TODO: Refactor ValueError case (image exceeds JPEG dimension max)
            self._zoom_state.level -= 1
            self._zoom_state.hit_cap()
            return None
        except (FileNotFoundError, UnidentifiedImageError):
            pass

        return None

    def load_remaining_frames(
        self, original_image: Image, last_frame: int, load_id: int
    ) -> None:
        """Loads all frames starting from the second"""
        for i in range(1, last_frame):
            if load_id != self.current_load_id:
                break
            try:
                original_image.seek(i)
                frame_image: Image = self.image_resizer.get_image_fit_to_screen(
                    original_image
                )

                self.animation_frames[i] = Frame(frame_image)
            except Exception:
                # moving to new image during this function causes a variety of errors
                # just break to kill thread
                break

    def reset_and_setup(self) -> None:
        """Resets zoom, animation frames, and closes previous image
        to setup for next image load"""
        self.animation_frames = []
        self.frame_index = 0
        self.PIL_image.close()
        self._rotation_state.reset()
        self._zoom_state.reset()
        self.zoomed_image_cache = []
