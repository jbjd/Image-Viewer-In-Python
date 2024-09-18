import configparser
import os
import sys

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(sys.argv[0]), "config.ini"))

# TODO: There must be a cleaner way to do this
try:
    default_font: str = config["FONT"]["DEFAULT"]
except KeyError:
    default_font = ""

if not default_font:
    default_font = "arial.ttf" if os.name == "nt" else "LiberationSans-Regular.ttf"

try:
    max_items_in_cache: int = int(config["CACHE"]["SIZE"])
except (KeyError, ValueError):
    max_items_in_cache = 20
