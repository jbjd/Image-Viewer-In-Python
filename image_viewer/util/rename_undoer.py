from collections import deque
from typing import NamedTuple
import os


if os.name == "nt":
    from winshell import undelete
    from send2trash.win.legacy import send2trash
else:
    from util.os import undelete
    from send2trash import send2trash


class RenameResult(NamedTuple):
    file_type_converted: bool
    preserve_index: bool


class _Rename(NamedTuple):
    """Class used for storage within this file"""

    original_name: str
    new_name: str
    old_file_deleted: bool
    file_type_converted: bool


class RenameUndoer:
    """Keeps information on recent file renames and optionally undoes them"""

    def __init__(self) -> None:
        self._stack: deque[_Rename] = deque(maxlen=4)

    def append(
        self, original_name: str, new_name: str, rename_result: RenameResult
    ) -> None:
        # File was deleted if file was converted and index did not need to be preserved
        old_file_deleted: bool = (
            rename_result.file_type_converted and not rename_result.preserve_index
        )
        self._stack.append(
            _Rename(
                original_name,
                new_name,
                old_file_deleted,
                rename_result.file_type_converted,
            )
        )

    def undo(self) -> tuple[str, str]:
        """returns tuple of image to add, image to remove, if any"""
        original_name, new_name, old_file_deleted, file_type_converted = (
            self._stack.pop()
        )
        # file was not converted -> try rename to its previous name
        if not file_type_converted:
            try:
                os.rename(new_name, original_name)
            except OSError:
                return ("", "")
            return (original_name, new_name)
        elif not old_file_deleted:
            send2trash(os.path.normpath(new_name))

            return ("", new_name)
        else:
            raise NotImplementedError

        return ("", "")

    def get_last_undoable_action(self) -> str:
        """Looks at top of deque and formats the information in a str"""
        original_name, new_name, old_file_deleted, file_type_converted = self._stack[-1]

        if not file_type_converted:
            return f"Rename {new_name} back to {original_name}?"
        elif not old_file_deleted:
            return f"Delete {new_name}?"
        else:
            return f"Delete {new_name} and restore {original_name} from trash?"
