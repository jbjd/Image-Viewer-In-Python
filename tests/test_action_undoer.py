from unittest.mock import patch

from image_viewer.util.action_undoer import ActionUndoer, RenameResult


def test_action_undoer():
    action_undoer = ActionUndoer()
    action_undoer.append(
        "old", "new", RenameResult(file_type_converted=False, preserve_index=False)
    )
    action_undoer.append(
        "old2", "new2", RenameResult(file_type_converted=True, preserve_index=True)
    )
    action_undoer.append(
        "old3", "new3", RenameResult(file_type_converted=True, preserve_index=False)
    )
    assert len(action_undoer._stack) == 3

    with patch("image_viewer.util.action_undoer.send2trash") as mock_trash:
        with patch("image_viewer.util.action_undoer.undelete") as mock_undelete:
            # Undo delete + convert, old3 should be added back and new3 removed
            assert action_undoer.undo() == ("old3", "new3")
            mock_trash.assert_called_once()
            mock_undelete.assert_called_once()

    with patch("image_viewer.util.action_undoer.send2trash") as mock_trash:
        # Undo convert, nothing added back and new2 removed
        assert action_undoer.undo() == ("", "new2")
        mock_trash.assert_called_once()

    with patch("image_viewer.util.action_undoer.os.rename") as mock_rename:
        # Undo rename, old added back and new removed
        assert action_undoer.undo() == ("old", "new")
        mock_rename.assert_called_once()
