from abc import ABC


class FileEvent(ABC):
    """Class used to track actions done to a file"""

    __slots__ = ("original_path",)

    def __init__(self, original_path: str) -> None:
        self.original_path: str = original_path


class Rename(FileEvent):
    """Represents a file path changing"""

    __slots__ = ("new_path", "original_file_deleted")

    def __init__(
        self, original_path: str, new_path: str, original_file_deleted: bool = False
    ) -> None:
        super().__init__(original_path)
        self.new_path: str = new_path
        self.original_file_deleted: bool = original_file_deleted


class Convert(Rename):
    """Represents a convertion done to a file such that a new path exists,
    but it is related to the old path. Such as converting an image where both
    the old and converted image now exist"""

    __slots__ = ()


class Delete(FileEvent):
    """Represents a file being deleted and sent to the recylce bin"""

    __slots__ = ()


class Edit(FileEvent):
    """Represent an image file being edited such that its path stays the same,
    but the underlying image had its bytes altered"""

    __slots__ = ("edit_performed", "original_bytes")

    def __init__(
        self, original_path: str, edit_performed: str, original_bytes: bytes
    ) -> None:
        super().__init__(original_path)
        self.edit_performed: str = edit_performed
        self.original_bytes: bytes = original_bytes