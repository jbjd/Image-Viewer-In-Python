from collections.abc import Callable
from os import stat
from threading import Thread

from cv2 import error as ResizeException
from PIL import UnidentifiedImageError
from PIL.Image import Image
from PIL.Image import open as open_image
from PIL.ImageTk import PhotoImage

from helpers.image_resizer import ImageResizer
from managers.file_manager import ImageFileManager


class ImageLoader:
    """Handles loading images from disk"""

    DEFAULT_GIF_SPEED: int = 100
    ANIMATION_SPEED_FACTOR: float = 0.82

    __slots__ = (
        "aniamtion_frames",
        "animation_callback",
        "file_manager",
        "file_pointer",
        "frame_index",
        "image_resizer",
        "zoom_cap",
        "zoom_factor",
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

        self.file_pointer: Image

        self.animation_callback: Callable[[int, int], None] = animation_callback
        self.aniamtion_frames: list = []
        self.frame_index: int = 0
        self.zoom_factor: float = 1.0
        self.zoom_cap: float = 128.0
        self.zoomed_image_cache: list[PhotoImage] = []

    def get_next_frame(self) -> tuple[PhotoImage, int] | None:
        self.frame_index = (self.frame_index + 1) % len(self.aniamtion_frames)
        current_frame = self.aniamtion_frames[self.frame_index]
        if current_frame is None:
            self.frame_index -= 1
        return current_frame

    def get_ms_until_next_frame(self) -> int:
        """Returns time until next frame for animated images"""
        return int(
            self.file_pointer.info.get("duration", self.DEFAULT_GIF_SPEED)
            * self.ANIMATION_SPEED_FACTOR
        )

    def begin_animation(self, current_image: PhotoImage, frame_count: int) -> None:
        """Begins new thread to handle dispalying frames of an aniamted image"""
        self.aniamtion_frames = [None] * frame_count

        ms_until_next_frame: int = self.get_ms_until_next_frame()

        self.aniamtion_frames[0] = current_image, ms_until_next_frame
        # begin loading frames in new thread and call animate
        Thread(
            target=self.load_remaining_frames,
            args=(self.file_pointer, frame_count),
            daemon=True,
        ).start()

        # Params: ms_until_next_frame, backoff time to help loading
        self.animation_callback(ms_until_next_frame + 20, self.DEFAULT_GIF_SPEED)

    def load_image(self) -> PhotoImage | None:
        """
        Loads an image and resizes it to fit on the screen
        Returns PhotoImage or None on failure to load
        """

        file_manager = self.file_manager
        path_to_current_image = file_manager.path_to_current_image
        try:
            # open even if in cache to throw error if user deleted it outside of program
            self.file_pointer = open_image(path_to_current_image)
        except (FileNotFoundError, UnidentifiedImageError, ImportError):
            # except import error since user might open file with inaccurate ext
            # and trigger import that was excluded if they compiled as standalone
            return None
        file_pointer = self.file_pointer

        image_kb_size: int = stat(path_to_current_image).st_size >> 10
        frame_count: int = getattr(file_pointer, "n_frames", 1)

        # check if was cached and not changed outside of program
        current_image: PhotoImage
        cached_image_data = file_manager.get_current_image_cache()
        if cached_image_data is not None and image_kb_size == cached_image_data.kb_size:
            current_image = cached_image_data.image
        else:
            try:
                if file_pointer.format == "JPEG":
                    current_image = self.image_resizer.get_jpeg_fit_to_screen(
                        file_pointer, path_to_current_image
                    )
                else:
                    current_image = self.image_resizer.get_image_fit_to_screen(
                        file_pointer
                    )
            except ResizeException:
                return None

            dimension_display: str = (
                f"{round(image_kb_size/10.24)/100}mb"
                if image_kb_size > 999
                else f"{image_kb_size}kb"
            )

            file_manager.cache_image(
                *file_pointer.size,
                dimension_display,
                current_image,
                image_kb_size,
            )

        if frame_count > 1:
            # file pointer will be closed when animation finised loading
            self.begin_animation(current_image, frame_count)
        else:
            self.file_pointer.close()

        self.zoomed_image_cache = [current_image]  # zoom 1.0 is same as current

        return current_image

    def get_zoomed_image(self, event_keycode: int) -> PhotoImage | None:
        """Handles getting and caching zoomed versions of the current image"""
        # determine new zoom factor
        previous_zoom: float = self.zoom_factor
        if event_keycode == 189 and previous_zoom > 1.0:  # -
            self.zoom_factor -= 0.25
        elif event_keycode == 187 and previous_zoom < self.zoom_cap:  # =
            self.zoom_factor += 0.25
        if previous_zoom == self.zoom_factor:
            return None
        # Check cache
        index = round(self.zoom_factor * 4) - 4  # round in case float weirdness
        if index < len(self.zoomed_image_cache):
            return self.zoomed_image_cache[index]
        # Otherwise open and resize to new zoom
        try:
            with open_image(self.file_manager.path_to_current_image) as fp:
                zoomed_image = self.image_resizer.get_zoomed_image(fp, self.zoom_factor)
                if zoomed_image is not None:
                    self.zoomed_image_cache.append(zoomed_image)
                else:
                    self.zoom_factor -= 0.25
                    self.zoom_cap = self.zoom_factor
                return zoomed_image
        except (FileNotFoundError, UnidentifiedImageError, ImportError):
            return None

    def load_remaining_frames(
        self,
        original_image: Image,
        last_frame: int,
    ) -> None:
        """Loads all frames starting from the second"""

        fp: Image = self.file_pointer
        for i in range(1, last_frame):
            # if user moved to new image, don't keep loading previous animated image
            if fp is not original_image:
                return
            try:
                fp.seek(i)
                ms_until_next_frame: int = self.get_ms_until_next_frame()

                self.aniamtion_frames[i] = (
                    self.image_resizer.get_image_fit_to_screen(fp),
                    ms_until_next_frame,
                )
            except Exception:
                # moving to new image during this function causes a variety of errors
                # just break and close to kill thread
                break

        if fp is original_image:
            original_image.close()

    def reset(self) -> None:
        """Resets zoom, animation frames, and closes previous image"""
        self.aniamtion_frames = []
        self.frame_index = 0
        self.file_pointer.close()
        self.zoom_factor = 1.0
        self.zoom_cap = 128.0
        self.zoomed_image_cache = []
