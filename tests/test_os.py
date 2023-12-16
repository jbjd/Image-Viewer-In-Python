from util.os import clean_str_for_OS_path


def test_clean_str_for_OS_path():
    bad_string: str = "String/With/Illegal/Characters.png"
    good_name = clean_str_for_OS_path(bad_string)
    assert good_name == "StringWithIllegalCharacters.png"
