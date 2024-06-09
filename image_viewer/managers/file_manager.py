import os
from os import stat_result
from time import ctime
from tkinter.messagebox import askyesno, showinfo

from PIL.Image import Image

from constants import Rotation
from helpers.action_undoer import ActionUndoer, Convert, Delete, Rename, Rotate
from helpers.file_dialog_asker import FileDialogAsker
from util.convert import try_convert_file_and_save_new
from util.image import CachedImage, ImageCache, ImageName, ImageNameList
from util.os import clean_str_for_OS_path, get_dir_name, trash_file, walk_dir
from util.PIL import rotate_image, save_image


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
        "action_undoer",
        "current_image",
        "file_dialog_asker",
        "image_cache",
        "image_directory",
        "path_to_image",
    )

    def __init__(self, first_image_path: str, image_cache: ImageCache) -> None:
        """Load single file for display before we load the rest"""

        first_image_name: ImageName = self._make_name_with_validation(first_image_path)
        self.image_directory: str = get_dir_name(first_image_path)

        self.image_cache: ImageCache = image_cache

        self.action_undoer: ActionUndoer = ActionUndoer()
        self.file_dialog_asker: FileDialogAsker = FileDialogAsker(self.VALID_FILE_TYPES)
        self._files: ImageNameList = ImageNameList([first_image_name])

        self.current_image: ImageName
        self.path_to_image: str
        self._update_after_move_or_edit()

    def _make_name_with_validation(self, path: str) -> ImageName:
        """Makes ImageName out of path. Raises ValueError if path is invalid"""
        image_name = ImageName(os.path.basename(path))
        if not os.path.isfile(path) or image_name.suffix not in self.VALID_FILE_TYPES:
            raise ValueError

        return image_name

    def move_to_new_directory(self) -> bool:
        """Asks user new image to go to and move to that image's directory
        Returns True if moving to new directory succeeded"""
        new_file_path: str = self.file_dialog_asker.ask_open_image(self.image_directory)
        if new_file_path == "":
            return False

        choosen_file: str = os.path.basename(new_file_path)
        new_dir: str = get_dir_name(new_file_path)

        if new_dir != self.image_directory:
            self.image_directory = new_dir
            self.find_all_images()

        index: int
        found: bool
        index, found = self._files.binary_search(choosen_file)
        self._files.display_index = index
        if not found:
            self.add_new_image(choosen_file, index=index)
        else:
            self._update_after_move_or_edit()

        return True

    def get_path_to_image(self, image_name: str | None = None) -> str:
        """Returns full path to image, defaulting to the current image displayed"""
        if image_name is None:
            image_name = self.current_image.name

        return f"{self.image_directory}/{image_name}"

    def _update_after_move_or_edit(self) -> None:
        """Sets variables about current image.
        Should be called after adding/deleting an image"""
        self.current_image = self._files.get_current_image()
        self.path_to_image = self.get_path_to_image()

    def find_all_images(self) -> None:
        """Init only loads one file, load entire directory here"""
        image_to_start_at: str = self._files.get_current_image().name

        VALID_FILE_TYPES = self.VALID_FILE_TYPES
        self._files = ImageNameList(
            [
                image_path
                for path in walk_dir(self.image_directory)
                if (image_path := ImageName(path)).suffix in VALID_FILE_TYPES
            ]
        )

        self._files.sort_and_preserve_index(image_to_start_at)
        self._update_after_move_or_edit()

    def refresh_image_list(self) -> None:
        """Clears cache and re-loads current images in direcrory"""
        self.image_cache.clear()
        self.find_all_images()

    def get_cached_details(self) -> str:
        """Returns tuple of current image's dimensions, size, and mode.
        Can raise KeyError on failure to get data"""
        image_info: CachedImage = self.image_cache[self.path_to_image]

        mode: str = image_info.mode
        bpp: int = len(mode) * 8 if mode != "1" else 1
        readable_mode: str = {
            "P": "Palette",
            "L": "Grayscale",
            "1": "Black And White",
        }.get(mode, mode)

        text: str = (
            f"Pixels: {image_info.width}x{image_info.height}\n"
            f"Size: {image_info.size_display}\n"
            f"Pixel Format: {bpp} bpp {readable_mode}\n"
        )
        return text

    def show_image_detail_popup(self, PIL_Image: Image) -> None:
        try:
            details: str = self.get_cached_details()
        except KeyError:
            return  # don't fail trying to read, if not in cache just exit

        try:
            image_metadata: stat_result = os.stat(self.path_to_image)
            # [4:] chops of 3 character day like Mon/Tue/etc.
            created_time: str = ctime(image_metadata.st_ctime)[4:]
            last_modifed_time: str = ctime(image_metadata.st_mtime)[4:]
            details += f"Created: {created_time}\nLast Modified: {last_modifed_time}\n"
        except (OSError, ValueError):
            pass  # don't include if can't get

        # Can add more here, just didn't see any others I felt were important enough
        comment: bytes | None = PIL_Image.info.get("comment")
        if comment:
            details += f"Comment: {comment.decode('utf-8')}\n"

        showinfo("Image Details", details)

    def move_index(self, amount: int) -> None:
        """Moves internal index with safe wrap around"""
        self._files.move_index(amount)
        self._update_after_move_or_edit()

    def delete_current_image(self) -> None:
        """Safely deletes the image at the current file path"""
        try:
            trash_file(self.path_to_image)
            self.action_undoer.append(Delete(self.path_to_image))
        except (OSError, FileNotFoundError):
            pass
        self.remove_current_image()

    def remove_current_image(self) -> None:
        """Deletes image from files array, cache, and optionally disk"""
        self._clear_current_image_data()
        self._update_after_move_or_edit()

    def _clear_current_image_data(self) -> None:
        try:
            self._files.pop_current_image()
        except IndexError:
            pass
        self.image_cache.pop_safe(self.path_to_image)

    def _clear_image_data(self, index: int) -> None:
        deleted_name: str = self._files.pop(index).name
        key: str = self.get_path_to_image(deleted_name)
        self.image_cache.pop_safe(key)

    def rename_or_convert_current_image(self, new_name_or_path: str) -> None:
        """Try to either rename or convert based on input"""
        new_dir: str
        new_name: str
        new_dir, new_name = self._split_dir_and_name(new_name_or_path)

        new_image_name: ImageName = ImageName(new_name)
        if new_image_name.suffix not in self.VALID_FILE_TYPES:
            new_name += f".{self.current_image.suffix}"
            new_image_name = ImageName(new_name)

        original_path: str = self.path_to_image
        new_path: str = self._construct_path_for_rename(new_dir, new_image_name.name)

        result: Rename
        if (
            new_image_name.suffix != self.current_image.suffix
            and try_convert_file_and_save_new(
                original_path, new_path, new_image_name.suffix
            )
        ):
            result = self._ask_to_delete_old_image_after_convert(
                original_path, new_path, new_image_name.suffix
            )
        else:
            result = self._rename(original_path, new_path)

        self.action_undoer.append(result)

        # Only add image if its still in the directory we are currently in
        if get_dir_name(new_path) == get_dir_name(original_path):
            preserve_index: bool = self._should_perserve_index(result)
            self.add_new_image(new_name, preserve_index)
        else:
            self._update_after_move_or_edit()

    def _split_dir_and_name(self, new_name_or_path: str) -> tuple[str, str]:
        """Returns tuple with path and file name split up"""
        new_name: str = (
            clean_str_for_OS_path(os.path.basename(new_name_or_path))
            or self.current_image.name
        )
        new_dir: str = get_dir_name(new_name_or_path)

        if new_name == "." or new_name == "..":
            # name is actually path specifier
            new_dir = os.path.normpath(os.path.join(new_dir, new_name))
            new_name = self.current_image.name

        return new_dir, new_name

    def _construct_path_for_rename(self, new_dir: str, new_name: str) -> str:
        """Makes new path with validations when moving between directories"""
        will_move_dirs: bool = new_dir != ""

        new_full_path: str
        if will_move_dirs:
            if not os.path.isabs(new_dir):
                new_dir = os.path.normpath(os.path.join(self.image_directory, new_dir))
            if not os.path.exists(new_dir):
                raise OSError
            new_full_path = os.path.join(new_dir, new_name)
        else:
            new_full_path = self.get_path_to_image(new_name)

        if os.path.exists(new_full_path):
            raise FileExistsError

        if will_move_dirs and not askyesno(
            "Confirm move",
            f"Move file to {new_dir} ?",
        ):
            raise OSError

        return new_full_path

    def _ask_to_delete_old_image_after_convert(
        self, original_path: str, new_full_path: str, new_format: str
    ) -> Convert:
        """Asks user to delete old file and returns Convert result"""
        deleted: bool = False

        if askyesno(
            "Confirm deletion",
            f"Converted file to {new_format}, delete old file?",
        ):
            try:
                self.delete_current_image()
            except IndexError:
                pass  # even if no images left, a new one will be added after this
            deleted = True

        return Convert(original_path, new_full_path, deleted)

    def _rename(self, original_path: str, new_full_path: str) -> Rename:
        """Renames a file and returns the rename result"""
        os.rename(original_path, new_full_path)
        self._clear_current_image_data()
        return Rename(original_path, new_full_path)

    @staticmethod
    def _should_perserve_index(result: Rename) -> bool:
        """Returns True when image list shifted or changed size so internal index
        needs to be changed to keep on the same image"""
        if isinstance(result, Convert):
            return not result.original_file_deleted

        return False

    def add_new_image(
        self, new_name: str, preserve_index: bool = False, index: int = -1
    ) -> None:
        """Adds a new image to the image list
        preserve_index: try to keep index at the same image it was before adding"""
        image_name: ImageName = ImageName(new_name)
        if index < 0:
            index, _ = self._files.binary_search(image_name.name)

        self._files.insert(index, image_name)
        if preserve_index and index <= self._files.display_index:
            self._files.move_index(1)
        self._update_after_move_or_edit()

    def undo_rename_or_convert(self) -> bool:
        """Undoes most recent rename/convert
        returns if screen needs a refresh"""
        if not self._ask_undo_last_action():
            return False

        image_to_add_path: str
        image_to_remove_path: str
        try:
            image_to_add_path, image_to_remove_path = self.action_undoer.undo()
        except OSError:
            return False  # TODO: error popup?

        image_to_add: str = os.path.basename(image_to_add_path)
        image_to_remove: str = os.path.basename(image_to_remove_path)

        if image_to_remove != "":
            index: int
            found: bool
            index, found = self._files.binary_search(image_to_remove)
            if found:
                self._clear_image_data(index)

        if image_to_add != "":
            preserve_index: bool = image_to_remove == ""
            self.add_new_image(image_to_add, preserve_index)
        else:
            self._update_after_move_or_edit()

        return True

    def _ask_undo_last_action(self) -> bool:
        """Returns if user wants to + can undo last action"""
        try:
            undo_message: str = self.action_undoer.get_undo_message()
        except IndexError:
            return False  # There was no action to undo

        return askyesno("Undo Rename/Convert", undo_message)

    def current_image_cache_still_fresh(self) -> bool:
        """Checks if cache for currently displayed image is still up to date"""
        return self.image_cache.image_cache_still_fresh(self.path_to_image)

    def rotate_image_and_save(self, image: Image, angle: Rotation) -> None:
        """Rotates and saves updated image on disk"""
        rotated_image: Image = rotate_image(image, angle)
        path: str = self.get_path_to_image()

        with open(path, "rb") as fp:
            original_bytes: bytes = fp.read()

        self.action_undoer.append(Rotate(path, original_bytes))

        with open(path, "wb") as fp:
            save_image(rotated_image, fp)
