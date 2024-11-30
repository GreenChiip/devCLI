import os
import subprocess # type: ignore
import click
from utils import select_dir_with_package_json, load_aliases, save_aliases

@click.command("run", help="Run 'npm run dev' in the specified folder.")
@click.argument('folder_name')
@click.option("--alias", "-a", help="Use an alias instead of a folder name.", is_flag=True)
@click.option("--code", "-c", help="Open VScode", is_flag=True)
def run_dev(folder_name, alias, code):
    base_path = "E:\\Develepment (DEV)"
    if alias:
        aliases = load_aliases()
        if folder_name not in aliases:
            click.echo(f"Error: Alias '{folder_name}' does not exist.")
            return
        folder_name = aliases[folder_name]

    target_dir = os.path.join(base_path, folder_name)

    # Check if the directory exists
    if not os.path.exists(target_dir):
        click.echo(f"Error: Folder '{target_dir}' does not exist.")
        return
    

    # Check if package.json exists in the target folder
    if not os.path.exists(os.path.join(target_dir, "package.json")):
        click.echo(f"Error: 'package.json' does not exist in the folder '{target_dir}'.")
        # Check if there are any directories in the target folder
        target_dir = select_dir_with_package_json(target_dir)

    # Change directory to the target folder
    os.chdir(target_dir)

    if code:
        vscode = r"C:\\Users\\Stenbro\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"  # Update this path if necessary
        subprocess.run([vscode, "."], check=True)

    npm_path = r"C:\\Program Files\\nodejs\\npm.cmd"  # Update this path if necessar

    # Run 'npm run dev' in the target folder
    try:
        subprocess.run([npm_path, "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command 'npm run dev' failed with exit code {e.returncode}.")
        subprocess.run([npm_path, "i", "--force"], check=True)
    except FileNotFoundError:
        click.echo("Error: 'npm' is not installed or not in your PATH.")


@click.command("alias", help="Add or remove an alias.")
@click.argument("action", type=click.Choice(["add", "remove", "list"], case_sensitive=False))
@click.argument("alias_name", required=False)
@click.argument("alias_for", required=False)
def alias(action, alias_name, alias_for):
    aliases = load_aliases()
    if action == "add" and alias_name and alias_for:
        if alias_name in aliases:
            click.echo(f"Error: Alias '{alias_name}' already exists.")
            return
        if not alias_for:
            click.echo("Error: 'alias_for' is required when adding an alias.")
            return
        aliases[alias_name] = alias_for
        save_aliases(aliases)
        click.echo(f"Alias '{alias_name}' added for '{alias_for}'.")

    elif action == "remove" and alias_name:
        if alias_name not in aliases:
            click.echo(f"Error: Alias '{alias_name}' does not exist.")
            return
        del aliases[alias_name]
        save_aliases(aliases)
        click.echo(f"Alias '{alias_name}' removed.")

    elif action == "list":
        """List all aliases."""
        aliases = load_aliases()
        if not aliases:
            click.echo("No aliases found.")
            return
        click.echo("Aliases:")
        for alias_name, alias_for in aliases.items():
            click.echo(f" {alias_name} -> {alias_for}")

