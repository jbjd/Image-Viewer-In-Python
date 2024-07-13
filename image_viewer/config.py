import configparser
import os
import sys

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(sys.argv[0]), "config.ini"))

default_font: str
try:
    default_font = config["FONT"]["DEFAULT"]
except KeyError:
    default_font = ""

if not default_font:
    default_font = "arial.ttf" if os.name == "nt" else "LiberationSans-Regular.ttf"
