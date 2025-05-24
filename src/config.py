import os, json, logging, re
from dotenv import load_dotenv
from InquirerPy import inquirer
import click

logger = logging.getLogger(__name__)

load_dotenv()
logger.debug(f"CONFIG_PATH from env: {os.getenv('CONFIG_PATH')}")
logger.debug(f"ALIAS_PATH from env: {os.getenv('ALIAS_PATH')}")
CONFIG_PATH = os.getenv("CONFIG_PATH")
ALIAS_PATH = os.getenv("ALIAS_PATH")
BASE_PATH = os.getenv("BASE_PATH")


def load_config(pathC = "config"):
    """
    Load the configuration from the JSON file.
    """
    path = CONFIG_PATH if pathC == "config" else ALIAS_PATH
    logger.debug(f"Loading config from path: {path}")
    if not os.path.exists(path):
        logger.error(f"Config file not found at {path}.")
        return {}

    try:
        with open(path, "r") as f:
            config_data = json.load(f)
            logger.debug(f"Config loaded successfully from {path}: {config_data}")
            return config_data
    except json.JSONDecodeError as e:
        logger.error(f"Error loading JSON config from {path}: {e}")
        logger.debug(e, exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading config from {path}: {e}")
        logger.debug(e, exc_info=True)
        return {}

def save_config(config_data, pathC="config"):
    """
    Save the configuration to the JSON file.
    """
    path = CONFIG_PATH if pathC == "config" else ALIAS_PATH
    logger.debug(f"Saving config to path: {path}. Data: {config_data}")
    try:
        with open(path, "w") as f:
            json.dump(config_data, f, indent=4)
        logger.info(f"Config saved successfully to {path}.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving config to {path}: {e}")
        logger.debug(e, exc_info=True)


def handle_list_aliases(aliases):
    """
    List all aliases.
    """
    logger.debug("Listing aliases.")
    if not aliases:
        logger.info("No aliases found to list.")
        # It's okay to use click.echo for direct user output not related to errors/status
        import click 
        click.echo("No aliases found.")
        return

    import click # for styled output if needed, or just log
    click.echo("Aliases:")
    for alias_name, alias_path in aliases.items():
        logger.debug(f"Alias: {alias_name} -> {alias_path}")
        click.echo(f"  {alias_name} -> {alias_path}")


def handle_remove_alias(aliases_data, alias_name_to_remove):
    """
    Remove an existing alias from the aliases file.
    """
    logger.debug(f"Attempting to remove alias: {alias_name_to_remove}")
    if not alias_name_to_remove:
        logger.error("Error: 'alias_name' is required to remove an alias.")
        click.echo("Error: 'alias_name' is required to remove an alias.")
        return

    if alias_name_to_remove not in aliases_data:
        logger.error(f"Error: Alias '{alias_name_to_remove}' does not exist.")
        click.echo(f"Error: Alias '{alias_name_to_remove}' does not exist.")
        return

    confirm_remove = inquirer.confirm(
        message=f"Are you sure you want to remove the alias '{alias_name_to_remove}'?",
        default=False
    ).execute()
    if not confirm_remove:
        logger.info(f"Alias removal cancelled for '{alias_name_to_remove}'.")
        click.echo("Alias removal cancelled.")
        return

    del aliases_data[alias_name_to_remove]
    save_config(aliases_data, "alias")
    logger.info(f"Alias '{alias_name_to_remove}' removed.")
    click.echo(f"Alias '{alias_name_to_remove}' removed.")


def handle_add_alias(aliases_data, new_alias_name, path_to_alias):
    """
    Add a new alias to the aliases file.
    """
    logger.debug(f"Attempting to add alias: {new_alias_name} for path: {path_to_alias}")
    if not new_alias_name or not path_to_alias:
        logger.error("Error: Both 'Alias name' and 'Alias for' are required to add an alias.")
        import click # For user guidance
        click.echo("Error: Both 'Alias name' and 'Alias for' are required to add an alias.")
        click.echo("\n\nUsage: alias add <Alias name> <Alias for>")
        click.echo("Example: alias add myfolder Projects\\myfolder\n\n")
        return

    # Validate alias_name format
    if not re.match(r"^[a-zA-Z0-9_-]+$", new_alias_name):
        logger.error(f"Error: Alias name '{new_alias_name}' is invalid. Only alphanumeric characters, hyphens, and underscores are allowed.")
        import click # For user feedback
        click.echo(f"Error: Alias name '{new_alias_name}' is invalid. Only alphanumeric characters, hyphens, and underscores are allowed.")
        return

    if new_alias_name in aliases_data:
        logger.error(f"Error: Alias '{new_alias_name}' already exists.")
        import click # For user feedback
        click.echo(f"Error: Alias '{new_alias_name}' already exists.")
        return
    
    # It's good practice to ensure BASE_PATH is available for constructing target_dir
    if not BASE_PATH:
        logger.error("BASE_PATH is not set. Cannot validate target directory for alias.")
        return

    target_dir = os.path.join(BASE_PATH, path_to_alias)
    logger.debug(f"Validating target directory for new alias: {target_dir}")
    if not os.path.exists(target_dir):
        logger.error(f"Error: Target directory '{target_dir}' does not exist for alias '{new_alias_name}'.")
        import click # For user feedback
        click.echo(f"Error: Target directory '{target_dir}' does not exist.")
        return

    aliases_data[new_alias_name] = path_to_alias
    save_config(aliases_data, "alias")
    logger.info(f"Alias '{new_alias_name}' added for '{path_to_alias}'.")
    import click # For user confirmation
    click.echo(f"Alias '{new_alias_name}' added for '{path_to_alias}'.")