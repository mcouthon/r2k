import sys

import click

from r2k.cli import cli_utils, logger
from r2k.config import get_config


@click.command("set")
@click.argument("key")
@cli_utils.config_path_option()
@cli_utils.force_option("If set will override an existing value (if it exists)")
def config_set(key: str, path: str, force: bool) -> None:
    """Set a value in the config."""
    _config = get_config(path)
    if key in _config:
        if force:
            logger.warning("Overriding an existing value...")
        else:
            logger.error(f"A value already exists for `{key}`.\n" f"Pass the --force flag to overwrite it.")
            sys.exit(1)

    value = logger.prompt(f"Please provide a new value for {key}")
    setattr(_config, key, value)
    logger.info("Configuration successfully updated!")
