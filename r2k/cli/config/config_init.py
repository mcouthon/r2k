import errno
import os
import sys

import click

from r2k.cli import cli_utils, logger
from r2k.config import config


@click.command("init")
@cli_utils.config_path_option(exists=False)
@cli_utils.force_option("If set will override an existing configuration file (if it exists)")
def config_init(path: str, force: bool) -> None:
    """Initialize a new configuration files."""
    create_config_dir_if_not_exists(path)
    validate_config_overwrite(path, force)

    send_from = logger.prompt("Please provide your gmail email address")
    password = logger.prompt("Please provide your gmail app password", hide_input=True)
    kindle_address = logger.prompt("Please provide your free kindle address (e.g. my_kindle@kindle.com)")
    config.reset({"send_from": send_from, "kindle_address": kindle_address, "password": password})
    logger.info("Successfully set the configuration!")


def validate_config_overwrite(path: str, force: bool) -> None:
    if os.path.exists(path):
        if force:
            logger.warning(f"Overwriting existing configuration file in `{path}`...")
        else:
            logger.error(f"A file already exists in `{path}`.\n" f"Pass the --force flag to overwrite it.")
            sys.exit(1)


def create_config_dir_if_not_exists(path: str) -> None:
    """Create the config dir if it doesn't already exist"""
    dirname = os.path.dirname(path)
    try:
        os.makedirs(dirname)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
