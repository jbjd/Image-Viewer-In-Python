from unittest.mock import mock_open, patch

from image_viewer.__main__ import exception_hook


@patch("util.os.ask_write_on_fatal_error", lambda *_: True)
def test_exception_hook_when_user_declines():
    """Do not write to file when user says no"""
    exception = Exception("problem!")

    with patch("builtins.open", new_callable=mock_open) as mock_bultins_open:
        exception_hook(type(exception), exception, None, "")  # type: ignore
        mock_bultins_open.assert_not_called()


@patch("util.os.ask_write_on_fatal_error", lambda *_: False)
def test_exception_hook_when_user_accepts():
    """Write to file when user says so"""
    exception = Exception("problem!")

    with patch("builtins.open", side_effect=OSError):
        # Should catch and not fail writing to file
        exception_hook(type(exception), exception, None, "")

    with patch("builtins.open", new_callable=mock_open) as mock_bultins_open:
        exception_hook(type(exception), exception, None, "")  # type: ignore
        mock_bultins_open.assert_called_once()
