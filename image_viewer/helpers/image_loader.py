from collections.abc import Callable
from os import stat
from math import log
from threading import Thread

from PIL import UnidentifiedImageError
from PIL.Image import Image
from PIL.Image import open as open_image

from helpers.image_resizer import ImageResizer
from states.zoom_state import ZoomState
from util.image import CachedImage, ImageCache, magic_number_guess
from util.os import get_byte_display
from util.PIL import get_placeholder_for_errored_image


class ImageLoader:
    """Handles loading images from disk"""

    DEFAULT_ANIMATION_SPEED: int = 100  # in milliseconds

    __slots__ = (
        "animation_frames",
        "animation_callback",
        "frame_index",
        "image_cache",
        "image_pyramid",
        "image_resizer",
        "PIL_image",
        "zoom_state",
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
        self.image_pyramid: list[Image]

        self.animation_frames: list[tuple[Image | None, int]] = []
        self.frame_index: int = 0
        self.zoom_state = ZoomState()

    def get_zoomed_image(self, zoom_in: bool) -> Image | None:
        zoom_changed = self.zoom_state.try_update_zoom_level(zoom_in)
        if not zoom_changed:
            return None

        if self.zoom_state.level == 1:
            return self.image_pyramid[-1]

        zoom_scale: float = self.zoom_state.zoom_scale

        pyramid_index: int = -2 - int(log(zoom_scale, 2))
        if -pyramid_index > len(self.image_pyramid):
            pyramid_index = 0
        image = self.image_pyramid[pyramid_index]
        return self.image_resizer.get_zoomed_image(image, zoom_scale)

    def get_next_frame(self) -> tuple[Image | None, int]:
        """Gets next frame of animated image or None while its being loaded"""
        try:
            self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
            current_frame = self.animation_frames[self.frame_index]
        except (ZeroDivisionError, IndexError):
            return (None, 0)

        if current_frame is None:
            self.frame_index -= 1

        return current_frame

    def get_ms_until_next_frame(self) -> int:
        """Returns milliseconds until next frame for animated images"""
        ms: int = round(
            self.PIL_image.info.get("duration", self.DEFAULT_ANIMATION_SPEED)
        )
        return ms if ms > 1 else self.DEFAULT_ANIMATION_SPEED

    def begin_animation(self, current_image: Image, frame_count: int) -> None:
        """Begins new thread to handle displaying frames of an aniamted image"""
        self.animation_frames = [(None, 0)] * frame_count

        ms_until_next_frame: int = self.get_ms_until_next_frame()

        self.animation_frames[0] = current_image, ms_until_next_frame
        # begin loading frames in new thread and call animate
        Thread(
            target=self.load_remaining_frames,
            args=(self.PIL_image, frame_count),
            daemon=True,
        ).start()

        # Params: time until next frame, backoff time to help loading
        self.animation_callback(ms_until_next_frame + 20, self.DEFAULT_ANIMATION_SPEED)

    def get_PIL_image(self, path_to_image: str) -> Image | None:
        """Trys to open file on disk as PIL Image
        Returns Image or None on failure"""
        try:
            fp = open(path_to_image, "rb")
            type_to_try_loading: tuple[str] = magic_number_guess(fp.read(4))
            return open_image(fp, "r", type_to_try_loading)
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            return None

    def load_image(self, path_to_image: str) -> Image | None:
        """Loads an image and resizes it to fit on the screen
        Returns Image or None on failure"""
        PIL_image: Image | None = self.get_PIL_image(path_to_image)
        if PIL_image is None:
            return None

        self.PIL_image = PIL_image
        byte_size: int = stat(path_to_image).st_size

        # check if was cached and not changed outside of program
        cached_image_data = self.image_cache.get(path_to_image)
        if cached_image_data is not None and byte_size == cached_image_data.byte_size:
            self.image_pyramid = cached_image_data.image
        else:
            original_mode: str = self.PIL_image.mode
            self.image_pyramid = self._load_image_from_disk()
            size_display: str = get_byte_display(byte_size)

            self.image_cache[path_to_image] = CachedImage(
                self.image_pyramid,
                self.PIL_image.size,
                size_display,
                byte_size,
                original_mode,
            )

        frame_count: int = getattr(self.PIL_image, "n_frames", 1)
        if frame_count > 1:
            # file pointer will be closed when animation finished loading
            self.begin_animation(self.image_pyramid[0], frame_count)
        else:
            self.PIL_image.close()

        return self.image_pyramid[-1]

    def _load_image_from_disk(self) -> list[Image]:
        """Resizes PIL image, which forces a load from disk.
        Caches it and returns it as a PhotoImage"""
        current_image: list[Image]
        try:
            current_image = self.image_resizer.get_image_pyramid(self.PIL_image)
        except OSError as e:
            current_image = get_placeholder_for_errored_image(
                e,
                self.image_resizer.screen_width,
                self.image_resizer.screen_height,
            )

        return current_image

    def load_remaining_frames(
        self,
        original_image: Image,
        last_frame: int,
    ) -> None:
        """Loads all frames starting from the second"""

        PIL_image = self.PIL_image
        for i in range(1, last_frame):
            # if user moved to new image, don't keep loading previous animated image
            if PIL_image is not original_image:
                return
            try:
                PIL_image.seek(i)
                ms_until_next_frame: int = self.get_ms_until_next_frame()

                self.animation_frames[i] = (
                    self.image_resizer.get_image_pyramid(PIL_image)[0],
                    ms_until_next_frame,
                )
            except Exception:
                # moving to new image during this function causes a variety of errors
                # just break and close to kill thread
                break

        if PIL_image is original_image:
            original_image.close()

    def reset_and_setup(self) -> None:
        """Resets zoom, animation frames, and closes previous image
        to setup for next image load"""
        self.animation_frames = []
        self.frame_index = 0
        self.PIL_image.close()
        self.zoom_state.reset()
