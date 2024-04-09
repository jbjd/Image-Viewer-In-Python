"""
Deals with converting between image file types
"""

from PIL.Image import open as open_image

from util.image import magic_number_guess


def try_convert_file_and_save_new(
    old_path: str, new_path: str, target_ext: str
) -> bool:
    """Tries to convert to new file format.
    Raises ValueError if converting animated file to non-animated format
    Returns bool if conversion performed, false when converting to the same type
    """
    with open(old_path, "rb") as fp:
        original_ext: str = magic_number_guess(fp.read(4))[0]

        # If trying to convert to same ext, no conversion needed
        # Only first letter checked here so jpeg is considered the same as jpg and so on
        if target_ext[0] == original_ext[0].lower():
            return False

        with open_image(fp) as temp_img:
            is_animated: bool = getattr(temp_img, "is_animated", False)
            if is_animated and target_ext not in ("webp", "gif", "png"):
                raise ValueError

            match target_ext:
                case "webp" | "png":
                    pass  # don't hit default case of return False
                case "jpg" | "jpeg" | "jif" | "jfif" | "jpe":
                    target_ext = "JPEG"
                    if temp_img.mode != "RGB":
                        temp_img = temp_img.convert("RGB")  # must be RGB to save as jpg
                case "gif":
                    # This pop fixes missing bitmap error during webp -> gif conversion
                    temp_img.info.pop("background", None)
                case _:
                    return False

            temp_img.save(
                new_path,
                target_ext,
                quality=100,
                method=6,
                optimize=True,
                save_all=is_animated,
            )

    return True
