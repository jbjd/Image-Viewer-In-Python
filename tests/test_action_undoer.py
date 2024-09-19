from unittest.mock import mock_open, patch

import pytest

from image_viewer.helpers.action_undoer import (
    ActionUndoer,
    Convert,
    Delete,
    Rename,
    Rotate,
)


@pytest.fixture
def action_undoer() -> ActionUndoer:
    return ActionUndoer()


def test_cap(action_undoer: ActionUndoer):
    """Test all 3 undoable actions"""

    action_undoer.append(Rename("This will get", "thrown out"))
    action_undoer.append(Rename("", ""))
    action_undoer.append(Convert("", "", False))
    action_undoer.append(Convert("", "", True))
    action_undoer.append(Delete(""))

    assert len(action_undoer) == 4  # maxlen is 4, 1st append is removed


def test_undo_delete(action_undoer: ActionUndoer):
    action_undoer.append(Delete("test"))

    with patch("image_viewer.helpers.action_undoer.restore_from_bin") as mock_undelete:
        assert action_undoer.get_undo_message()
        assert action_undoer.undo() == ("test", "")
        mock_undelete.assert_called_once()


def test_undo_convert_with_deletion(action_undoer: ActionUndoer):
    action_undoer.append(Convert("old", "new", True))

    with (
        patch("image_viewer.helpers.action_undoer.trash_file") as mock_trash,
        patch("image_viewer.helpers.action_undoer.restore_from_bin") as mock_undelete,
    ):
        # Undo delete + convert, old3 should be added back and new3 removed
        assert action_undoer.get_undo_message()
        assert action_undoer.undo() == ("old", "new")
        mock_trash.assert_called_once()
        mock_undelete.assert_called_once()


def test_undo_convert_without_deletion(action_undoer: ActionUndoer):
    action_undoer.append(Convert("old", "new", False))

    with (
        patch("image_viewer.helpers.action_undoer.trash_file") as mock_trash,
        patch("image_viewer.helpers.action_undoer.restore_from_bin") as mock_undelete,
    ):
        assert action_undoer.get_undo_message()
        assert action_undoer.undo() == ("", "new")
        mock_trash.assert_called_once()
        mock_undelete.assert_not_called()


def test_undo_rename(action_undoer: ActionUndoer):
    action_undoer.append(Rename("old", "new"))

    with patch("image_viewer.helpers.action_undoer.os.rename") as mock_rename:
        assert action_undoer.get_undo_message()
        assert action_undoer.undo() == ("old", "new")
        mock_rename.assert_called_once()


def test_undo_rotate(action_undoer: ActionUndoer):
    action_undoer.append(Rotate("old", b"original bytes"))

    with patch("builtins.open", mock_open()) as mock_fp:
        assert action_undoer.get_undo_message()
        assert action_undoer.undo() == ("", "")
        mock_fp.assert_called_once()
        assert any(call[0] == "().write" for call in mock_fp.mock_calls)
