from unittest.mock import patch

import pytest

from image_viewer.helpers.action_undoer import ActionUndoer, Convert, Delete, Rename


@pytest.fixture
def action_undoer() -> ActionUndoer:
    return ActionUndoer()


def test_action_undoer(action_undoer: ActionUndoer):
    """Test all 3 undoable actions"""

    action_undoer.append(Rename("This will get", "thrown out"))
    action_undoer.append(Rename("old", "new"))
    action_undoer.append(Convert("old2", "new2", False))
    action_undoer.append(Convert("old3", "new3", True))
    action_undoer.append(Delete("old4"))

    assert len(action_undoer) == 4  # maxlen is 4, 1st append is removed

    with patch("image_viewer.helpers.action_undoer.restore_from_bin") as mock_undelete:
        # Undo delete, old4 should be added back and nothing removed
        assert action_undoer.get_last_undoable_action()
        assert action_undoer.undo() == ("old4", "")
        mock_undelete.assert_called_once()

    with (
        patch("image_viewer.helpers.action_undoer.trash_file") as mock_trash,
        patch("image_viewer.helpers.action_undoer.restore_from_bin") as mock_undelete,
    ):
        # Undo delete + convert, old3 should be added back and new3 removed
        assert action_undoer.get_last_undoable_action()
        assert action_undoer.undo() == ("old3", "new3")
        mock_trash.assert_called_once()
        mock_undelete.assert_called_once()

    with patch("image_viewer.helpers.action_undoer.trash_file") as mock_trash:
        # Undo convert, nothing added back and new2 removed
        assert action_undoer.get_last_undoable_action()
        assert action_undoer.undo() == ("", "new2")
        mock_trash.assert_called_once()

    with patch("image_viewer.helpers.action_undoer.os.rename") as mock_rename:
        # Undo rename, old added back and new removed
        assert action_undoer.get_last_undoable_action()
        assert action_undoer.undo() == ("old", "new")
        mock_rename.assert_called_once()
