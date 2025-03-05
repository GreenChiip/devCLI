import click, os
from dotenv import load_dotenv
from InquirerPy import inquirer
from utils import open_in_vscode, run_npm_dev, isBun, run_bun_dev, select_dir_with_package_json, resolve_folder, validate_package_json, change_directory, run_docker_compose_up
from alias import handle_add_alias, handle_remove_alias, handle_list_aliases, load_aliases
from create import get_project_details, generate_project_json, create_project_files

load_dotenv()
BASE_PATH = os.getenv("BASE_PATH")

@click.command("run", help="Run 'npm run dev' in the specified folder.")
@click.argument('folder_name')
def run_dev(folder_name):
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        click.echo("No valid directory selected.")
        return
    
    if not validate_package_json(target_dir):
        target_dir = select_dir_with_package_json(target_dir)
        if not target_dir:
            click.echo(f"Error: 'package.json' does not exist in the folder '{target_dir}'.")
            return

    change_directory(target_dir)

    if isBun(target_dir):
        click.echo("Detected 'bun.lock'. Running 'bun'...")
        run_bun_dev()
    else:
        run_npm_dev()

@click.command("alias", help="Add or remove an alias.")
@click.argument("action", type=click.Choice(["add", "remove", "list"], case_sensitive=False))
@click.argument("alias_name", required=False)
@click.argument("alias_for", required=False)
def alias(action, alias_name, alias_for):
    aliases = load_aliases()
    if action == "add":
        handle_add_alias(aliases, alias_name, alias_for)
    elif action == "remove":
        handle_remove_alias(aliases, alias_name)
    elif action == "list":
        handle_list_aliases(aliases)


@click.command("code", help="Opens the specified folder in VScode.")
@click.argument('folder_name')
@click.option("--alias", "-a", help="Use an alias instead of a folder name.", is_flag=True)
def code(folder_name, alias):
    # target_dir = os.path.join(base_path, folder_name)
    target_dir = resolve_folder(folder_name, alias)
    if not target_dir:
        return
    
    change_directory(target_dir)
    open_in_vscode()
    

@click.command("docker", help="Run docker-compose up in the specified folder.")
@click.argument('folder_name')
@click.argument('state', required=True, type=click.Choice(["up", "down"], case_sensitive=False))
@click.option("--alias", "-a", help="Use an alias instead of a folder name.", is_flag=True)
@click.option("--build", "-b", help="Build images before starting containers.", is_flag=True)
@click.option("--detach", "-d", help="Run containers in the background.", is_flag=True)
def docker(folder_name, state, alias, build, detach):
    target_dir = resolve_folder(folder_name, alias)
    if not target_dir:
        return

    change_directory(target_dir)
    run_docker_compose_up(state, build, detach)


@click.command("init", help="Create a new project folder with a devCLI-project.json file.")
def init():
    """
    Initialize a new project with a devCLI-project.json file and prompt the user for details.
    """
    # Gather project details
    project_details = get_project_details()

    os.makedirs(os.path.join(BASE_PATH, project_details["name"]))

    # Generate devCLI-project.json
    generate_project_json(project_details)

    # Add folder to aliases if confirmed
    if inquirer.confirm(message="Do you want to add this folder to your aliases?").execute():
        alias_name = inquirer.text(message="Enter alias name:", default=project_details["name"]).execute()
        aliases = load_aliases()
        if alias_name in aliases:
            click.echo(f"⚠️ Alias '{alias_name}' already exists.")
            return
        handle_add_alias(aliases, alias_name, project_details["name"])

    # Create project-specific files
    create_project_files(project_details)

    click.echo(f"✅ Project '{project_details['name']}' initialized successfully!")
