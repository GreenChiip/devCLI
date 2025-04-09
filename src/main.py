import click
from commands import run_dev, alias, code, docker, init, list_folders, update, help


@click.group(help="General commands")
def cli() -> None:
    pass


cli.add_command(code)
cli.add_command(run_dev)
cli.add_command(alias)
cli.add_command(docker)
cli.add_command(init)
cli.add_command(list_folders)
cli.add_command(help)
cli.add_command(update)


if __name__ == "__main__":
    cli()