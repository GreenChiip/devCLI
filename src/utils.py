import os
import json
from typing import List
from InquirerPy import inquirer

ALIAS_FILE = "E:\\Develepment (DEV)\\devCLI\\alias.json"

# Ensure the alias file exists
def ensure_alias_file():
    if not os.path.exists(ALIAS_FILE):
        with open(ALIAS_FILE, "w") as f:
            json.dump({}, f)

# Load aliases from the JSON file
def load_aliases():
    ensure_alias_file()
    with open(ALIAS_FILE, "r") as f:
        return json.load(f)

# Save aliases to the JSON file
def save_aliases(aliases):
    with open(ALIAS_FILE, "w") as f:
        json.dump(aliases, f, indent=4)

## Fuction to get dirs in a path
def get_dirs_in_path(path: str) -> List[str]:
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def select_dir_with_package_json(base_path="."):
    """
    Allows the user to select a directory containing a `package.json` file using arrow keys.
    Keeps prompting until a valid directory is chosen or exits if none are available.

    :param base_path: The base path to search for directories.
    :return: The selected directory containing `package.json`.
    """
    while True:
        # Get a list of directories containing `package.json`
        dirs_with_package_json = [
            d for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d)) and
            os.path.exists(os.path.join(base_path, d, "package.json"))
        ]

        if not dirs_with_package_json:
            print("No directories with 'package.json' found.")
            return None

        # Prompt user to select a directory
        selected_dir = inquirer.select(
            message="Select a directory with 'package.json':",
            choices=dirs_with_package_json,
            default=dirs_with_package_json[0],
        ).execute()

        # Return the selected directory
        return os.path.join(base_path, selected_dir)