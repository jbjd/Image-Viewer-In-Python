import os
from abc import ABC
from collections import deque

from util.os import restore_from_bin, trash_file


class FileAction(ABC):
    """Class used to track actions done to a file"""

    __slots__ = "original_path"

    def __init__(self, original_path: str) -> None:
        self.original_path: str = original_path


class Rename(FileAction):
    """Any actions that results in the path of a file being changed"""

    __slots__ = "new_path", "original_file_deleted"

    def __init__(
        self, original_path: str, new_path: str, original_file_deleted: bool = False
    ) -> None:
        super().__init__(original_path)
        self.new_path: str = new_path
        self.original_file_deleted: bool = original_file_deleted


class Convert(Rename):
    """Convert action"""

    __slots__ = ()


class Delete(FileAction):
    """Delete action"""

    __slots__ = ()


class Rotate(FileAction):
    """Delete action"""

    __slots__ = "original_bytes"

    def __init__(self, original_path: str, original_bytes: bytes) -> None:
        super().__init__(original_path)
        self.original_bytes: bytes = original_bytes


class ActionUndoer(deque[FileAction]):
    """Keeps information on recent file actions and can undo them"""

    __slots__ = ()

    def __init__(self, maxlen: int = 4) -> None:
        super().__init__(maxlen=maxlen)

    def undo(self) -> tuple[str, str]:
        """Returns tuple of image to add, image to remove, if any"""
        action: FileAction = self.pop()

        if type(action) is Rename:

            os.rename(action.new_path, action.original_path)
            return (action.original_path, action.new_path)

        elif type(action) is Convert and action.original_file_deleted:

            restore_from_bin(action.original_path)
            trash_file(action.new_path)
            return (action.original_path, action.new_path)

        elif type(action) is Convert:

            trash_file(action.new_path)
            return ("", action.new_path)

        elif type(action) is Delete:

            restore_from_bin(action.original_path)
            return (action.original_path, "")

        elif type(action) is Rotate:

            with open(action.original_path, "wb") as fp:
                fp.write(action.original_bytes)
            return ("", "")

        else:
            assert False  # Unreachable

    def get_undo_message(self) -> str:
        """Looks at top of deque and formats the information in a string.
        Throws IndexError when empty"""
        action: FileAction = self[-1]

        if type(action) is Rename:
            return f"Rename {action.new_path} back to {action.original_path}?"
        elif type(action) is Convert and action.original_file_deleted:
            return (
                f"Delete {action.new_path} and restore {action.original_path}"
                " from trash?"
            )
        elif type(action) is Convert:
            return f"Delete {action.new_path}?"
        elif type(action) is Delete:
            return f"Restore {action.original_path} from trash?"
        elif type(action) is Rotate:
            return f"Undo rotation on {action.original_path}?"
        else:
            assert False  # Unreachable
