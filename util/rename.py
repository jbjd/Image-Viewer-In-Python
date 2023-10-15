import os
from PIL.Image import Image, open as open_image

from image import ImagePath


def try_convert_file_and_save_new(
    old_image: Image,
    old_path: str,
    old_image_data: ImagePath,
    new_path: str,
    new_image_data: ImagePath,
) -> bool:
    """
    Closes image and reopens it for safety, thens trys to convert to new file format.
    return: if file was converted and a new file was created"""
    _prepare_to_rename(new_path, old_image)

    with open(old_path, mode="rb") as fp:
        with open_image(fp) as temp_img:
            # refuse to convert animations other than to webp
            is_animated: bool = getattr(temp_img, "n_frames", 1) > 1
            if is_animated and new_image_data.suffix != ".webp":
                raise ValueError()

            match new_image_data.suffix:
                case ".webp":
                    temp_img.save(
                        new_path, "WebP", quality=100, method=6, save_all=is_animated
                    )
                case ".png":
                    temp_img.save(new_path, "PNG", optimize=True)
                case ".bmp":
                    temp_img.save(new_path, "BMP")
                case ".jpg" | ".jpeg" | ".jif" | ".jfif" | ".jpe":
                    # if two different JPEG varients
                    if old_image_data.suffix[1] == "j":
                        return False
                    temp_img.save(new_path, "JPEG", optimize=True, quality=100)
                case _:
                    return False

            fp.flush()

    return True


def rename_image(old_image: Image, old_path: str, new_path: str) -> None:
    _prepare_to_rename(new_path, old_image)
    os.rename(old_path, new_path)


def _prepare_to_rename(path: str, old_image: Image) -> None:
    """Errors if path already exists.
    Then closes old image to prepare for rename"""
    if os.path.isfile(path) or os.path.isdir(path):
        raise FileExistsError()
    old_image.close()
