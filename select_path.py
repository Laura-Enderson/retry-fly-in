"""Provide terminal user interface for file selection and GUI configuration."""

from pathlib import Path
import questionary
from typing import Any


class Tui():
    """Handle user interactions through a terminal interface."""

    @staticmethod
    def find_txt_files() -> list[Path]:
        """
        Find text files.

        Returns:
            list[Path]: Sorted list of discovered text files.
        """
        root_path = Path(".")
        excluded_dirs = [
            ".venv",
            "venv",
            "__pycache__",
            ".git"
        ]
        txt_files = []
        for file in root_path.rglob("*"):
            relative_parts = file.relative_to(".").parts
            if any(part in excluded_dirs for part in relative_parts[:-1]):
                continue
            if file.is_file():
                txt_files.append(file)
        return sorted(txt_files)

    @staticmethod
    def select_txt_files() -> Any:
        """
        Display an interactive menu to select an input file.

        Returns:
            Any: Selected file path, or None if no file is found
                or the selection is cancelled.
        """
        files = Tui.find_txt_files()
        if not files:
            print("No input file found.")
            return None
        choices = [
            questionary.Choice(
                title=str(file.relative_to(".")),
                value=str(file.resolve())
            )
            for file in files
        ]
        selected_file = questionary.select(
            "Choose the map:",
            choices=choices,
            qmark="",
            pointer=">>>",
            instruction="Use arrow keys and press Enter\n"
        ).ask()
        return (selected_file)

    @staticmethod
    def ask_for_gui() -> Any:
        """
        Ask the user whether to display the graphical interface.

        Returns:
            Any: True if the GUI is enabled, False otherwise,
                or None if the selection is cancelled.
        """
        choices = [
            questionary.Choice(
                title="Yes",
                value=True
            ),
            questionary.Choice(
                title="No",
                value=False
            )
        ]
        answer = questionary.select(
            "Do you want to see the GUI?",
            choices=choices,
            qmark="\n\n",
            pointer=">>>",
            instruction="Use arrow keys and press Enter\n"
        ).ask()
        return answer
