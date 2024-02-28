import os
from time import ctime
from tkinter.messagebox import askyesno, showinfo

from PIL.Image import Image

from util.convert import try_convert_file_and_save_new
from util.image import CachedImage, ImageName
from util.os import OS_name_cmp, clean_str_for_OS_path, truncate_path, walk_dir

if os.name == "nt":
    from send2trash.win.legacy import send2trash
else:
    from send2trash import send2trash


class ImageFileManager:
    """Manages internal list of images"""

    VALID_FILE_TYPES: set[str] = {
        "gif",
        "jpg",
        "jpeg",
        "jpe",
        "jfif",
        "jif",
        "png",
        "webp",
    }

    __slots__ = (
        "_files",
        "_index",
        "cache",
        "current_image",
        "image_directory",
        "path_to_current_image",
    )

    def __init__(self, first_image_to_load: str) -> None:
        """Load single file for display before we load the rest"""

        if not os.path.isfile(first_image_to_load):
            raise ValueError("File doesn't exist or is a directory")

        first_image_data = ImageName(os.path.basename(first_image_to_load))
        if first_image_data.suffix not in self.VALID_FILE_TYPES:
            raise ValueError("File extension not supported")

        self.image_directory: str = os.path.dirname(first_image_to_load)
        self._files: list[ImageName] = [first_image_data]
        self._index: int = 0
        self._update_after_move_or_edit()
        self.cache: dict[str, CachedImage] = {}

    def construct_path_to_image(self, image_name: str) -> str:
        return f"{self.image_directory}/{image_name}"

    def _update_after_move_or_edit(self) -> None:
        """Sets variables about current image.
        Should be called after adding/deleting an image"""
        self.current_image = self._files[self._index]
        self.path_to_current_image = self.construct_path_to_image(
            self.current_image.name
        )

    def fully_load_image_data(self) -> None:
        """Init only loads one file, load entire directory here"""
        image_to_start_at: str = self._files[self._index].name

        VALID_FILE_TYPES = self.VALID_FILE_TYPES
        self._files = [
            image_path
            for path in walk_dir(self.image_directory)
            if (image_path := ImageName(path)).suffix in VALID_FILE_TYPES
        ]

        self._files.sort()
        self._index = self._binary_search(image_to_start_at)
        self._update_after_move_or_edit()

    def refresh_image_list(self) -> None:
        """Clears cache and re-loads current images in direcrory"""
        self.cache = {}
        self.fully_load_image_data()

    def get_cached_details(self) -> str:
        """Returns tuple of current image's dimensions, size, and mode.
        Can raise KeyError on failure to get data"""
        image_info: CachedImage = self.cache[self.current_image.name]

        bpp: int = len(image_info.mode) * 8 if image_info.mode != "1" else 1
        readable_mode: str = {
            "P": "Palette",
            "L": "Grayscale",
            "1": "Black And White",
        }.get(image_info.mode, image_info.mode)

        dimension_text: str = f"Pixels: {image_info.width}x{image_info.height}"
        size_text: str = f"Size: {image_info.size_display}"
        mode_text: str = f"\nPixel Format: {bpp} bpp {readable_mode}"

        return f"{dimension_text}\n{size_text}\n{mode_text}"

    def show_image_details(self, PIL_Image: Image) -> None:
        """Shows a popup with image details"""
        try:
            details: str = f"{self.get_cached_details()}\n"
        except KeyError:
            return  # don't fail trying to read, if not in cache just exit

        try:
            os_info = os.stat(self.path_to_current_image)
            # [4:] chops of 3 character day like Mon/Tue/etc.
            created_time: str = ctime(os_info.st_ctime)[4:]
            last_modifed_time: str = ctime(os_info.st_mtime)[4:]
            details += f"Created: {created_time}\nLast Modified: {last_modifed_time}\n"
        except (OSError, ValueError):
            pass  # don't include if can't get

        # Can add more here, just didn't see any others I felt were important enough
        if comment := PIL_Image.info.get("comment"):
            details += f"Comment: {comment.decode('utf-8')}\n"

        showinfo("Image Details", details)

    def move_index(self, amount: int) -> None:
        """Moves internal index with safe wrap around"""
        self._index = (self._index + amount) % len(self._files)

        self._update_after_move_or_edit()

    def _clear_image_data(self) -> None:
        self.cache.pop(self._files.pop(self._index).name, None)

    def remove_current_image(self, delete_from_disk: bool) -> None:
        """Deletes image from files array, cache, and optionally disk"""
        if delete_from_disk:
            send2trash(os.path.normpath(self.path_to_current_image))
        self._clear_image_data()

        remaining_image_count: int = len(self._files)

        if self._index >= remaining_image_count:
            self._index = remaining_image_count - 1

        # This needs to be after index check if we catch IndexError and add
        # a new image, index will be -1 which works for newly added image
        if remaining_image_count == 0:
            raise IndexError()

        self._update_after_move_or_edit()

    def _ask_to_delete_old_image_after_convert(self, new_format: str) -> bool:
        """Returns True if user agreed to delete"""
        if askyesno(
            "Confirm deletion",
            f"Converted file to {new_format}, delete old file?",
        ):
            try:
                self.remove_current_image(True)
            except IndexError:
                pass  # even if no images left, a new one will be added after this
            return True
        return False

    def _construct_path_for_rename(self, new_dir: str, new_name: str) -> str:
        """Makes new path with validations when moving between directories"""
        will_move_dirs: bool = new_dir != ""
        new_full_path: str
        if will_move_dirs:
            if not os.path.isabs(new_dir):
                new_dir = os.path.join(self.image_directory, new_dir)
            new_dir = truncate_path(new_dir)
            if not os.path.exists(new_dir):
                raise OSError()
            new_full_path = os.path.join(new_dir, new_name)
        else:
            new_full_path = self.construct_path_to_image(new_name)

        if os.path.exists(new_full_path):
            raise FileExistsError()

        if will_move_dirs and not askyesno(
            "Confirm move",
            f"Move file to {new_dir} ?",
        ):
            raise Exception()

        return new_full_path

    def _split_dir_and_name(self, new_name_or_path: str) -> tuple[str, str]:
        """Returns tuple with path and file name split up"""
        new_name: str = (
            clean_str_for_OS_path(os.path.basename(new_name_or_path))
            or self.current_image.name
        )
        new_dir: str = os.path.dirname(new_name_or_path)

        if new_name == "." or new_name == "..":
            # name is acutally path specifier
            new_dir = os.path.join(new_dir, new_name)
            new_name = self.current_image.name

        return new_dir, new_name

    def rename_or_convert_current_image(self, new_name_or_path: str) -> None:
        """Try to either rename or convert based on input"""
        new_dir, new_name = self._split_dir_and_name(new_name_or_path)

        new_image_data = ImageName(new_name)
        if new_image_data.suffix not in self.VALID_FILE_TYPES:
            new_name += f".{self.current_image.suffix}"
            new_image_data = ImageName(new_name)

        new_full_path: str = self._construct_path_for_rename(new_dir, new_name)

        preserve_index: bool = False
        if (
            new_image_data.suffix != self.current_image.suffix
            and try_convert_file_and_save_new(
                self.path_to_current_image,
                new_full_path,
                new_image_data.suffix,
            )
        ):
            # If not, we need to preserve index since the # of files will increase,
            # possibly moving index away from the displayed image
            preserve_index = not self._ask_to_delete_old_image_after_convert(
                new_image_data.suffix
            )
        else:
            os.rename(self.path_to_current_image, new_full_path)
            self._clear_image_data()

        # Only add image if its still in the same directory
        if os.path.dirname(new_full_path) == os.path.dirname(
            self.path_to_current_image
        ):
            self.add_new_image(new_name, preserve_index)
        else:
            self._update_after_move_or_edit()

    def add_new_image(self, new_name: str, preserve_index: bool) -> None:
        """Adds a new image to the image list
        preserve_index: try to keep index at the same image it was before adding"""
        image_data = ImageName(new_name)
        insert_index: int = self._binary_search(image_data.name)
        self._files.insert(insert_index, image_data)
        if preserve_index and insert_index <= self._index:
            self._index += 1
        self._update_after_move_or_edit()

    def cache_image(self, cached_image: CachedImage) -> None:
        self.cache[self.current_image.name] = cached_image

    def current_image_cache_still_fresh(self) -> bool:
        """Returns True when it seems the cached image is still accurate.
        Not guaranteed to be correct, but thats not important for this case"""
        try:
            return (
                os.stat(self.path_to_current_image).st_size
                == self.cache[self.current_image.name].size_in_kb
            )
        except (OSError, ValueError, KeyError):
            return False

    def get_current_image_cache(self) -> CachedImage | None:
        return self.cache.get(self.current_image.name)

    def _binary_search(self, target_image: str) -> int:
        """Finds index of target_image in internal list"""
        files = self._files
        low: int = 0
        high: int = len(files) - 1
        while low <= high:
            mid: int = (low + high) >> 1
            current_image = files[mid].name
            if target_image == current_image:
                return mid
            if OS_name_cmp(target_image, current_image):
                high = mid - 1
            else:
                low = mid + 1
        return low
