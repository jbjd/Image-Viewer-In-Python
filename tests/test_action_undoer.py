from unittest.mock import patch

import pytest

# Hack: Importing the Undo types from their original file
# Breaks type()/isinstance() since python sees different import paths
# One starting with image_viewer.action..., the other just action...
# But importing the imported types in the undoer file works
from image_viewer.actions.undoer import (
    ActionUndoer,
    Convert,
    Delete,
    FileAction,
    Rename,
    UndoResponse,
)

MODULE_PATH = "image_viewer.actions"


@pytest.fixture
def action_undoer() -> ActionUndoer:
    return ActionUndoer()


def test_cap():
    """Test that last X actions are preserved"""
    action_undoer = ActionUndoer(maxlen=4)

    action_undoer.append(Rename("This will get", "thrown out"))
    action_undoer.append(Rename("", ""))
    action_undoer.append(Convert("", "", False))
    action_undoer.append(Convert("", "", True))
    action_undoer.append(Delete(""))

    assert len(action_undoer) == 4


@pytest.mark.parametrize(
    "action",
    [
        (Delete("original_path")),
        (Convert("original_path", "new_path", original_file_deleted=True)),
        (Convert("original_path", "new_path", original_file_deleted=False)),
        (Rename("original_path", "new_path")),
    ],
)
def test_undo_action(action_undoer: ActionUndoer, action: FileAction):
    action_undoer.append(action)
    assert action_undoer.get_undo_message()

    with (
        patch(f"{MODULE_PATH}.undoer.trash_file") as mock_trash,
        patch(f"{MODULE_PATH}.undoer.restore_from_bin") as mock_undelete,
        patch(f"{MODULE_PATH}.undoer.os.rename") as mock_rename,
    ):
        undo_response: UndoResponse = action_undoer.undo()
        _assert_correct_undo_response(action, undo_response)

        if type(action) is Delete or (
            type(action) is Convert and action.original_file_deleted
        ):
            mock_undelete.assert_called_once()
        else:
            mock_undelete.assert_not_called()

        if type(action) is Convert:
            mock_trash.assert_called_once()
        else:
            mock_trash.assert_not_called()

        if type(action) is Rename:
            mock_rename.assert_called_once()
        else:
            mock_rename.assert_not_called()


def _assert_correct_undo_response(action: FileAction, undo_response: UndoResponse):
    if type(action) is Delete:
        assert not undo_response.path_removed
    else:
        assert undo_response.path_removed

    if type(action) is Convert and not action.original_file_deleted:
        assert not undo_response.path_restored
    else:
        assert undo_response.path_restored
