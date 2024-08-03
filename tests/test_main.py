from unittest.mock import mock_open, patch

from image_viewer.__main__ import exception_hook


def test_exception_hook():
    """Ensure tries to write to a file while swallowing errors"""
    exception = Exception("problem!")

    with patch("builtins.open", side_effect=OSError):
        # Should catch and not fail writing to file
        exception_hook(type(exception), exception, None, "")  # type: ignore

    with patch("builtins.open", new_callable=mock_open) as mock_bultins_open:
        exception_hook(type(exception), exception, None, "")  # type: ignore
        mock_bultins_open.assert_called_once()
