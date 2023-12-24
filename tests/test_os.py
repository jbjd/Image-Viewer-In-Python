from util.os import clean_str_for_OS_path


def test_clean_str_for_OS_path():
    """Test that illegal characters for OS are removed from string"""
    bad_name: str = "String/With/Illegal/Characters.png"
    good_name: str = clean_str_for_OS_path(bad_name)
    assert good_name == "StringWithIllegalCharacters.png"
