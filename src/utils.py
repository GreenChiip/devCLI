import os
import click
import subprocess
from typing import List
from InquirerPy import inquirer
from dotenv import load_dotenv
from alias import load_aliases

load_dotenv()
BASE_PATH = os.getenv("BASE_PATH")
VSCODE_PATH = os.getenv("VSCODE_PATH")
NPM_PATH = os.getenv("NPM_PATH")
DOCKER_PATH = os.getenv("DOCKER_PATH")

## Fuction to get dirs in a path
def get_dirs_in_path(path: str) -> List[str]:
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def select_dir_with_package_json():
    """
    Allows the user to select a directory containing a `package.json` file using arrow keys.
    Keeps prompting until a valid directory is chosen or exits if none are available.

    :param base_path: The base path to search for directories.
    :return: The selected directory containing `package.json`.
    """
    while True:
        # Get a list of directories containing `package.json`
        dirs_with_package_json = [
            d for d in os.listdir(BASE_PATH)
            if os.path.isdir(os.path.join(BASE_PATH, d)) and
            os.path.exists(os.path.join(BASE_PATH, d, "package.json"))
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
        return os.path.join(BASE_PATH, selected_dir)


def resolve_folder(folder_name, alias):
    """
    Resolve the folder name using alias if applicable and validate existence.
    """
    if alias:
        aliases = load_aliases()
        if folder_name not in aliases:
            return False
        folder_name = aliases[folder_name]
    target_dir = os.path.join(BASE_PATH, folder_name)
    if not os.path.exists(target_dir):
        return False
    return target_dir

def validate_package_json(target_dir):
    """
    Check if 'package.json' exists in the target directory.
    """
    package_json_path = os.path.join(target_dir, "package.json")
    if not os.path.exists(package_json_path):
        click.echo(f"Error: 'package.json' does not exist in the folder '{target_dir}'.")
        return False
    return True

def change_directory(target_dir):
    """
    Change the working directory to the target directory.
    """
    os.chdir(target_dir)
    click.echo(f"Changed directory to: {target_dir}")

def open_in_vscode():
    """
    Open the current directory in Visual Studio Code.
    """
    try:
        subprocess.run([VSCODE_PATH, "."], check=True)
    except FileNotFoundError:
        click.echo("Error: Visual Studio Code is not installed or the path is incorrect.")


def run_npm_dev():
    """
    Run 'npm run dev' and handle errors.
    """
    try:
        subprocess.run([NPM_PATH, "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command 'npm run dev' failed with exit code {e.returncode}. Attempting recovery...")
        try:
            subprocess.run([NPM_PATH, "i", "--force"], check=True)
        except subprocess.CalledProcessError as install_error:
            click.echo(f"Error: 'npm i --force' failed with exit code {install_error.returncode}.")
    except FileNotFoundError:
        click.echo("Error: 'npm' is not installed or not in your PATH.")


def run_docker_compose_up(state, build, detach):
    ## Run docker-compose with the provided arguments
    args = [state]
    if build:
        args.append("--build")
    if detach:
        args.append("--detach")

    try:
        subprocess.run(["docker", "compose"] + args, check=True)
    except FileNotFoundError:
        click.echo("Error: 'docker compose' is not installed or not in your PATH.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command 'docker compose {state}' failed with exit code {e.returncode}.")
        
        