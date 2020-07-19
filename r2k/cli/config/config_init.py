import errno
import os
import sys

import click

from r2k.cli import cli_utils, logger
from r2k.config import Config
from r2k.constants import Parser

from .prompts import Prompt


@click.command("init")
@cli_utils.config_path_option(exists=False)
@cli_utils.force_option("If set will override an existing configuration file (if it exists)")
def config_init(path: str, force: bool) -> None:
    """Initialize a new configuration files."""
    create_config_dir_if_not_exists(path)
    validate_config_overwrite(path, force)

    new_config = get_new_config()
    new_config.save(path)
    logger.info("Successfully set the configuration!")


def get_new_config() -> Config:
    """Ask the user to fill in all the necessary information, and return the resulting dict"""
    send_from = Prompt.get("send_from")
    password = Prompt.get("password")
    kindle_address = Prompt.get("kindle_address")
    parser = Prompt.get("parser")
    return Config(
        feeds={}, send_from=send_from, kindle_address=kindle_address, password=password, parser=Parser(parser)
    )


def validate_config_overwrite(path: str, force: bool) -> None:
    """Make sure the --force flag is passed where applicable"""
    if os.path.exists(path):
        if force:
            logger.warning(f"Overwriting existing configuration file in `{path}`...")
        else:
            logger.error(f"A file already exists in `{path}`.\nPass the --force flag to overwrite it.")
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
