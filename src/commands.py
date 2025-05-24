import click, os, logging
from dotenv import load_dotenv
from InquirerPy import inquirer

logger = logging.getLogger(__name__)
from utils import run_install_package, updateRepo, open_in_vscode, run_npm_dev, is_bun, PROJECT_DETECTORS, TAG_COLORS, run_bun_dev, select_dir_with_package_json, resolve_folder, validate_package_json, change_directory, run_docker_compose_up
from config import handle_add_alias, handle_remove_alias, handle_list_aliases, load_config, save_config
from create import get_project_details, generate_project_json, create_project_files

load_dotenv()

# Ensure config and aliases are loaded after BASE_PATH is potentially set by dotenv
BASE_PATH = os.getenv("BASE_PATH")
# Note: config and aliases are loaded globally. This is fine for now,
# but for the 'configcmd set' to reflect changes immediately if 'config' variable is used by other commands
# during the same run, 'config' might need to be reloaded or updated.
# However, load_config() is called within each command, so it always gets fresh data.

config = load_config()
aliases = load_config("alias")

@click.command("run", help="Run 'npm run dev' in the specified folder.")
@click.argument('folder_name')
def run_dev(folder_name):
    logger.debug(f"run_dev called with folder_name: {folder_name}")
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        logger.error("No valid directory selected or directory does not exist.")
        return
    
    if not validate_package_json(target_dir):
        logger.warning(f"'package.json' not found in {target_dir}. Attempting to select a different directory.")
        target_dir = select_dir_with_package_json() # Removed target_dir argument
        if not target_dir:
            logger.error(f"Error: 'package.json' does not exist in the folder '{target_dir}'.")
            return

    change_directory(target_dir)
    logger.info(f"Changed directory to: {target_dir}")

    if is_bun(target_dir):
        logger.info("Detected 'bun.lock'. Running 'bun dev'...")
        run_bun_dev()
    else:
        logger.info("Running 'npm run dev'...")
        run_npm_dev()

@click.command("alias", help="Add or remove an alias.")
@click.argument("action", required=False)
@click.argument("alias_name", required=False)
@click.argument("alias_for", required=False)
def alias(action, alias_name, alias_for):
    if action is None:
        handle_list_aliases(aliases) # This function in config.py will also need logger
        return
    
    logger.debug(f"alias command called with action: {action}, alias_name: {alias_name}, alias_for: {alias_for}")
    if action not in ["add", "remove"]:
        logger.error("Error: Invalid action. Use 'add' or 'remove'.")
        return
        
    if action == "add":
        handle_add_alias(aliases, alias_name, alias_for) # This function in config.py will also need logger
        return
    
    if action == "remove":
        handle_remove_alias(aliases, alias_name) # This function in config.py will also need logger
        return



@click.command("code", help="Opens the selected folder in VScode. (default: dev)")
@click.argument('folder_name', required=True, type=str)
def code(folder_name = "dev"):
    logger.debug(f"code command called with folder_name: {folder_name}")
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        logger.error(f"Folder '{folder_name}' not found or alias is incorrect.")
        return
    
    change_directory(target_dir)
    logger.info(f"Changed directory to: {target_dir}")
    open_in_vscode()
    

@click.command("docker", help="Run 'docker-compose up' in the selected folder.")
@click.argument('folder_name', required=True, type=str) 
@click.argument('state', required=True, type=click.Choice(["up", "down"], case_sensitive=False))
@click.option("--build", "-b", help="Build images before starting containers.", is_flag=True)
@click.option("--detach", "-d", help="Run containers in the background.", is_flag=True)
def docker(folder_name, state, build, detach):
    logger.debug(f"docker command called with folder_name: {folder_name}, state: {state}, build: {build}, detach: {detach}")
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        logger.error(f"Folder '{folder_name}' not found or alias is incorrect.")
        return

    change_directory(target_dir)
    logger.info(f"Changed directory to: {target_dir}")
    run_docker_compose_up(state, build, detach)


@click.command("init", help="Create a new project folder with a devCLI-project.json file. (not implemented yet)")
def init():
    """
    Initialize a new project with a devCLI-project.json file and prompt the user for details.
    """
    logger.info("Starting project initialization...")
    # Gather project details
    project_details = get_project_details()
    if not project_details:
        logger.error("Project details not provided or cancelled. Aborting init.")
        return

    # Ensure BASE_PATH is available
    if not BASE_PATH:
        logger.error("BASE_PATH environment variable is not set. Cannot create project directory.")
        click.echo("❌ Error: BASE_PATH is not configured. Please set it in your .env file.")
        return
        
    project_path = os.path.join(BASE_PATH, project_details["name"])
    logger.debug(f"Project will be created at: {project_path}")

    try:
        os.makedirs(project_path, exist_ok=True) # exist_ok=True in case folder was created manually before error
        logger.info(f"Ensured project directory exists: {project_path}")
    except OSError as e:
        logger.error(f"Error creating project directory {project_path}: {e}")
        click.echo(f"❌ Error creating project directory: {e}")
        return

    # Generate devCLI-project.json
    # generate_project_json expects project_details, and it creates the file *inside* project_details["name"]
    # so we must be in BASE_PATH or provide full path.
    # The current generate_project_json in create.py is:
    # project_json_path = os.path.join(project_details["name"], "devCLI-project.json")
    # This implies it should be called when CWD is BASE_PATH, or it needs adjustment.
    # For safety, let's change CWD.
    original_cwd = os.getcwd()
    try:
        os.chdir(BASE_PATH) # Change to base path to match how generate_project_json constructs path
        logger.debug(f"Changed CWD to {BASE_PATH} for generate_project_json")
        generate_project_json(project_details)
    except Exception as e:
        logger.error(f"Error during generate_project_json: {e}")
        click.echo(f"❌ Error generating devCLI-project.json: {e}")
        os.chdir(original_cwd) # Restore CWD
        return
    finally:
        os.chdir(original_cwd) # Always restore CWD
        logger.debug(f"Restored CWD to {original_cwd}")


    # Add folder to aliases if confirmed
    if inquirer.confirm(message="Do you want to add this folder to your aliases?", default=True).execute():
        alias_name_default = project_details["name"].split('-NextJS-')[0].split('-Python-')[0] # Suggest cleaner name
        alias_name = inquirer.text(message="Enter alias name:", default=alias_name_default).execute()
        
        # Validate alias_name (handle_add_alias does this, but good to catch early)
        if not alias_name:
            logger.warning("No alias name entered. Skipping alias creation.")
        elif alias_name in aliases:
            logger.warning(f"Alias '{alias_name}' already exists. Skipping alias creation.")
            click.echo(f"⚠️ Alias '{alias_name}' already exists.") # User facing
        else:
            # The alias target should be the project folder name, relative to BASE_PATH
            handle_add_alias(aliases, alias_name, project_details["name"])
            # aliases object is modified in place by handle_add_alias and saved by it.

    # Create project-specific files
    # create_project_files expects project_details.
    # It then calls create_node_files(project_details["name"]) or create_python_files(project_details["name"])
    # These functions then operate within that path.
    # So, similar to generate_project_json, these need to be called from BASE_PATH or paths adjusted.
    try:
        os.chdir(BASE_PATH)
        logger.debug(f"Changed CWD to {BASE_PATH} for create_project_files")
        create_project_files(project_details) 
    except Exception as e:
        logger.error(f"Error during create_project_files: {e}")
        click.echo(f"❌ Error creating project specific files: {e}")
        return # Don't report success if this fails
    finally:
        os.chdir(original_cwd)
        logger.debug(f"Restored CWD to {original_cwd} after create_project_files")


    logger.info(f"Project '{project_details['name']}' initialized successfully!")
    click.echo(f"✅ Project '{project_details['name']}' initialized successfully at {project_path}") # User facing


@click.command("list", help="List all available folders.")
def list_folders():
    """
    List all available folders in the BASE_PATH with detected project type tags.
    """
    logger.debug(f"Listing folders in BASE_PATH: {BASE_PATH}")
    folders = [
        d for d in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, d))
    ]

    if not folders:
        logger.info("No folders found in BASE_PATH.")
        click.echo("No folders found.") # User facing
        return

    click.echo("Available folders:") # User facing
    for folder in folders:
        full_path = os.path.join(BASE_PATH, folder)
        logger.debug(f"Checking folder: {full_path}")
        tags = [tag for tag, detector in PROJECT_DETECTORS.items() if detector(full_path)]

        # Colorize tags
        colored_tags = [
            click.style(tag, fg=TAG_COLORS.get(tag, "white"))
            for tag in tags
        ]

        # Align output nicely
        folder_display = f"{folder:<35}"
        if tags:
            folder_display += f"[{', '.join(colored_tags)}]"

        click.echo(f"  - {click.style(folder_display)}") # User facing


@click.command("update", help="Get the latest version of the projects git repo (default: dev).")
@click.argument('folder_name', required=False, default="dev")
@click.option('--force', is_flag=True, help="Force update even if no changes detected.")
@click.option('--no-pull', is_flag=True, help="Skip pulling changes from the repository.")
def update(folder_name, force = False , no_pull = False):
    """
    Update the devCLI to the latest version from GitHub.
    """
    logger.debug(f"update command called with folder_name: {folder_name}, force: {force}, no_pull: {no_pull}")
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        logger.error("No valid directory selected for update.")
        return
    
    change_directory(target_dir)
    logger.info(f"Changed directory to: {target_dir} for update")
    if updateRepo(force, no_pull):
        logger.info("Update completed successfully!")
        click.echo("Update completed successfully!") # User facing
        # Check if the project has a package.json file and ask if to run npm install if it does
        if validate_package_json(target_dir):
            logger.debug(f"package.json found in {target_dir}")
            if inquirer.confirm(message="Do you want to install packages?", default=True).execute():
                if is_bun(target_dir):
                    logger.info("Detected 'bun.lock'. Running 'bun install'...")
                    click.echo("Detected 'bun.lock'. Running 'bun install'...") # User facing
                    run_install_package("bun")
                else:
                    logger.info("Running 'npm install'...")
                    click.echo("Running 'npm install'...") # User facing
                    run_install_package("npm")
        else:
            logger.info("No package.json found. Skipping package installation.")
            click.echo("No package.json found. Skipping npm install.") # User facing
        
    else:
        logger.warning("No updates available or an error occurred during update.")
        click.echo("No updates available or an error occurred.") # User facing


@click.command("start", help="Start the current default selected project.")
@click.option('setProject', "--set", help="Set a project to start by default.", default=None)
@click.option('code', '--code', is_flag=True, help="Open the project in VSCode.")
def start(setProject = None, code = True):
    """
    Start the current selected project.
    """
    logger.debug(f"start command called with setProject: {setProject}, code: {code}")
    if setProject:
        target_dir = resolve_folder(setProject)
        if not target_dir:
            logger.error(f"Cannot set project. Folder '{setProject}' not found or alias is incorrect.")
            return
        config["currentProject"] = setProject
        save_config(config) # This function in config.py will also need logger
        logger.info(f"Current project set to: {setProject}")
        click.echo(f"Current project set to: {setProject}") # User facing
        return

    current_project_name = config.get("currentProject")
    if not current_project_name:
        logger.error("No current project set. Use `devcli start --set <project_name>` to set one.")
        return

    target_dir = resolve_folder(current_project_name)
    if not target_dir:
        logger.error(f"Current project '{current_project_name}' not found. Please select a valid project.")
        return

    change_directory(target_dir)
    logger.info(f"Changed directory to current project: {target_dir}")

    if code: # Check if code flag is true
        logger.debug("Opening project in VSCode due to --code flag or default behavior.")
        open_in_vscode()

    if not validate_package_json(target_dir):
        logger.info(f"'package.json' not found in {target_dir}. Only opening in VSCode if specified.")
        # open_in_vscode() was here, moved up to handle --code flag independently
        return
    
    if is_bun(target_dir):
        logger.info("Detected 'bun.lock'. Running 'bun dev'...")
        click.echo("Detected 'bun.lock'. Running 'bun dev'...") # User facing
        # open_in_vscode() was here, moved up
        run_bun_dev()
    else:
        logger.info("Running 'npm run dev'...")
        # open_in_vscode() was here, moved up
        run_npm_dev()


@click.command("cd", help="Change directory to the specified folder.")
@click.argument('folder_name', required=False, type=str, default=None)
def cd(folder_name):
   logger.debug(f"cd command called with folder_name: {folder_name}")
   if folder_name == None:
        current_project_name = config.get("currentProject")
        if not current_project_name:
            logger.error("No current project set. Cannot change directory.")
            return
        target_dir = resolve_folder(current_project_name)
        if not target_dir:
            logger.error(f"Current project '{current_project_name}' not found.")
            return
        change_directory(target_dir)
        logger.info(f"Changed directory to current project: {target_dir}")
        click.echo(f"Changed directory to: {target_dir}") # User facing
   else:
        target_dir = resolve_folder(folder_name)
        if not target_dir:
            logger.error(f"Folder '{folder_name}' not found or alias is incorrect.")
            return
        change_directory(target_dir)
        logger.info(f"Changed directory to: {target_dir}")
        click.echo(f"Changed directory to: {target_dir}") # User facing
       

@click.command("help", help="Show help information.")
@click.argument('command', required=False)
def help(command = None):
    if command:
        commands = {
            "run": run_dev,
            "alias": alias,
            "code": code,
            "docker": docker,
            "init": init,
            "list": list_folders,
            "update": update,
            "start": start,
            "help": help
        }

        if command in commands:
            # click.echo(commands[command].get_help(click.Context(commands[command])))
            # click.echo("")
            # The above is fine, but for consistency, let's logger.debug it if verbose
            help_text = commands[command].get_help(click.Context(commands[command]))
            logger.debug(f"Displaying help for command: {command}\n{help_text}")
            click.echo(help_text) # User facing
            click.echo("") # User facing
        else:
            logger.error(f"Error: Command '{command}' not found for help display.")
            # print "Error" in a red color
            click.echo(f"Error: Command '{command}' not found.", fg="red") # User facing
            click.echo() # User facing
    else:
        # This is general help, click.echo is appropriate
        click.echo("")
        click.echo("devCLI - Command Line Interface")
        click.echo("Available commands:")
        click.echo("   run <folder_name>  - Run 'npm run dev' in the specified folder.")
        click.echo("   alias <action> <alias_name> <alias_for>  - Add or remove an alias.")
        click.echo("   code <folder_name>  - Open the specified folder in VScode.")
        click.echo("   docker <folder_name> <state> [--build] [--detach]  - Run docker-compose up/down.")
        click.echo("   init  - Create a new project folder with a devCLI-project.json file.")
        click.echo("   list  - List all available folders.")
        click.echo("   update [folder_name] [--force] [--no-pull]  - Update devCLI to the latest version.")
        click.echo("   configcmd <subcommand> [args] - View or modify CLI configuration.")
        click.echo("   help  - Show help information.")
        click.echo("")


# CONFIG COMMANDS START
@click.group("configcmd", help="View or modify CLI configuration (config.json). Name is 'configcmd' to avoid conflict with 'config' variable.")
def config_cmd():
    pass

@config_cmd.command("view", help="View all current configurations or a specific key.")
@click.argument("key", required=False)
def view_config(key):
    cfg = load_config() # Loads from main config.json
    if not cfg:
        logger.warning("Configuration is empty or could not be loaded.")
        click.echo("Configuration is empty.")
        return

    if key:
        if key in cfg:
            click.echo(f"{key}: {cfg[key]}")
        else:
            logger.warning(f"Configuration key '{key}' not found.")
            click.echo(f"Error: Key '{key}' not found in configuration.")
    else:
        click.echo("Current configuration:")
        for k, v in cfg.items():
            click.echo(f"  {k}: {v}")

@config_cmd.command("set", help="Set a configuration key-value pair.")
@click.argument("key")
@click.argument("value")
def set_config(key, value):
    cfg = load_config()
    # Attempt to parse value to common types like int, float, bool
    try:
        parsed_value = int(value)
    except ValueError:
        try:
            parsed_value = float(value)
        except ValueError:
            if value.lower() == 'true':
                parsed_value = True
            elif value.lower() == 'false':
                parsed_value = False
            else:
                parsed_value = value # Keep as string

    cfg[key] = parsed_value
    save_config(cfg) # Saves to main config.json
    logger.info(f"Configuration updated: Set '{key}' to '{parsed_value}'.")
    click.echo(f"Configuration updated: '{key}' has been set to '{parsed_value}'.")

@config_cmd.command("get", help="Get a specific configuration value by key.")
@click.argument("key")
def get_config(key):
    cfg = load_config() # ensure cfg is loaded
    if key in cfg:
        click.echo(f"{cfg[key]}") # Directly print the value
    else:
        logger.warning(f"Configuration key '{key}' not found.")
        click.echo(f"Error: Key '{key}' not found in configuration.", err=True)
# CONFIG COMMANDS END
