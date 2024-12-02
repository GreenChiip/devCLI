import os, json, click
from dotenv import load_dotenv

load_dotenv()
ALIAS_PATH = os.getenv("ALIAS_PATH")
BASE_PATH = os.getenv("BASE_PATH")


# Ensure the alias file exists
def ensure_alias_file():
    if not os.path.exists(ALIAS_PATH):
        with open(ALIAS_PATH, "w") as f:
            json.dump({}, f)

# Load aliases from the JSON file
def load_aliases():
    ensure_alias_file()
    with open(ALIAS_PATH, "r") as f:
        return json.load(f)

# Save aliases to the JSON file
def save_aliases(aliases):
    with open(ALIAS_PATH, "w") as f:
        json.dump(aliases, f, indent=4)


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


def handle_remove_alias(aliases, alias_name):
    """
    Remove an existing alias from the aliases file.
    """
    if not alias_name:
        click.echo("Error: 'alias_name' is required to remove an alias.")
        return

    if alias_name not in aliases:
        click.echo(f"Error: Alias '{alias_name}' does not exist.")
        return

    del aliases[alias_name]
    save_aliases(aliases)
    click.echo(f"Alias '{alias_name}' removed.")


def handle_add_alias(aliases, alias_name, alias_for):
    """
    Add a new alias to the aliases file.
    """
    if not alias_name or not alias_for:
        click.echo("Error: Both 'Alias name' and 'Alias for' are required to add an alias.")
        click.echo("\n\nUsage: alias add <Alias name> <Alias for>")
        click.echo("Example: alias add myfolder Projects\myfolder\n\n")
        return

    if alias_name in aliases:
        click.echo(f"Error: Alias '{alias_name}' already exists.")
        return

    aliases[alias_name] = alias_for
    save_aliases(aliases)
    click.echo(f"Alias '{alias_name}' added for '{alias_for}'.")