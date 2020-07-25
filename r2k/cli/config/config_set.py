import sys

import click

from r2k.cli import cli_utils, logger
from r2k.config import config as _config

from .prompts import Prompt


@click.command("set")
@click.option("-k", "--key", type=click.Choice(_config.fields()), required=True, help="The config key to set")
@cli_utils.config_path_option()
@cli_utils.force_option("If set will override an existing value (if it exists)")
def config_set(key: str, force: bool) -> None:
    """Set a value in the config."""
    if getattr(_config, key):
        if force:
            logger.warning("Overriding an existing value...")
        else:
            logger.error(f"A value already exists for `{key}`.\nPass the --force flag to overwrite it.")
            sys.exit(1)

    value = Prompt.get(key)

    setattr(_config, key, value)
    logger.info("Configuration successfully updated!")
