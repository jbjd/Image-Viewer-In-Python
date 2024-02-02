from os.path import exists

from PIL.Image import open as open_image

from util.image import ImagePath


def try_convert_file_and_save_new(
    old_path: str,
    old_image_data: ImagePath,
    new_path: str,
    new_image_data: ImagePath,
) -> bool:
    """Trys to convert to new file format.
    Return: bool if file was converted and a new file was created"""

    if exists(new_path):
        raise FileExistsError()

    with open_image(old_path) as temp_img:
        is_animated: bool = getattr(temp_img, "is_animated", False)
        if is_animated and new_image_data.suffix not in (".webp", ".gif", ".png"):
            raise ValueError()

        match new_image_data.suffix:
            case ".webp":
                temp_img.save(
                    new_path, "WEBP", quality=100, method=6, save_all=is_animated
                )
            case ".png":
                temp_img.save(new_path, "PNG", optimize=True, save_all=is_animated)
            case ".jpg" | ".jpeg" | ".jif" | ".jfif" | ".jpe":
                # if two different JPEG varients
                if old_image_data.suffix[1] == "j":
                    return False
                if temp_img.mode != "RGB":
                    temp_img = temp_img.convert("RGB")
                temp_img.save(new_path, "JPEG", optimize=True, quality=100)
            case ".gif":
                # This pop fixes missing bitmap error during webp -> gif conversion
                temp_img.info.pop("background", None)
                temp_img.save(new_path, "GIF", save_all=is_animated)
            case _:
                return False

    return True
