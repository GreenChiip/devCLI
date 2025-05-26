import sys
import click, logging, os
from commands import run_dev, alias, code, docker, init, list_folders, update, help, start, config_cmd

# Get a logger for this module
logger = logging.getLogger(__name__)

@click.group(help="General commands")
@click.option('--verbose', is_flag=True, help='Enable verbose output for debugging.')
def cli(verbose: bool) -> None:
    # Console logging
    initial_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=initial_level, format='%(levelname)s: %(name)s - %(message)s') # Added %(name)s

    # File logging
    log_file_dir = os.path.expanduser(os.path.join('~', '.devcli'))
    log_file_path = os.path.join(log_file_dir, 'devcli.log')
    
    try:
        os.makedirs(log_file_dir, exist_ok=True)
        logger.debug(f"Log directory ensured: {log_file_dir}")

        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG level to file
        
        logging.getLogger().addHandler(file_handler)
        logger.info(f"File logging configured at: {log_file_path}")
        
    except Exception as e:
        # Use a basic print here as logging might not be fully set up if this fails
        print(f"Error setting up file logging: {e}", file=sys.stderr)


cli.add_command(code)
cli.add_command(run_dev)
cli.add_command(alias)
cli.add_command(docker)
cli.add_command(init)
cli.add_command(list_folders)
cli.add_command(help)
cli.add_command(update)
cli.add_command(start)
cli.add_command(config_cmd)


if __name__ == "__main__":
    # Example of using the module-level logger, though cli() itself won't use it directly for its messages
    # logger.debug("CLI starting") 
    cli()