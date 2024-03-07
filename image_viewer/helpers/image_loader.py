from collections.abc import Callable
from os import stat
from threading import Thread

from PIL import UnidentifiedImageError
from PIL.Image import Image
from PIL.Image import open as open_image
from PIL.ImageTk import PhotoImage

from helpers.image_resizer import ImageResizer
from managers.file_manager import ImageFileManager
from util.image import CachedImage, magic_number_guess
from util.os import get_byte_display
from util.PIL import get_placeholder_for_errored_image


class ImageLoader:
    """Handles loading images from disk"""

    DEFAULT_ANIMATION_SPEED: int = 100  # in milliseconds

    __slots__ = (
        "animation_frames",
        "animation_callback",
        "file_manager",
        "PIL_image",
        "frame_index",
        "image_resizer",
        "zoom_cap",
        "zoom_level",
        "zoomed_image_cache",
    )

    def __init__(
        self,
        file_manager: ImageFileManager,
        image_resizer: ImageResizer,
        animation_callback: Callable[[int, int], None],
    ) -> None:
        self.file_manager: ImageFileManager = file_manager
        self.image_resizer: ImageResizer = image_resizer

        self.animation_callback: Callable[[int, int], None] = animation_callback

        self.PIL_image = Image()

        self.animation_frames: list[tuple[PhotoImage | None, int]] = []
        self.frame_index: int = 0
        self.zoom_cap: int = 512
        self.zoom_level: int = 0
        self.zoomed_image_cache: list[PhotoImage] = []

    def get_next_frame(self) -> tuple[PhotoImage | None, int]:
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

    def begin_animation(self, current_image: PhotoImage, frame_count: int) -> None:
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

    def _cache_image(
        self,
        current_image: PhotoImage,
        dimensions: tuple[int, int],
        byte_size: int,
        mode: str,
    ) -> None:
        size_display: str = get_byte_display(byte_size)

        self.file_manager.cache_image(
            CachedImage(
                current_image,
                *dimensions,
                size_display,
                byte_size,
                mode,
            )
        )

    def load_image(self) -> PhotoImage | None:
        """Loads an image and resizes it to fit on the screen
        Returns PhotoImage or None on failure to load"""
        try:
            # open even if in cache to throw error if user deleted it outside of program
            fp = open(self.file_manager.path_to_current_image, "rb")
            self.PIL_image = open_image(fp, "r", magic_number_guess(fp.read(4)))
        except (FileNotFoundError, UnidentifiedImageError):
            return None

        PIL_image = self.PIL_image
        byte_size: int = stat(self.file_manager.path_to_current_image).st_size

        # check if was cached and not changed outside of program
        current_image: PhotoImage
        cached_image_data = self.file_manager.get_current_image_cache()
        if cached_image_data is not None and byte_size == cached_image_data.byte_size:
            current_image = cached_image_data.image
        else:
            original_mode: str = PIL_image.mode  # save since resize might change it
            try:
                current_image = self.image_resizer.get_image_fit_to_screen(PIL_image)
            except OSError as e:
                # Likely truncated, you can force PIL to not error here, but image
                # will black screen. Gonna return None instead so image gets skipped
                current_image = get_placeholder_for_errored_image(
                    e,
                    self.image_resizer.screen_width,
                    self.image_resizer.screen_height,
                )

            self._cache_image(current_image, PIL_image.size, byte_size, original_mode)

        frame_count: int = getattr(PIL_image, "n_frames", 1)
        if frame_count > 1:
            # file pointer will be closed when animation finished loading
            self.begin_animation(current_image, frame_count)
        else:
            PIL_image.close()

        # first zoom level is just the image as is
        self.zoomed_image_cache = [current_image]

        return current_image

    def get_zoomed_image(self, event_keycode: int) -> PhotoImage | None:
        """Handles getting and caching zoomed versions of the current image"""
        if not self._try_update_zoom_level(event_keycode):
            return None

        if self.zoom_level < len(self.zoomed_image_cache):
            return self.zoomed_image_cache[self.zoom_level]

        # Not in cache, resize to new zoom
        try:
            with open_image(self.file_manager.path_to_current_image) as fp:
                zoomed_image = self.image_resizer.get_zoomed_image(fp, self.zoom_level)

            self.zoomed_image_cache.append(zoomed_image)
            return zoomed_image
        except ValueError:  # image resizer determined zoom cap exceeded
            self.zoom_level -= 1
            self.zoom_cap = self.zoom_level
        except (FileNotFoundError, UnidentifiedImageError):
            pass

        return None

    def _try_update_zoom_level(self, event_keycode: int) -> bool:
        """Trys to update zoom level and returns if zoom changed"""
        previous_zoom: int = self.zoom_level

        if event_keycode == 189 and previous_zoom > 0:  # minus key
            self.zoom_level -= 1
        elif event_keycode == 187 and previous_zoom < self.zoom_cap:  # plus key
            self.zoom_level += 1

        return previous_zoom != self.zoom_level

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
                    self.image_resizer.get_image_fit_to_screen(PIL_image),
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
        self.zoom_cap = 512
        self.zoom_level = 0
        self.zoomed_image_cache = []
