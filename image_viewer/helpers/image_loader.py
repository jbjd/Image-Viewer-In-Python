import os
from collections.abc import Callable
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
    ANIMATION_SPEED_FACTOR: float = 0.75

    __slots__ = (
        "file_manager",
        "image_resizer",
        "file_pointer",
        "aniamtion_frames",
        "animation_callback",
        "frame_index",
    )

    def __init__(
        self,
        file_manager: ImageFileManager,
        screen_width: int,
        screen_height: int,
        path_to_exe: str,
        animation_callback: Callable,
    ) -> None:
        self.file_manager: ImageFileManager = file_manager
        self.image_resizer = ImageResizer(screen_width, screen_height, path_to_exe)

        self.file_pointer: Image

        self.animation_callback: Callable = animation_callback
        self.aniamtion_frames: list = []
        self.frame_index = 0

    def get_next_frame(self) -> tuple[PhotoImage, int] | None:
        self.frame_index = (self.frame_index + 1) % len(self.aniamtion_frames)
        current_frame = self.aniamtion_frames[self.frame_index]
        if current_frame is None:
            self.frame_index -= 1
        return current_frame

    def get_ms_until_next_frame(self) -> int:
        """Returns time until next frame for animated images"""
        try:
            speed = int(
                self.file_pointer.info["duration"] * self.ANIMATION_SPEED_FACTOR
            )
            if speed < 1:
                speed = self.DEFAULT_GIF_SPEED
        except (KeyError, AttributeError):
            speed = self.DEFAULT_GIF_SPEED

        return speed

    def _finish_image_load(self, current_image: PhotoImage, frame_count: int) -> None:
        """Begins animations if multiple frames are present, otherwise closes file"""
        if frame_count > 1:
            self.begin_animation(current_image, frame_count)
        else:
            self.file_pointer.close()

    def begin_animation(self, current_image: PhotoImage, frame_count: int) -> None:
        """Begins new thread to handle dispalying frames of an aniamted image"""
        self.aniamtion_frames = [None] * frame_count

        ms_until_next_frame: int = self.get_ms_until_next_frame()

        self.aniamtion_frames[0] = current_image, ms_until_next_frame
        # begin loading frames in new thread and call animate
        Thread(
            target=self.load_frame,
            args=(self.file_pointer, 1, frame_count),
            daemon=True,
        ).start()

        # Params: ms_until_next_frame, backoff time to help loading
        self.animation_callback(ms_until_next_frame + 20, self.DEFAULT_GIF_SPEED)

    def load_image(self) -> PhotoImage | None:
        """Loads an image and resizes it to fit on the screen
        Returns PhotoImage or None on failure to load"""
        try:
            # open even if in cache to throw error if user deleted it outside of program
            self.file_pointer = open_image(self.file_manager.path_to_current_image)
        except (FileNotFoundError, UnidentifiedImageError):
            return None

        image_kb_size: int = (
            os.stat(self.file_manager.path_to_current_image).st_size >> 10
        )
        frame_count: int = getattr(self.file_pointer, "n_frames", 1)

        current_image: PhotoImage

        # check if was cached and not changed outside of program
        cached_image_data = self.file_manager.get_cached_image_data()
        if cached_image_data is not None and image_kb_size == cached_image_data.kb_size:
            current_image = cached_image_data.image
            self._finish_image_load(current_image, frame_count)
        else:
            image_width, image_height = self.file_pointer.size
            image_size: str = (
                f"{round(image_kb_size/10.24)/100}mb"
                if image_kb_size > 999
                else f"{image_kb_size}kb"
            )

            try:
                if self.file_pointer.format == "JPEG":
                    current_image = self.image_resizer.get_jpeg_fit_to_screen(
                        self.file_pointer, self.file_manager.path_to_current_image
                    )
                else:
                    current_image = self.image_resizer.get_image_fit_to_screen(
                        self.file_pointer
                    )
            except ResizeException:
                return None

            self._finish_image_load(current_image, frame_count)

            self.file_manager.cache_image(
                image_width,
                image_height,
                image_size,
                current_image,
                image_kb_size,
            )

        return current_image

    def load_frame(
        self,
        original_image: Image,
        frame_index: int,
        last_frame: int,
    ) -> None:
        # if user moved to new image, don't keep loading previous animated image
        if self.file_pointer is not original_image:
            return
        try:
            self.file_pointer.seek(frame_index)
            ms_until_next_frame: int = self.get_ms_until_next_frame()

            self.aniamtion_frames[frame_index] = (
                self.image_resizer.get_image_fit_to_screen(self.file_pointer),
                ms_until_next_frame,
            )
        except Exception:
            # changing images during load causes a variety of errors
            pass
        frame_index += 1
        if frame_index < last_frame:
            self.load_frame(original_image, frame_index, last_frame)
        else:
            original_image.close()

    def reset(self) -> None:
        """Clears all animation frames and closes previous image pointer
        if its still open"""
        self.aniamtion_frames.clear()
        self.frame_index = 0
        self.file_pointer.close()
