import os, sys, click, subprocess
from typing import List
from InquirerPy import inquirer
from dotenv import load_dotenv
from conifg import load_config

load_dotenv()
BASE_PATH = os.getenv("BASE_PATH")
VSCODE_PATH = os.getenv("VSCODE_PATH")
NPM_PATH = os.getenv("NPM_PATH")
DOCKER_PATH = os.getenv("DOCKER_PATH")
BUN_PATH = os.getenv("BUN_PATH")

config = load_config()

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


def resolve_folder(folder_name):
    """
    Resolve the folder name using alias if applicable and validate existence.
    """
    aliases = config.get("alias", {})
    if folder_name in aliases:
        folder_name = aliases[folder_name]
    
    target_dir = os.path.join(BASE_PATH, folder_name)
    if not os.path.exists(target_dir):
        return None
    
    return target_dir

def isBun(target_dir):
    """
        Check if 'bun.lock' exists in the target directory.
    """
    return os.path.exists(os.path.join(target_dir, "bun.lock"))

def validate_package_json(target_dir):
    """
        Check if 'package.json' exists in the target directory.
    """
    return os.path.exists(os.path.join(target_dir, "package.json"))

def change_directory(target_dir):
    """
        Change the working directory to the target directory.
    """
    os.chdir(target_dir)


def open_in_vscode():
    """
    Open current directory in VS Code (or code-server) and detach from terminal.
    """
    try:
        kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }

        # Add platform-specific options
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS
        elif sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            # On Unix-like systems (Linux/macOS/iOS): run via shell in background
            subprocess.Popen(f"{VSCODE_PATH} . >/dev/null 2>&1 &", shell=True)
            return

        # Default fallback (Windows)
        subprocess.Popen([VSCODE_PATH, "."], **kwargs)

    except FileNotFoundError:
        print("Error: VS Code or code-server not found.")
    except Exception as e:
        print(f"Error: {e}")


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


def run_bun_dev():
    """
        Run 'bun dev' and handle errors.
    """
    try:
        subprocess.run([BUN_PATH, "dev"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command 'bun dev' failed with exit code {e.returncode}. Attempting recovery...")
        try:
            subprocess.run([BUN_PATH, "install"], check=True)
        except subprocess.CalledProcessError as install_error:
            click.echo(f"Error: 'bun install' failed with exit code {install_error.returncode}.")
    except FileNotFoundError:
        click.echo("Error: 'bun' is not installed or not in your PATH.")


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
        

def is_bun(folder: str) -> bool:
    return (
        os.path.exists(os.path.join(folder, "bun.lockb")) or
        os.path.exists(os.path.join(folder, "bun.lock")) or
        os.path.exists(os.path.join(folder, ".bunfig.toml"))
    )

def is_npm(folder: str) -> bool:
    return (
        os.path.exists(os.path.join(folder, "package-lock.json")) or
        os.path.exists(os.path.join(folder, "yarn.lock")) or
        os.path.exists(os.path.join(folder, "pnpm-lock.yaml"))
    )

def is_python(folder: str) -> bool:
    return (
        os.path.exists(os.path.join(folder, "requirements.txt")) or
        os.path.exists(os.path.join(folder, ".venv")) or
        os.path.exists(os.path.join(folder, "pyproject.toml"))
    )

def is_docker(folder: str) -> bool:
    return (
        os.path.exists(os.path.join(folder, "Dockerfile")) or
        os.path.exists(os.path.join(folder, "docker-compose.yml"))
    )


def updateRepo(force: bool, no_pull: bool) -> bool:
    """
        Update the repository by pulling the latest changes from the remote.
    """
    try:
        if force:
            subprocess.run(["git", "fetch", "--all"])
            subprocess.run(["git", "reset", "--hard", "origin/main"])
            return True
        elif not no_pull:
            subprocess.run(["git", "pull"])
            return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command 'git pull' failed with exit code {e.returncode}.")
        return False
    except FileNotFoundError:
        click.echo("Error: 'git' is not installed or not in your PATH.")
        return False
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")
        return False

    return False
    


PROJECT_DETECTORS = {
        "BUN": is_bun,
        "NPM": is_npm,
        "PYTHON": is_python,
        "DOCKER": is_docker,
    }

TAG_COLORS = {
    "BUN": "bright_blue",
    "NPM": "yellow",
    "PYTHON": "green",
    "DOCKER": "cyan",
}