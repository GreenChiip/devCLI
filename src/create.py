import click, os, json, subprocess, logging, shutil # Added shutil
from datetime import datetime
from InquirerPy import inquirer
from dotenv import load_dotenv

from config import handle_add_alias, load_config
from utils import resolve_folder

logger = logging.getLogger(__name__)

# Determine CLI_ROOT_DIR, assuming this file is in CLI_ROOT_DIR/src/create.py
CLI_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.debug(f"CLI_ROOT_DIR determined as: {CLI_ROOT_DIR}")

load_dotenv() 
BASE_PATH = os.getenv("BASE_PATH") # Used for new projects and potentially by resolve_folder
NPX_PATH = os.getenv("NPX_PATH") # Used by initCommand for Next.js

# These are loaded globally in commands.py, but for create.py to use them if needed directly:
# config = load_config() 
# aliases = load_config("alias")
# However, it's better if functions like handle_add_alias are passed the aliases object from commands.py.
# For now, assuming config/aliases loaded here if needed by functions in this module directly,
# or they are passed in as args. `load_config` is used in `get_project_details`.


def get_project_details(existing_project_name: str = None, existing_project_path: str = None):
    """
    Prompt the user for project details and return them as a dictionary.
    Can pre-fill project name and path for in-place initialization.
    """
    final_project_name = None
    project_path_to_use = None

    if existing_project_name and existing_project_path:
        logger.info(f"Getting project details for existing project: {existing_project_name} at {existing_project_path}")
        final_project_name = existing_project_name
        project_path_to_use = existing_project_path
        # Description and author will still be prompted for, allowing customization even for existing dirs.
    else:
        if not BASE_PATH: # Crucial for creating new projects
            logger.error("BASE_PATH is not set. Cannot create new project or check for existing directories.")
            click.echo("❌ Error: BASE_PATH is not configured. Please set it in your .env file.")
            return {}

        project_name_input = inquirer.text(message="Enter the project name:").execute()
        if not project_name_input.strip():
            logger.error("Project name cannot be empty.")
            click.echo("❌ Project name cannot be empty.")
            return {}

        final_project_name = project_name_input
        prospective_path = os.path.join(BASE_PATH, project_name_input)
        if os.path.exists(prospective_path):
            logger.warning(f"Directory '{project_name_input}' already exists at {prospective_path}.")
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            final_project_name = f"{project_name_input}-{current_time}"
            click.echo(f"⚠️ Folder '{project_name_input}' already exists. Name changed to '{final_project_name}'.")
            logger.info(f"Project name changed to '{final_project_name}' due to existing directory.")
        
        project_path_to_use = os.path.join(BASE_PATH, final_project_name)

    project_description = inquirer.text(message="Enter the project description:", default="A new project").execute()
    project_author = inquirer.text(message="Enter the author name:", default="Your Name").execute()

    # Load Project Types from config.json
    cli_config = load_config() # Loads main config.json
    if not cli_config:
        logger.error("Failed to load CLI configuration (config.json). Cannot list project types.")
        click.echo("❌ Error: Could not load CLI configuration.")
        return {} 
        
    project_types_config = cli_config.get("initialized_commands", {})
    if not project_types_config:
        logger.error("No project types defined in config.json under 'initialized_commands'. Cannot proceed.")
        click.echo("❌ Error: No project types found in CLI configuration.")
        return {}

    # Prepare Choices for InquirerPy
    choices = [
        {"name": details.get("name", key), "value": key}
        for key, details in project_types_config.items() if isinstance(details, dict) # ensure details is a dict
    ]
    if not choices:
        logger.error("No valid choices could be prepared from 'initialized_commands' in config.json.")
        click.echo("❌ Error: No project types available to choose from.")
        return {}

    # Prompt for Project Type
    chosen_project_type_key = inquirer.select(
        message="Select project type:",
        choices=choices,
        default=choices[0]["value"] if choices else None
    ).execute()
    
    selected_config = project_types_config.get(chosen_project_type_key)
    if not selected_config:
        logger.error(f"Configuration for selected project type key '{chosen_project_type_key}' not found.")
        click.echo("❌ Error: Selected project type configuration is missing.")
        return {}

    # Prompt for Docker Usage
    use_docker = inquirer.confirm(
        message="Do you want to use Docker for this project environment?",
        default=selected_config.get("defaultUseCompose", False) # Use default from config if available
    ).execute()

    return {
        "name": final_project_name,
        "path": project_path_to_use, # Absolute path to the project
        "description": project_description,
        "author": project_author,
        "chosen_project_type_key": chosen_project_type_key,
        "project_type_config": selected_config,
        "use_docker": use_docker
    }


def generate_project_json(project_details):
    """
    Create the devCLI-project.json file with project details and commands.
    """
    project_type = project_details["type"]
    project_json = {
        "name": project_details["name"],
        "description": project_details["description"],
        "author": project_details["author"],
        "commands": {
            "npm": "npm run dev" if project_type == "node" else None,
            "docker": "docker-compose up --build" if project_type in ["python"] else None,
        }
    }

    if not project_details or not project_details.get("name") or not project_details.get("project_type_config"):
        logger.error("generate_project_json called with incomplete project_details.")
        return

    project_name = project_details["name"]
    project_config = project_details["project_type_config"]
    use_docker_choice = project_details.get("use_docker", False)

    # Determine startup command
    startup_command = None
    if use_docker_choice:
        startup_command = project_config.get("dockerStartupCommand")
    else:
        startup_command = project_config.get("localStartupCommand")
    
    if not startup_command:
        logger.warning(f"No startup command found for project '{project_name}' (Docker choice: {use_docker_choice}).")

    # Determine useCompose
    docker_compose_path_template = project_config.get("dockerComposePath")
    default_use_compose_from_config = project_config.get("defaultUseCompose", False)
    # useCompose is true if user chose Docker, a docker-compose path is defined, AND the project type defaults to using compose
    # This interpretation means even if a compose file *could* be used, if defaultUseCompose is false, this flag is false.
    # An alternative interpretation could be: use_docker AND docker_compose_path_template exists.
    # Using the prompt's specified logic:
    actual_use_compose = bool(use_docker_choice and docker_compose_path_template and default_use_compose_from_config)
    logger.debug(f"Determined useCompose for {project_name}: {actual_use_compose} (use_docker_choice: {use_docker_choice}, docker_compose_path_template: {docker_compose_path_template}, default_use_compose_from_config: {default_use_compose_from_config})")

    project_json_data = {
        "name": project_name,
        "version": "0.1.0", # Default version
        "description": project_details.get("description", ""),
        "author": project_details.get("author", ""),
        "project_type_key": project_details.get("chosen_project_type_key"),
        "project_type_name": project_config.get("name"),
        "use_docker_preference": use_docker_choice, # User's direct choice for Docker
        "useCompose": actual_use_compose, # Specific logic as per requirements
        "startup": startup_command,
        # Store template paths for reference, only if Docker is chosen by user
        "dockerfile_template": project_config.get("dockerfilePath") if use_docker_choice else None,
        "docker_compose_template": docker_compose_path_template if use_docker_choice else None,
    }
    
    # The project_details['path'] is the absolute path to the project directory.
    # devCLI-project.json should be created inside this path.
    if not project_details.get("path"):
        logger.error("generate_project_json called but 'path' is missing in project_details.")
        click.echo("❌ Error: Project path missing, cannot generate devCLI-project.json.")
        return
        
    project_json_target_path = os.path.join(project_details["path"], "devCLI-project.json")
    logger.debug(f"Generating devCLI-project.json at: {project_json_target_path} with data: {project_json_data}")
    
    try:
        with open(project_json_target_path, "w") as f:
            json.dump(project_json_data, f, indent=4)
        logger.info(f"Created devCLI-project.json in {project_details['name']}") # Use name for logging simplicity
        click.echo(f"📄 Created devCLI-project.json in {project_details['name']}")
    except IOError as e:
        logger.error(f"Failed to write devCLI-project.json for {project_details['name']}: {e}")
        click.echo(f"❌ Error writing devCLI-project.json: {e}")


def create_project_structure_from_command(project_details):
    project_name = project_details.get("name")
    project_root_path = project_details.get("path") # Absolute path to the project
    project_config = project_details.get("project_type_config")
    init_command_template = project_config.get("initCommand")

    if not all([project_name, project_root_path, project_config, init_command_template]):
        logger.error("create_project_structure_from_command called with incomplete details.")
        click.echo("❌ Error: Cannot create project structure due to missing configuration or project path.")
        return

    logger.info(f"Creating project structure for '{project_name}' using type '{project_details.get('chosen_project_type_key')}'.")
    # initCommand is executed from within project_root_path
    init_command = init_command_template
    logger.info(f"Executing initialization command in {project_root_path}: {init_command}")
    
    try:
        if ".venv/bin/activate" in init_command:
            full_command = f"bash -c 'cd \"{project_root_path}\" && {init_command}'"
            logger.debug(f"Executing wrapped venv command: {full_command}")
            process = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
        else:
            process = subprocess.run(init_command, shell=True, check=True, capture_output=True, text=True, cwd=project_root_path)

        logger.info(f"Initialization command stdout for '{project_name}':\n{process.stdout}")
        if process.stderr:
            logger.info(f"Initialization command stderr for '{project_name}':\n{process.stderr}")
        click.echo(f"✅ Project files for '{project_name}' initialized successfully using command.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during project files initialization for '{project_name}': {e.cmd}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        click.echo(f"❌ Error initializing project files for '{project_name}'. Check logs for details.")
        return # Stop if init command fails

    except Exception as e:
        logger.error(f"An unexpected error occurred during project files initialization for '{project_name}': {e}")
        click.echo(f"❌ An unexpected error occurred. Check logs for details.")
        return # Stop on other errors too

    # Docker file copying logic, executed after initCommand
    if project_details.get("use_docker"):
        logger.debug(f"Attempting to copy Docker files for '{project_name}'. CLI_ROOT_DIR: {CLI_ROOT_DIR}")
        dockerfile_template_rel_path = project_config.get("dockerfilePath")
        docker_compose_template_rel_path = project_config.get("dockerComposePath")

        if dockerfile_template_rel_path:
            dockerfile_template_abs_path = os.path.join(CLI_ROOT_DIR, dockerfile_template_rel_path)
            target_dockerfile_path = os.path.join(project_root_path, 'Dockerfile') # Standard name
            if os.path.exists(dockerfile_template_abs_path):
                try:
                    shutil.copy(dockerfile_template_abs_path, target_dockerfile_path)
                    logger.info(f"Copied Dockerfile from {dockerfile_template_abs_path} to {target_dockerfile_path}")
                except Exception as e:
                    logger.error(f"Error copying Dockerfile from {dockerfile_template_abs_path} to {target_dockerfile_path}: {e}")
            else:
                logger.warning(f"Dockerfile template not found at {dockerfile_template_abs_path}")
        
        if docker_compose_template_rel_path:
            compose_template_abs_path = os.path.join(CLI_ROOT_DIR, docker_compose_template_rel_path)
            target_compose_path = os.path.join(project_root_path, 'docker-compose.yml') # Standard name
            if os.path.exists(compose_template_abs_path):
                try:
                    shutil.copy(compose_template_abs_path, target_compose_path)
                    logger.info(f"Copied docker-compose.yml from {compose_template_abs_path} to {target_compose_path}")
                except Exception as e:
                    logger.error(f"Error copying docker-compose.yml from {compose_template_abs_path} to {target_compose_path}: {e}")
            else:
                logger.warning(f"docker-compose.yml template not found at {compose_template_abs_path}")


def create_project_files(project_details):
    # CWD for create_project_files (and thus this function) is BASE_PATH from commands.py's init.
    # The project directory (project_details["name"] or project_details["path"]) itself is created in commands.py's init.
    create_project_structure_from_command(project_details)


def handle_in_place_init(target_dir: str, folder_name: str) -> bool:
    """
    Handles the in-place initialization of an existing directory.
    Prompts user for project details, generates devCLI-project.json,
    and runs the initCommand for the chosen project type.

    Args:
        target_dir: Absolute path to the existing project directory.
        folder_name: Base name of the project directory.

    Returns:
        True if initialization was successful and devCLI-project.json was created, False otherwise.
    """
    click.echo(f"Starting in-place initialization for project: {folder_name} at {target_dir}")
    logger.info(f"Handling in-place init for directory: {target_dir}, folder name: {folder_name}")

    # 1. Get project details, pre-filling name and path
    project_details = get_project_details(
        existing_project_name=folder_name,
        existing_project_path=target_dir
    )

    if not project_details or not project_details.get("chosen_project_type_key"):
        logger.error(f"Failed to get project details during in-place init for {folder_name}.")
        click.echo("Project detail gathering failed or was aborted. Initialization cancelled.")
        return False

    # 2. Generate devCLI-project.json
    # generate_project_json now uses project_details['path']
    try:
        generate_project_json(project_details) 
        logger.info(f"devCLI-project.json generated for {folder_name} at {project_details['path']}.")
    except Exception as e:
        logger.error(f"Failed to generate devCLI-project.json for {folder_name}: {e}", exc_info=True)
        click.echo(f"Error generating devCLI-project.json: {e}")
        return False

    # 3. Run initCommand and copy Docker files (if applicable)
    # create_project_structure_from_command also uses project_details['path']
    try:
        # This function should run initCommand *inside* project_details['path']
        # and copy Docker templates *into* project_details['path'].
        create_project_structure_from_command(project_details)
        logger.info(f"Project structure initialized for {folder_name} using command: {project_details['project_type_config'].get('initCommand')}")
    except Exception as e:
        logger.error(f"Failed during structure initialization for {folder_name}: {e}", exc_info=True)
        click.echo(f"Error during project structure initialization: {e}")
        # Note: devCLI-project.json was created, but initCommand failed. This is a partial success.
        # Depending on desired behavior, you might want to remove the json or leave it.
        # For now, we'll consider it a failure to fully init.
        return False
            
    click.echo(f"Project '{folder_name}' has been configured.")
    return True

