from unittest.mock import patch

from PIL.Image import Image

from image_viewer.image.cache import ImageCache, ImageCacheEntry


def test_image_cache_full():
    """Should respect set value for max items and remove last inserted"""

    cache = ImageCache(2)

    entry1 = _get_empty_cache_entry()
    entry2 = _get_empty_cache_entry()
    entry3 = _get_empty_cache_entry()

    cache["entry1"] = entry1
    cache["entry2"] = entry2
    cache["entry3"] = entry3

    assert len(cache) == 2
    assert entry1 not in cache


def test_zero_length_cache():
    """Should not try to insert anything when max items is 0"""

    cache = ImageCache(0)

    with patch.object(cache, "__setitem__") as mock_set_item:
        cache["entry1"] = _get_empty_cache_entry()

        assert len(cache) == 0
        mock_set_item.assert_not_called()


def test_update_key():
    """Should move value from one key to another"""

    cache = ImageCache(1)

    old_key: str = "entry1"
    new_key: str = "entry2"
    cache[old_key] = _get_empty_cache_entry()

    cache.update_key("does_not_exist", new_key)
    assert old_key in cache

    cache.update_key(old_key, new_key)
    assert old_key not in cache
    assert new_key in cache


def _get_empty_cache_entry() -> ImageCacheEntry:
    return ImageCacheEntry(Image(), (0, 0), "", 0, "", "")
