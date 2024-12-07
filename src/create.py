import click, os, json
from InquirerPy import inquirer



def get_project_details():
    """
    Prompt the user for project details and return them as a dictionary.
    """
    project_name = inquirer.text(message="Enter the project name:", default="MyProject").execute()
    project_description = inquirer.text(message="Enter the project description:", default="A new project").execute()
    project_author = inquirer.text(message="Enter the author name:", default="Anonymous").execute()
    project_type = inquirer.select(
        message="Select project type:",
        choices=["node", "python", "go"],
        default="node"
    ).execute()

    return {
        "name": project_name,
        "description": project_description,
        "author": project_author,
        "type": project_type,
    }


def generate_project_json(project_folder, project_details):
    """
    Create the project.json file with project details and commands.
    """
    project_type = project_details["type"]
    project_json = {
        "name": project_details["name"],
        "description": project_details["description"],
        "author": project_details["author"],
        "commands": {
            "npm": "npm run dev" if project_type == "node" else None,
            "docker": "docker-compose up --build" if project_type in ["python", "go"] else None,
        }
    }

    project_json_path = os.path.join(project_folder, "devCLI-project.json")
    with open(project_json_path, "w") as f:
        json.dump(project_json, f, indent=4)
    click.echo(f"📄 Created devCLI-project.json in {project_folder}")


def create_node_files(project_folder):
    """
    Generate files for a Node.js project.
    """
    package_json = {
        "name": "node-project",
        "version": "1.0.0",
        "scripts": {
            "dev": "node index.js"
        }
    }
    with open(os.path.join(project_folder, "package.json"), "w") as f:
        json.dump(package_json, f, indent=4)

    open(os.path.join(project_folder, "index.js"), "w").close()
    click.echo("✨ Node.js project files created.")


def create_python_files(project_folder):
    """
    Generate files for a Python project, including Docker configuration.
    """
    open(os.path.join(project_folder, "main.py"), "w").close()

    dockerfile = (
        "FROM python:3.9-slim\n"
        "WORKDIR /app\n"
        "COPY . .\n"
        "CMD [\"python\", \"main.py\"]"
    )
    with open(os.path.join(project_folder, "Dockerfile"), "w") as f:
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
    with open(os.path.join(project_folder, "docker-compose.yml"), "w") as f:
        f.write(docker_compose)

    click.echo("🐍 Python project files and Docker configuration created.")



def create_project_files(project_folder, project_type):
    """
    Create the appropriate files for the selected project type.
    """
    project_file_generators = {
        "node": create_node_files,
        "python": create_python_files
    }

    if project_type in project_file_generators:
        project_file_generators[project_type](project_folder)
    else:
        click.echo(f"⚠️ Unsupported project type: {project_type}")

