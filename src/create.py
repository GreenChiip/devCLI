import click, os, json, subprocess
from datetime import datetime
from InquirerPy import inquirer
from dotenv import load_dotenv

from conifg import handle_add_alias, load_config
from utils import resolve_folder


load_dotenv()
NPX_PATH = os.getenv("NPX_PATH")

config = load_config()
aliases = load_config("alias")

def get_project_details():
    """
    Prompt the user for project details and return them as a dictionary.
    """
    project_name = inquirer.text(message=f"Enter the project name:").execute()

    target_dir = resolve_folder(project_name, False)
    if target_dir:
        project_name = f"{project_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        click.echo(f"⚠️ Folder '{project_name}' already exists.")
        click.echo(f"⚠️ Changed name to '{project_name}' to avoid conflicts.")

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
    with open(project_json_path, "w") as f:
        json.dump(project_json, f, indent=4)
    click.echo(f"📄 Created devCLI-project.json in {project_details['name']}")


def create_node_files(project_details):
    """
    Generate files for a Node.js project based on the selected framework.
    """
    
    subprocess.run([NPX_PATH, "create-next-app@latest", "app", "--yes"], check=True)
    handle_add_alias(aliases, project_details['name'], f"{project_details['name']}/app")
    click.echo("🦄 NextJS project created.")
    



def create_python_files(project_details):
    """
    Generate files for a Python project, including Docker configuration.
    """
    open(os.path.join(project_details['name'], "main.py"), "w").close()

    dockerfile = (
        "FROM python:3.9-slim\n"
        "WORKDIR /app\n"
        "COPY . .\n"
        "CMD [\"python\", \"main.py\"]"
    )
    with open(os.path.join(project_details['name'], "Dockerfile"), "w") as f:
        f.write(dockerfile)

    docker_compose = (
        "version: '3.9'\n"
        "services:\n"
        "  app:\n"
        "    build: .\n"
        "    volumes:\n"
        "      - .:/app\n"
        "    command: python main.py"
    )
    with open(os.path.join(project_details["name"], "docker-compose.yml"), "w") as f:
        f.write(docker_compose)

    click.echo("🐍 Python project files and Docker configuration created.")



def create_project_files(project_details):
    """
    Create the appropriate files for the selected project type.
    """
    project_file_generators = {
        "node": create_node_files,
        "python": create_python_files
    }

    if project_details["type"] in project_file_generators:
        project_file_generators[project_details["type"]](project_details["name"])
    else:
        click.echo(f"⚠️ Unsupported project type: {project_details['type']}")

