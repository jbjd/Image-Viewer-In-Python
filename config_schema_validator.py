"""A simple script to valid the config.ini file
to ensure it presents accurate examples"""

from configparser import ConfigParser

from schema import Schema

schema = Schema(
    {
        "FONT": {"default": str},
        "CACHE": {"size": lambda size: size == "" or int(size) >= 0},
        "KEYBINDS": {
            "move_to_new_file": str,
            "show_details": str,
            "undo_most_recent_action": str,
        },
        "UI": {"background_color": str},
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
