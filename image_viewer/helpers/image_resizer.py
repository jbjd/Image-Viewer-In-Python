import os
from typing import Final

from PIL.Image import Image, Resampling, fromarray
from PIL.ImageTk import PhotoImage
from turbojpeg import TJPF_RGB, TurboJPEG

from util.PIL import resize


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    ZOOM_MIN: float = 2.0

    __slots__ = ("jpeg_helper", "screen_height", "screen_width")

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: Final[int] = screen_width
        self.screen_height: Final[int] = screen_height

        self.jpeg_helper = TurboJPEG(
            os.path.join(path_to_exe, "dll/libturbojpeg.dll")
            if os.name == "nt"
            else None
        )

    def get_zoomed_image(
        self, image: Image, zoom_level: int
    ) -> tuple[PhotoImage, bool]:
        """Resizes image using the provided zoom_level and bool if max zoom reached"""
        width, height = image.size
        zoom_factor: float = self._calc_zoom_factor(width, height, zoom_level)

        dimensions, interpolation = self.dimension_finder(
            *self._scale_dimensions(image.size, zoom_factor)
        )
        dimensions = self._scale_dimensions(dimensions, zoom_factor)

        max_zoom_hit: bool
        if self._too_zoomed_in(dimensions, zoom_factor):
            max_zoom_hit = True
            dimensions = (
                self._fit_to_screen_height(width, height)
                if height < self.screen_height
                else self._fit_to_screen_width(width, height)
            )
        else:
            max_zoom_hit = False

        return PhotoImage(resize(image, dimensions, interpolation)), max_zoom_hit

    def _calc_zoom_factor(self, width: int, height: int, zoom_level: int) -> float:
        """Calcs zoom factor based on image size vs screen, zoom level, and w/h ratio"""
        zoom_scale: int = 1 + int(
            max(width / self.screen_width, height / self.screen_height) / 5
        )
        # w/h ratio divide by magic 6 since seemed best after testing
        wh_ratio: int = 1 + max(width // height, height // width) // 6
        return 1 + (0.25 * zoom_scale * zoom_level * wh_ratio)

    def _too_zoomed_in(self, dimensions: tuple[int, int], zoom_factor) -> bool:
        """Returns bool if new image dimensions would zoom in too much"""
        return (
            dimensions[0] >= self.screen_width
            and dimensions[1] >= self.screen_height
            and zoom_factor > self.ZOOM_MIN
        )

    @staticmethod
    def _scale_dimensions(t: tuple[int, int], scale: float) -> tuple[int, int]:
        first, second = t
        return (int(first * scale), int(second * scale))

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
        else fit to width and let height go off screen.
        Returns new width, new height, and interpolation to use"""
        interpolation: Resampling = self._determine_interpolation(
            image_width, image_height
        )
        fit_to_height: tuple[int, int] = self._fit_to_screen_height(
            image_width, image_height
        )
        return (
            fit_to_height
            if fit_to_height[0] <= self.screen_width
            else self._fit_to_screen_width(image_width, image_height)
        ), interpolation

    def _determine_interpolation(
        self, image_width: int, image_height: int
    ) -> Resampling:
        """Determine resampling to use based on image and screen"""
        height_is_big: bool = image_height >= self.screen_height
        width_is_big: bool = image_width >= self.screen_width

        if height_is_big and width_is_big:
            return Resampling.HAMMING
        elif height_is_big or width_is_big:
            return Resampling.BICUBIC
        else:
            return Resampling.LANCZOS

    def _fit_to_screen_height(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's height"""
        width: int = round(image_width * (self.screen_height / image_height))
        return (width, self.screen_height)

    def _fit_to_screen_width(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's width"""
        height: int = round(image_height * (self.screen_width / image_width))
        return (self.screen_width, height)
