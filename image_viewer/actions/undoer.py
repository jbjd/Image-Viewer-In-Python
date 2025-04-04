"""
Classes representing actions and a class that handles undoing them
"""

import os
from collections import deque

from actions.types import Convert, Delete, FileAction, Rename
from util.os import restore_from_bin, trash_file


class UndoResponse:
    """Response when a file action in undone, contains what paths have been edited
    so caller can deal with determining if display needs updating"""

    __slots__ = ("path_to_restore", "path_to_remove")

    def __init__(self, path_to_restore: str, path_to_remove: str) -> None:
        self.path_to_restore: str = path_to_restore
        self.path_to_remove: str = path_to_remove


class ActionUndoer(deque[FileAction]):
    """Keeps information on recent file actions and can undo them"""

    __slots__ = ()

    def __init__(self, maxlen: int = 4) -> None:
        super().__init__(maxlen=maxlen)

    def undo(self) -> UndoResponse:
        """Returns tuple of image to add, image to remove, if any"""
        action: FileAction = self.pop()

        if type(action) is Rename:

            os.rename(action.new_path, action.original_path)
            return UndoResponse(action.original_path, action.new_path)

        if type(action) is Convert and action.original_file_deleted:

            restore_from_bin(action.original_path)
            trash_file(action.new_path)
            return UndoResponse(action.original_path, action.new_path)

        if type(action) is Convert:

            trash_file(action.new_path)
            return UndoResponse("", action.new_path)

        if type(action) is Delete:

            restore_from_bin(action.original_path)
            return UndoResponse(action.original_path, "")

        assert False  # Unreachable

    def get_undo_message(self) -> str:
        """Looks at top of deque and formats the information in a string.
        Throws IndexError when empty"""
        action: FileAction = self[-1]

        if type(action) is Rename:
            return f"Rename {action.new_path} back to {action.original_path}?"
        if type(action) is Convert and action.original_file_deleted:
            return (
                f"Delete {action.new_path} and restore {action.original_path}"
                " from trash?"
            )
        if type(action) is Convert:
            return f"Delete {action.new_path}?"
        if type(action) is Delete:
            return f"Restore {action.original_path} from trash?"

        assert False  # Unreachable
