import click

from .config_init import config_init
from .config_set import config_set
from .config_show import config_show


@click.group()
def config() -> None:
    """Interact with the application config."""
    pass


config.add_command(config_init)
config.add_command(config_show)
config.add_command(config_set)
