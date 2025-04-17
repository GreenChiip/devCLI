import os, json, click
from dotenv import load_dotenv

load_dotenv()
CONFIG_PATH = os.getenv("CONFIG_PATH")
ALIAS_PATH = os.getenv("ALIAS_PATH")
BASE_PATH = os.getenv("BASE_PATH")


def load_config(pathC = "config"):
    """
    Load the configuration from the JSON file.
    """
    path = CONFIG_PATH if pathC == "config" else ALIAS_PATH
    if not os.path.exists(path):
        click.echo(f"Config file not found at {path}.")
        return {}

    with open(path, "r") as f:
        try:
            config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            click.echo(f"Error loading config: {e}")
            return {}
        
def save_config(config, pathC="config"):
    """
    Save the configuration to the JSON file.
    """
    path = CONFIG_PATH if pathC == "config" else ALIAS_PATH
    with open(path, "w") as f:
        json.dump(config, f, indent=4)


def handle_list_aliases(aliases):
    """
    List all aliases.
    """
    if not aliases:
        click.echo("No aliases found.")
        return

    click.echo("Aliases:")
    for alias_name, alias_for in aliases.items():
        click.echo(f"  {alias_name} -> {alias_for}")


def handle_remove_alias(alias, alias_name):
    """
    Remove an existing alias from the aliases file.
    """
    if not alias_name:
        click.echo("Error: 'alias_name' is required to remove an alias.")
        return

    if alias_name not in "alias":
        click.echo(f"Error: Alias '{alias_name}' does not exist.")
        return

    del alias["alias_name"]
    save_config(alias, "alias")
    click.echo(f"Alias '{alias_name}' removed.")


def handle_add_alias(alias, alias_name, alias_for):
    """
    Add a new alias to the aliases file.
    """
    if not alias_name or not alias_for:
        click.echo("Error: Both 'Alias name' and 'Alias for' are required to add an alias.")
        click.echo("\n\nUsage: alias add <Alias name> <Alias for>")
        click.echo("Example: alias add myfolder Projects\myfolder\n\n")
        return

    if alias_name in alias:
        click.echo(f"Error: Alias '{alias_name}' already exists.")
        return
    
    target_dir = os.path.join(BASE_PATH, alias_for)
    if not os.path.exists(target_dir):
        click.echo(f"Error: Target directory '{target_dir}' does not exist.")
        return

    alias[alias_name] = alias_for
    save_config(alias, "alias")
    click.echo(f"Alias '{alias_name}' added for '{alias_for}'.")