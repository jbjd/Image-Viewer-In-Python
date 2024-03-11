import os
from abc import ABC
from collections import deque

from util.os import restore_from_bin, trash_file


class Action(ABC):
    """Class used to track actions done to a file"""

    __slots__ = "original_path"

    def __init__(self, original_path: str) -> None:
        self.original_path: str = original_path


class Rename(Action):
    """One class for rename/convert since this program handles them very closely"""

    __slots__ = "new_path", "preserve_index"

    def __init__(
        self, original_path: str, new_path: str, preserve_index: bool = False
    ) -> None:
        super().__init__(original_path)
        self.new_path: str = new_path
        self.preserve_index: bool = preserve_index


class Convert(Rename):
    """Convert action"""

    __slots__ = "old_file_deleted"

    def __init__(
        self, original_path: str, new_path: str, old_file_deleted: bool
    ) -> None:
        super().__init__(original_path, new_path, not old_file_deleted)
        self.old_file_deleted: bool = old_file_deleted


class Delete(Action):
    """Delete action"""

    __slots__ = ()


class ActionUndoer:
    """Keeps information on recent file actions and can undo them"""

    __slots__ = "_stack"

    def __init__(self) -> None:
        self._stack: deque[Action] = deque(maxlen=4)

    def append(self, action: Action) -> None:
        self._stack.append(action)

    def undo(self) -> tuple[str, str]:
        """returns tuple of image to add, image to remove, if any"""
        action: Action = self._stack.pop()

        if type(action) is Rename:

            os.rename(action.new_path, action.original_path)
            return (action.original_path, action.new_path)

        elif type(action) is Convert and action.old_file_deleted:

            restore_from_bin(action.original_path)
            trash_file(action.new_path)
            return (action.original_path, action.new_path)

        elif type(action) is Convert:

            trash_file(action.new_path)
            return ("", action.new_path)

        else:  # Delete

            restore_from_bin(action.original_path)
            return (action.original_path, "")

    def get_last_undoable_action(self) -> str:
        """Looks at top of deque and formats the information in a str"""
        action: Action = self._stack[-1]

        if type(action) is Rename:
            return f"Rename {action.new_path} back to {action.original_path}?"
        elif type(action) is Convert and action.old_file_deleted:
            return (
                f"Delete {action.new_path} and restore {action.original_path}"
                " from trash?"
            )
        elif type(action) is Convert:
            return f"Delete {action.new_path}?"
        else:  # Delete
            return f"Restore {action.original_path} from trash?"
