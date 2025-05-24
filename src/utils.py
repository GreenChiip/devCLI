import os, sys, subprocess, logging
from typing import List
from InquirerPy import inquirer
from dotenv import load_dotenv
from config import load_config # load_config uses logging
import click # Added for click.echo in updateRepo

logger = logging.getLogger(__name__)

load_dotenv()
logger.debug(f"BASE_PATH from env: {os.getenv('BASE_PATH')}")
BASE_PATH = os.getenv("BASE_PATH")
VSCODE_PATH = os.getenv("VSCODE_PATH")
NPM_PATH = os.getenv("NPM_PATH")
DOCKER_PATH = os.getenv("DOCKER_PATH")
BUN_PATH = os.getenv("BUN_PATH")

config = load_config()
aliases = load_config("alias")

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
            logger.warning("No directories with 'package.json' found.")
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
    if folder_name in aliases:
        folder_name = aliases[folder_name]
    
    
    target_dir = os.path.join(BASE_PATH, folder_name)
    logger.debug(f"Resolved target_dir: {target_dir}")
    
    if not os.path.exists(target_dir):
        logger.warning(f"Target directory {target_dir} does not exist.")
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
    logger.debug(f"Attempting to open VS Code at {os.getcwd()}")
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
        logger.error(f"Error: VS Code or code-server not found at VSCODE_PATH: {VSCODE_PATH}. Please check your .env file.")
    except Exception as e:
        logger.error(f"Error opening VS Code: {e}")


def run_npm_dev():
    """
        Run 'npm run dev' and handle errors.
    """
    logger.debug(f"Running 'npm run dev' with NPM_PATH: {NPM_PATH}")
    try:
        subprocess.run([NPM_PATH, "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: Command 'npm run dev' failed with exit code {e.returncode}. Attempting recovery...")
        logger.debug(e)
        try:
            logger.info("Attempting 'npm i --force'...")
            subprocess.run([NPM_PATH, "i", "--force"], check=True)
            logger.info("'npm i --force' completed. Please try running the dev command again.")
        except subprocess.CalledProcessError as install_error:
            logger.error(f"Error: 'npm i --force' failed with exit code {install_error.returncode}.")
            logger.debug(install_error)
    except FileNotFoundError:
        logger.error(f"Error: 'npm' is not installed or not in your PATH. NPM_PATH: {NPM_PATH}")


def run_bun_dev():
    """
        Run 'bun dev' and handle errors.
    """
    logger.debug(f"Running 'bun dev' with BUN_PATH: {BUN_PATH}")
    try:
        subprocess.run([BUN_PATH, "dev"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: Command 'bun dev' failed with exit code {e.returncode}. Attempting recovery...")
        logger.debug(e)
        try:
            logger.info("Attempting 'bun install'...")
            subprocess.run([BUN_PATH, "install"], check=True)
            logger.info("'bun install' completed. Please try running the dev command again.")
        except subprocess.CalledProcessError as install_error:
            logger.error(f"Error: 'bun install' failed with exit code {install_error.returncode}.")
            logger.debug(install_error)
    except FileNotFoundError:
        logger.error(f"Error: 'bun' is not installed or not in your PATH. BUN_PATH: {BUN_PATH}")


def run_docker_compose_up(state, build, detach):
    ## Run docker-compose with the provided arguments
    logger.debug(f"Running 'docker compose {state}' with build={build}, detach={detach}. DOCKER_PATH: {DOCKER_PATH}")
    args = [state]
    if build:
        args.append("--build")
    if detach:
        args.append("--detach")

    try:
        subprocess.run([DOCKER_PATH, "compose"] + args, check=True)
    except FileNotFoundError:
        logger.error(f"Error: 'docker compose' is not installed or not in your PATH. DOCKER_PATH: {DOCKER_PATH}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: Command 'docker compose {state}' failed with exit code {e.returncode}.")
        logger.debug(e)
        

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
    logger.debug(f"Updating repo. Force: {force}, No Pull: {no_pull}")
    try:
        if force:
            logger.warning("The --force option will discard any local changes and reset your current branch to origin/main.")
            confirm_force_update = inquirer.confirm(
                message="Are you sure you want to proceed with the force update? This is a destructive operation.",
                default=False
            ).execute()
            if not confirm_force_update:
                logger.info("Force update cancelled by the user.")
                click.echo("Force update cancelled.")
                return False # Indicate that the update was cancelled
            
            logger.info("Forcing update: git fetch --all and git reset --hard origin/main")
            subprocess.run(["git", "fetch", "--all"], check=True)
            subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
            logger.info("Force update successful.")
            return True
        elif not no_pull:
            logger.info("Pulling latest changes: git pull")
            subprocess.run(["git", "pull"], check=True)
            logger.info("Git pull successful.")
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: Git command failed with exit code {e.returncode}.")
        logger.debug(e)
        return False
    except FileNotFoundError:
        logger.error("Error: 'git' is not installed or not in your PATH.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during repo update: {e}")
        logger.debug(e)
        return False

    logger.debug("Repo update skipped as no_pull is True and force is False.")
    return False
    

def run_install_package(package_manager: str):
    """
        Run the package manager's install command.
    """
    logger.debug(f"Running install for package manager: {package_manager}")
    try:
        if package_manager == "npm":
            logger.info(f"Running 'npm install' with NPM_PATH: {NPM_PATH}")
            subprocess.run([NPM_PATH, "install"], check=True)
            logger.info("'npm install' successful.")
        elif package_manager == "bun":
            logger.info(f"Running 'bun install' with BUN_PATH: {BUN_PATH}")
            subprocess.run([BUN_PATH, "install"], check=True)
            logger.info("'bun install' successful.")
        else:
            logger.error(f"Error: Unsupported package manager '{package_manager}'.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: Command '{package_manager} install' failed with exit code {e.returncode}.")
        logger.debug(e)
    except FileNotFoundError:
        logger.error(f"Error: '{package_manager}' is not installed or not in your PATH. Path for {package_manager.upper()}_PATH might be missing in .env or incorrect.")


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