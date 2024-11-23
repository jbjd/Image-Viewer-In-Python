"""
Deals with converting between image file types
"""

from PIL.Image import open as open_image

from constants import VALID_FILE_TYPES
from util.image import magic_number_guess
from util.PIL import image_is_animated, save_image


def try_convert_file_and_save_new(
    old_path: str, new_path: str, target_format: str
) -> bool:
    """Tries to convert image at old_path to a target format saved at new_path.
    Raises ValueError if converting animated file to non-animated format.

    Returns True if conversion performed,
    False if converting to the same type or invalid format
    """
    target_format = target_format.lower()

    if target_format not in VALID_FILE_TYPES:
        return False

    with open(old_path, "rb") as fp:
        original_ext: str = magic_number_guess(fp.read(4))

        # Only first letter checked since jpeg is the only supported file extension
        # that has multiple variations and all start with 'j'
        if target_format[0] == original_ext[0].lower():
            return False

        with open_image(fp) as temp_img:
            is_animated: bool = image_is_animated(temp_img)
            if is_animated and target_format not in ("webp", "gif", "png"):
                raise ValueError

            match target_format:
                case "jpg" | "jpeg" | "jif" | "jfif" | "jpe":
                    target_format = "jpeg"
                    if temp_img.mode != "RGB":
                        temp_img = temp_img.convert("RGB")  # must be RGB to save as jpg
                case "gif":
                    # This pop fixes missing bitmap error during webp -> gif conversion
                    temp_img.info.pop("background", None)

            save_image(
                temp_img,
                new_path,
                target_format,
                is_animated=is_animated,
            )

    return True
