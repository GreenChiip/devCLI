import click, os, json, subprocess, logging
from datetime import datetime
from InquirerPy import inquirer
from dotenv import load_dotenv

from config import handle_add_alias, load_config # handle_add_alias uses logging
from utils import resolve_folder # resolve_folder uses logging

logger = logging.getLogger(__name__)


load_dotenv()
NPX_PATH = os.getenv("NPX_PATH")

config = load_config()
aliases = load_config("alias")

def get_project_details():
    """
    Prompt the user for project details and return them as a dictionary.
    """
    project_name = inquirer.text(message=f"Enter the project name:").execute()

    # resolve_folder already logs if verbose, so direct logging here might be redundant
    # unless we want to ensure it's always logged regardless of resolve_folder's internal logging.
    # For now, let's assume resolve_folder's logging is sufficient for its actions.
    target_dir = resolve_folder(project_name) # Assuming resolve_folder now takes only one arg or handles default
    if target_dir:
        original_project_name = project_name
        project_name = f"{project_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        logger.warning(f"Folder '{original_project_name}' already exists. Changed name to '{project_name}' to avoid conflicts.")
        click.echo(f"⚠️ Folder '{original_project_name}' already exists.") # User facing
        click.echo(f"⚠️ Changed name to '{project_name}' to avoid conflicts.") # User facing

    project_description = inquirer.text(message="Enter the project description:", default="A new project").execute()
    project_author = inquirer.text(message="Enter the author name:", default="Kai Stenbro").execute()
    project_type = inquirer.select(
        message="Select project type:",
        choices=["node", "python"],
        default="node"
    ).execute()

    if project_type == "node":
        node_framework = inquirer.select(
            message="Select framework:",
            choices=["NextJS-15", "NextJS-14"],
            default="NextJS-15"
        ).execute()
        project_name = f"{project_name}-{node_framework}"

    return {
        "name": project_name,
        "description": project_description,
        "author": project_author,
        "type": project_type,
        "framework": node_framework if project_type == "node" else None
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

    project_json_path = os.path.join(project_details["name"], "devCLI-project.json")
    logger.debug(f"Generating devCLI-project.json at: {project_json_path}")
    with open(project_json_path, "w") as f:
        json.dump(project_json, f, indent=4)
    logger.info(f"Created devCLI-project.json in {project_details['name']}")
    click.echo(f"📄 Created devCLI-project.json in {project_details['name']}") # User facing


def create_node_files(project_name_arg): # Changed from project_details to project_name_arg
    """
    Generate files for a Node.js project based on the selected framework.
    """
    logger.info(f"Creating Node.js files for project: {project_name_arg}")
    # Assuming project_name_arg is just the name string.
    # We might need the full project_details if other parts are used.
    # For now, let's assume NPX_PATH is defined and works.
    
    # The structure of project_details['name'] was used before, so if project_name_arg is different,
    # this might need adjustment. Assuming project_name_arg is the folder name.
    target_app_path = os.path.join(project_name_arg, "app") # Define where create-next-app should run
    os.makedirs(target_app_path, exist_ok=True) # Ensure the base project folder exists

    try:
        # Create the Next.js app inside the 'app' subdirectory of the project folder
        subprocess.run([NPX_PATH, "create-next-app@latest", target_app_path, "--typescript", "--eslint", "--tailwind", "--src-dir", "--app", "--import-alias", "@/*", "--yes"], check=True, cwd=project_name_arg)
        logger.info(f"Successfully ran create-next-app in {target_app_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during npx create-next-app for {project_name_arg}: {e}")
        click.echo(f"❌ Error creating Next.js project: {e}") # User facing
        return # Stop if create-next-app failed

    # The alias should point to the project directory, not the 'app' subdirectory directly for dev purposes.
    # So if project_name_arg is "my-next-project-NextJS-15", alias should be for "my-next-project-NextJS-15"
    # and the path it points to should be "my-next-project-NextJS-15".
    # handle_add_alias expects the alias name and the relative path from BASE_PATH.
    # If project_name_arg is already the correct relative path, then it's fine.
    handle_add_alias(aliases, project_name_arg, project_name_arg) # Alias name and folder name are the same
    logger.info(f"Alias '{project_name_arg}' added for project.")
    click.echo(f"🦄 NextJS project '{project_name_arg}' created.") # User facing
    

def create_python_files(project_name_arg): # Changed from project_details to project_name_arg
    """
    Generate files for a Python project, including Docker configuration.
    """
    logger.info(f"Creating Python files for project: {project_name_arg}")
    main_py_path = os.path.join(project_name_arg, "main.py")
    dockerfile_path = os.path.join(project_name_arg, "Dockerfile")
    docker_compose_path = os.path.join(project_name_arg, "docker-compose.yml")

    logger.debug(f"Creating main.py at {main_py_path}")
    open(main_py_path, "w").close()

    dockerfile_content = (
        "FROM python:3.9-slim\n"
        "WORKDIR /app\n"
        "COPY . .\n"
        "CMD [\"python\", \"main.py\"]"
    )
    logger.debug(f"Creating Dockerfile at {dockerfile_path} with content:\n{dockerfile_content}")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    docker_compose_content = (
        "version: '3.9'\n"
        "services:\n"
        "  app:\n"
        "    build: .\n"
        "    volumes:\n"
        "      - .:/app\n"
        "    command: python main.py"
    )
    logger.debug(f"Creating docker-compose.yml at {docker_compose_path} with content:\n{docker_compose_content}")
    with open(docker_compose_path, "w") as f:
        f.write(docker_compose_content)

    logger.info(f"Python project files and Docker configuration created for {project_name_arg}.")
    click.echo(f"🐍 Python project '{project_name_arg}' files and Docker configuration created.") # User facing



def create_project_files(project_details):
    """
    Create the appropriate files for the selected project type.
    """
    logger.debug(f"Creating project files for project: {project_details['name']}, type: {project_details['type']}")
    project_file_generators = {
        "node": create_node_files,
        "python": create_python_files
    }

    project_type = project_details["type"]
    project_name = project_details["name"] # This is the actual folder name

    if project_type in project_file_generators:
        # Before calling, ensure the main project directory exists
        # Base path for projects should come from config or be well-defined
        # Assuming BASE_PATH is imported or accessible globally for project creation path
        # project_base_creation_path = BASE_PATH 
        # full_project_path = os.path.join(project_base_creation_path, project_name)
        # os.makedirs(full_project_path, exist_ok=True)
        # logger.debug(f"Ensured base project directory exists: {full_project_path}")
        
        # The called functions (create_node_files, create_python_files)
        # will now create files inside this project_name folder.
        project_file_generators[project_type](project_name)
    else:
        logger.error(f"Unsupported project type: {project_type}")
        click.echo(f"⚠️ Unsupported project type: {project_type}") # User facing

