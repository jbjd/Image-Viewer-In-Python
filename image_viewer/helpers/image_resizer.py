import os

from PIL.Image import Image, Resampling, fromarray
from PIL.ImageTk import PhotoImage
from turbojpeg import TJPF_RGB, TurboJPEG

from util.PIL import resize


def _scale_tuple(t: tuple[int, int], scale: float) -> tuple[int, int]:
    return (int(t[0] * scale), int(t[1] * scale))


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    ZOOM_MIN: float = 2.0

    __slots__ = ("jpeg_helper", "screen_height", "screen_width")

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.jpeg_helper = TurboJPEG(
            os.path.join(path_to_exe, "dll/libturbojpeg.dll")
            if os.name == "nt"
            else None
        )

    def get_zoomed_image(self, image: Image, zoom_level: int) -> PhotoImage | None:
        """Resizes image using the provided zoom_level.
        Returns None when max zoom reached"""
        # scale zoom factor based on image size vs screen
        w, h = image.size
        ratio: int = 1 + int(max(w / self.screen_width, h / self.screen_height) / 5)
        zoom_factor: float = 1 + (0.25 * ratio * zoom_level)

        dimensions, interpolation = self.dimension_finder(
            *_scale_tuple(image.size, zoom_factor)
        )
        dimensions = _scale_tuple(dimensions, zoom_factor)
        if (
            dimensions[0] > self.screen_width
            and dimensions[1] > self.screen_height
            and zoom_factor > self.ZOOM_MIN
        ):
            return None
        return PhotoImage(resize(image, dimensions, interpolation))

    def _get_jpeg_scale_factor(
        self, image_width: int, image_height: int
    ) -> tuple[int, int] | None:
        """Gets scaling factor for images larger than screen"""
        ratio_to_screen: float = max(
            image_width / self.screen_width, image_height / self.screen_height
        )

        if ratio_to_screen >= 4:
            return (1, 4)
        if ratio_to_screen >= 2:
            return (1, 2)
        return None

    def _get_jpeg_fit_to_screen(self, image: Image) -> PhotoImage:
        """Resizes a JPEG utilizing libjpegturbo to shrink very large images"""
        image_width, image_height = image.size
        scale_factor: tuple[int, int] | None = self._get_jpeg_scale_factor(
            image_width, image_height
        )
        # if small do a normal resize, otherwise utilize libJpegTurbo
        if scale_factor is None:
            return self._fit_to_screen(image)

        image.fp.seek(0)  # type: ignore
        image_as_array = self.jpeg_helper.decode(
            image.fp.read(),  # type: ignore
            TJPF_RGB,
            scale_factor,
            0,
        )
        return self._fit_to_screen(fromarray(image_as_array))

    def _fit_to_screen(self, image: Image) -> PhotoImage:
        """Resizes image to screen and returns it as a PhotoImage"""
        return PhotoImage(resize(image, *self.dimension_finder(*image.size)))

    def get_image_fit_to_screen(self, image: Image) -> PhotoImage:
        """Returns resized image as a PhotoImage"""
        if image.format == "JPEG":
            return self._get_jpeg_fit_to_screen(image)

        return self._fit_to_screen(image)

    def dimension_finder(
        self, image_width: int, image_height: int
    ) -> tuple[tuple[int, int], Resampling]:
        """Fits dimensions to height if width within screen,
        else fit to width and let height go off screen
        returns: new width, new height, and interpolation to use"""
        interpolation: Resampling = (
            Resampling.HAMMING
            if image_height > self.screen_height or image_width > self.screen_width
            else Resampling.LANCZOS
        )
        width: int = round(image_width * (self.screen_height / image_height))

        return (
            ((width, self.screen_height), interpolation)
            if width <= self.screen_width
            else (
                (
                    self.screen_width,
                    round(image_height * (self.screen_width / image_width)),
                ),
                interpolation,
            )
        )
