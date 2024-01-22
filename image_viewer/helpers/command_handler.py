import re
from copy import copy
import argparse
from argparse import Namespace
from util.image import ImagePath
from managers.file_manager import ImageFileManager
from util.convert import try_convert_file_and_save_new


class CommandHandler:
    VALID_COMMANDS: set[str] = {"convert"}

    def __init__(self, file_manager: ImageFileManager) -> None:
        self.file_manager = file_manager

    def process_command(self, input: str) -> None:
        command_args = re.sub("  ", " ", input).strip().split(" ")

        command: str = command_args[0].lower()
        if command not in self.VALID_COMMANDS:
            return

        match command:
            case "convert":
                self._convert(command_args)

    def _convert(self, command_args: list[str]) -> str:
        if "-h" in command_args:
            return "Converts current image to a new format"

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("format")
        parser.add_argument(
            "-D",
            "--delete",
            action="store_true",
            help="Flag to delete original image after a successful conversion",
        )

        valid_formats: str = (
            f"Valid formats include {' '.join(self.file_manager.VALID_FILE_TYPES)}"
        )

        # TODO try catch and add valid formats to error message
        args: Namespace = parser.parse_args()

        current_image: ImagePath = self.file_manager.current_image

        new_image: ImagePath = copy(current_image)
        new_image.suffix = f".{args.format.lower()}"
        new_path_to_image: str = self.file_manager.construct_path_to_image(
            new_image.name
        )

        if not try_convert_file_and_save_new(
            self.file_manager.path_to_current_image,
            current_image,
            new_path_to_image,
            new_image,
        ):
            raise Exception(
                "Format was either invalid or an alias for the existing format.\n"
                + valid_formats
            )

        return "Success"
