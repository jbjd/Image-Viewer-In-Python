"""
Classes representing actions and a class that handles undoing them
"""

import os
from collections import deque

from actions.types import Convert, Delete, Edit, FileEvent, Rename
from util.os import restore_from_bin, trash_file


class ActionUndoer(deque[FileEvent]):
    """Keeps information on recent file actions and can undo them"""

    __slots__ = ()

    def __init__(self, maxlen: int = 4) -> None:
        super().__init__(maxlen=maxlen)

    def undo(self) -> tuple[str, str]:
        """Returns tuple of image to add, image to remove, if any"""
        action: FileEvent = self.pop()

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

        elif type(action) is Edit:

            with open(action.original_path, "wb") as fp:
                fp.write(action.original_bytes)
            return ("", "")

        else:
            assert False  # Unreachable

    def get_undo_message(self) -> str:
        """Looks at top of deque and formats the information in a string.
        Throws IndexError when empty"""
        action: FileEvent = self[-1]

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
        elif type(action) is Edit:
            return f"Undo {action.edit_performed} on {action.original_path}?"
        else:
            assert False  # Unreachable