import os
from typing import Final

from PIL.Image import Image, Resampling, fromarray
from turbojpeg import TJPF_RGB, TurboJPEG

from util.PIL import resize

JPEG_MAX_DIMENSION: Final[int] = 65_535
MIN_ZOOM_RATIO_TO_SCREEN: int = 2


class ZoomedImageResult:
    """Represents the result of zoom into an image where
    hit_max_zoom is True when this is the max zoom that is allowed"""

    __slots__ = ("image", "hit_max_zoom")

    def __init__(self, image: Image, hit_max_zoom: bool) -> None:
        self.image: Image = image
        self.hit_max_zoom: bool = hit_max_zoom


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    __slots__ = ("jpeg_helper", "screen_height", "screen_width")

    def __init__(
        self, path_to_exe_folder: str, screen_width: int, screen_height: int
    ) -> None:
        self.screen_width: Final[int] = screen_width
        self.screen_height: Final[int] = screen_height

        turbo_jpeg_lib_path: str | None = None  # None will auto detect

        if os.name == "nt":
            turbo_jpeg_lib_path = os.path.join(
                path_to_exe_folder, "dll/libturbojpeg.dll"
            )

        self.jpeg_helper = TurboJPEG(turbo_jpeg_lib_path)

    def get_zoomed_image(self, image: Image, zoom_level: int) -> ZoomedImageResult:
        """Resizes image using the provided zoom_level.

        Raises ValueError if resized image would exceed JPEG size max"""
        image_width, image_height = image.size
        zoom_factor: float = self._calculate_zoom_factor(
            image_width, image_height, zoom_level
        )

        # Pre-scale to determine interpolation since an image we originally shrunk
        # might now grow
        scaled_width, scaled_height = self._scale_dimensions(image.size, zoom_factor)
        interpolation = self.get_resampling(scaled_width, scaled_height)

        dimensions = self._scale_dimensions(
            self.fit_dimensions_to_screen(image_width, image_height), zoom_factor
        )

        if dimensions[0] > JPEG_MAX_DIMENSION or dimensions[1] > JPEG_MAX_DIMENSION:
            raise ValueError

        hit_max_zoom: bool = self._too_zoomed_in(dimensions)

        if hit_max_zoom:
            if dimensions[1] < self.screen_height:
                dimensions = self._fit_dimensions_to_screen_height(
                    image_width, image_height
                )
            elif dimensions[0] < self.screen_width:
                dimensions = self._fit_dimensions_to_screen_width(
                    image_width, image_height
                )

        return ZoomedImageResult(resize(image, dimensions, interpolation), hit_max_zoom)

    def _calculate_zoom_factor(self, width: int, height: int, zoom_level: int) -> float:
        """Calculates zoom factor based on zoom level and w/h ratio"""
        # w/h ratio divide by magic 6 since seemed best after testing
        wh_ratio: int = 1 + max(width // height, height // width) // 6
        return (1.4**zoom_level) * wh_ratio

    def _too_zoomed_in(self, dimensions: tuple[int, int]) -> bool:
        """Returns bool if new image dimensions would zoom in too much"""
        return (
            dimensions[0] >= self.screen_width * MIN_ZOOM_RATIO_TO_SCREEN
            and dimensions[1] >= self.screen_height * MIN_ZOOM_RATIO_TO_SCREEN
        )

    @staticmethod
    def _scale_dimensions(t: tuple[int, int], scale: float) -> tuple[int, int]:
        first, second = t
        return (int(first * scale), int(second * scale))

    def _get_jpeg_scale_factor(
        self, image_width: int, image_height: int
    ) -> tuple[int, int] | None:
        """Gets Turbo JPEG scaling factor for images larger than screen"""
        ratio_to_screen: float = max(
            image_width / self.screen_width, image_height / self.screen_height
        )

        if ratio_to_screen >= 4:
            return (1, 4)
        if ratio_to_screen >= 2:
            return (1, 2)
        return None

    def _get_jpeg_fit_to_screen(self, image: Image) -> Image:
        """Resizes a JPEG utilizing libjpeg-turbo to shrink very large images"""
        image_width, image_height = image.size
        scale_factor: tuple[int, int] | None = self._get_jpeg_scale_factor(
            image_width, image_height
        )
        # if small do a normal resize, otherwise utilize libJpegTurbo
        if scale_factor is None:
            return self._get_image_fit_to_screen_with_PIL(image)

        image.fp.seek(0)  # type: ignore
        image_as_array = self.jpeg_helper.decode(
            image.fp.read(),  # type: ignore
            TJPF_RGB,
            scale_factor,
            0,
        )
        return self._get_image_fit_to_screen_with_PIL(fromarray(image_as_array))

    def _get_image_fit_to_screen_with_PIL(self, image: Image) -> Image:
        """Resizes image to screen with PIL"""
        image_width, image_height = image.size
        interpolation: Resampling = self.get_resampling(image_width, image_height)
        dimensions: tuple[int, int] = self.fit_dimensions_to_screen(
            image_width, image_height
        )

        return resize(image, dimensions, interpolation)

    def get_image_fit_to_screen(self, image: Image) -> Image:
        """Resizes image to screen using either libjpeg-turbo or PIL"""
        if image.format == "JPEG":
            return self._get_jpeg_fit_to_screen(image)

        return self._get_image_fit_to_screen_with_PIL(image)

    def fit_dimensions_to_screen(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to height if width within screen,
        else fit to width and let height go off screen.
        Returns new width/height, and interpolation to use"""
        fit_to_height: tuple[int, int] = self._fit_dimensions_to_screen_height(
            image_width, image_height
        )
        return (
            fit_to_height
            if fit_to_height[0] <= self.screen_width
            else self._fit_dimensions_to_screen_width(image_width, image_height)
        )

    def get_resampling(self, image_width: int, image_height: int) -> Resampling:
        """Determine resampling to use based on image and screen"""
        height_is_big: bool = image_height >= self.screen_height
        width_is_big: bool = image_width >= self.screen_width

        if height_is_big and width_is_big:
            return Resampling.HAMMING
        if height_is_big or width_is_big:
            return Resampling.BICUBIC

        return Resampling.LANCZOS

    def _fit_dimensions_to_screen_height(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's height"""
        width: int = round(image_width * (self.screen_height / image_height))
        return (width, self.screen_height)

    def _fit_dimensions_to_screen_width(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's width"""
        height: int = round(image_height * (self.screen_width / image_width))
        return (self.screen_width, height)
