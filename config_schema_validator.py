"""A simple script to valid the config.ini file
to ensure it presents accurate examples"""

from configparser import ConfigParser

from schema import Schema

from image_viewer.util._generic import is_valid_hex_color, is_valid_keybind

schema = Schema(
    {
        "FONT": {"default": str},
        "CACHE": {"size": lambda size: size == "" or int(size) >= 0},
        "KEYBINDS": {
            "COPY_TO_CLIPBOARD_AS_BASE64": is_valid_keybind,
            "move_to_new_file": is_valid_keybind,
            "show_details": is_valid_keybind,
            "undo_most_recent_action": is_valid_keybind,
        },
        "UI": {"background_color": is_valid_hex_color},
    }
)


config_parser: ConfigParser = ConfigParser()
config_parser.read("image_viewer/config.ini")

config: dict = {}
for section in config_parser.sections():
    config[section] = {}
    for option in config_parser.options(section):
        config[section][option] = config_parser.get(section, option)

schema.validate(config)
