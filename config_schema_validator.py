from schema import Schema
from configparser import ConfigParser

schema = Schema(
    {
        "FONT": {"default": str},
        "CACHE": {"size": lambda size: size == "" or int(size) >= 0},
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
