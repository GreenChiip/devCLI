import click, os
from dotenv import load_dotenv
from InquirerPy import inquirer
from utils import run_install_package, updateRepo, open_in_vscode, run_npm_dev, is_bun, PROJECT_DETECTORS, TAG_COLORS, run_bun_dev, select_dir_with_package_json, resolve_folder, validate_package_json, change_directory, run_docker_compose_up
from conifg import handle_add_alias, handle_remove_alias, handle_list_aliases, load_config, save_config
from create import get_project_details, generate_project_json, create_project_files

load_dotenv()
BASE_PATH = os.getenv("BASE_PATH")

config = load_config()
aliases = load_config("alias")

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

    if is_bun(target_dir):
        click.echo("Detected 'bun.lock'. Running 'bun'...")
        run_bun_dev()
    else:
        run_npm_dev()

@click.command("alias", help="Add or remove an alias.")
@click.argument("action", required=False)
@click.argument("alias_name", required=False)
@click.argument("alias_for", required=False)
def alias(action, alias_name, alias_for):
    if action is None:
        handle_list_aliases(aliases)
        return
    
    if action not in ["add", "remove"]:
        click.echo("Error: Invalid action. Use 'add' or 'remove'.")
        return
        
    if action == "add":
        handle_add_alias(aliases, alias_name, alias_for)
        return
    
    if action == "remove":
        handle_remove_alias(aliases, alias_name)
        return



@click.command("code", help="Opens the selected folder in VScode. (default: dev)")
@click.argument('folder_name', required=True, type=str)
def code(folder_name = "dev"):
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        return
    
    change_directory(target_dir)
    open_in_vscode()
    

@click.command("docker", help="Run 'docker-compose up' in the selected folder.")
@click.argument('folder_name', required=True, type=str) 
@click.argument('state', required=True, type=click.Choice(["up", "down"], case_sensitive=False))
@click.option("--build", "-b", help="Build images before starting containers.", is_flag=True)
@click.option("--detach", "-d", help="Run containers in the background.", is_flag=True)
def docker(folder_name, state, build, detach):
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        return

    change_directory(target_dir)
    run_docker_compose_up(state, build, detach)


@click.command("init", help="Create a new project folder with a devCLI-project.json file. (not implemented yet)")
def init():
    """
    Initialize a new project with a devCLI-project.json file and prompt the user for details.
    """
    click.echo("Not implemented yet.")
    return
    # Gather project details
    project_details = get_project_details()

    os.makedirs(os.path.join(BASE_PATH, project_details["name"]))

    # Generate devCLI-project.json
    generate_project_json(project_details)

    # Add folder to aliases if confirmed
    if inquirer.confirm(message="Do you want to add this folder to your aliases?").execute():
        alias_name = inquirer.text(message="Enter alias name:", default=project_details["name"]).execute()
        aliases
        if alias_name in aliases:
            click.echo(f"⚠️ Alias '{alias_name}' already exists.")
            return
        handle_add_alias(aliases, alias_name, project_details["name"])

    # Create project-specific files
    create_project_files(project_details)

    click.echo(f"✅ Project '{project_details['name']}' initialized successfully!")


@click.command("list", help="List all available folders.")
def list_folders():
    """
    List all available folders in the BASE_PATH with detected project type tags.
    """
    folders = [
        d for d in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, d))
    ]

    if not folders:
        click.echo("No folders found.")
        return

    click.echo("Available folders:")
    for folder in folders:
        full_path = os.path.join(BASE_PATH, folder)
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

        click.echo(f"  - {click.style(folder_display)}")


@click.command("update", help="Get the latest version of the projects git repo (default: dev).")
@click.argument('folder_name', required=False, default="dev")
@click.option('--force', is_flag=True, help="Force update even if no changes detected.")
@click.option('--no-pull', is_flag=True, help="Skip pulling changes from the repository.")
def update(folder_name, force = False , no_pull = False):
    """
    Update the devCLI to the latest version from GitHub.
    """
    target_dir = resolve_folder(folder_name)
    if not target_dir:
        click.echo("No valid directory selected.")
        return
    
    change_directory(target_dir)
    if updateRepo(force, no_pull):
        click.echo("Update completed successfully!")
        # Check if the project has a package.json file and ask if to run npm install if it does
        if validate_package_json(target_dir):
            if inquirer.confirm(message="Do you want to install packages?", default=True).execute():
                if is_bun(target_dir):
                    click.echo("Detected 'bun.lock'. Running 'bun install'...")
                    run_install_package("bun")
                else:
                    click.echo("Running 'npm install'...")
                    run_install_package("npm")
        else:
            click.echo("No package.json found. Skipping npm install.")
        
    else:
        click.echo("No updates available or an error occurred.")


@click.command("start", help="Start the current default selected project.")
@click.option('setProject', "--set", help="Set a project to start by default.", default=None)
@click.option('code', '--code', is_flag=True, help="Open the project in VSCode.")
def start(setProject = None, code = True):
    """
    Start the current selected project.
    """
    if setProject:
        target_dir = resolve_folder(setProject)
        if not target_dir:
            click.echo("No valid directory selected.")
            return
        config["currentProject"] = setProject
        save_config(config)
        click.echo(f"Current project set to: {setProject}")
        return

    target_dir = resolve_folder(config["currentProject"])
    change_directory(target_dir)

    if not validate_package_json(target_dir):
        open_in_vscode()
        return
    

    if is_bun(target_dir):
        click.echo("Detected 'bun.lock'. Running 'bun'...")
        open_in_vscode()
        run_bun_dev()
    else:
        open_in_vscode()
        run_npm_dev()


@click.command("cd", help="Change directory to the specified folder.")
@click.argument('folder_name', required=False, type=str, default=None)
def cd(folder_name):
   if folder_name == None:
        target_dir = resolve_folder(config["currentProject"])
        change_directory(target_dir)
        click.echo(f"Changed directory to: {target_dir}")
   else:
        target_dir = resolve_folder(folder_name)
        if not target_dir:
            click.echo("No valid directory selected.")
            return
        change_directory(target_dir)
        click.echo(f"Changed directory to: {target_dir}")
       

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
            click.echo(commands[command].get_help(click.Context(commands[command])))
            click.echo("")
        else:
            # print "Error" in a red color
            click.echo(f"Error: Command '{command}' not found.", fg="red")
            click.echo()
    else:
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
        click.echo("   help  - Show help information.")
        click.echo("")
