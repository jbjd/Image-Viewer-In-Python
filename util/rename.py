from PIL.Image import open as open_image

from image import ImagePath


def try_convert_file_and_save_new(
    old_path: str,
    old_image_data: ImagePath,
    new_path: str,
    new_image_data: ImagePath,
) -> bool:
    """
    Closes image and reopens it for safety, thens trys to convert to new file format.
    return: if file was converted and a new file was created"""

    with open(old_path, mode="rb") as fp:
        with open_image(fp) as temp_img:
            # refuse to convert animations other than to webp
            is_animated: bool = getattr(temp_img, "n_frames", 1) > 1
            if is_animated and new_image_data.suffix not in (".webp", ".gif", ".png"):
                raise ValueError()

            match new_image_data.suffix:
                case ".webp":
                    temp_img.save(
                        new_path, "WEBP", quality=100, method=6, save_all=is_animated
                    )
                case ".png":
                    temp_img.save(new_path, "PNG", optimize=True)
                case ".bmp":
                    temp_img.save(new_path, "BMP")
                case ".jpg" | ".jpeg" | ".jif" | ".jfif" | ".jpe":
                    # if two different JPEG varients
                    if old_image_data.suffix[1] == "j":
                        return False
                    if temp_img.mode == "RGBA":
                        temp_img = temp_img.convert("RGB")
                    temp_img.save(new_path, "JPEG", optimize=True, quality=100)
                case ".gif":
                    temp_img.save(new_path, "GIF", save_all=is_animated)
                case _:
                    return False

            fp.flush()

    return True
