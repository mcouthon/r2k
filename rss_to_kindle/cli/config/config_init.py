import os
import sys

import click

from rss_to_kindle.cli import cli_utils, logger
from rss_to_kindle.config import get_config


@click.command("init")
@cli_utils.config_path_option(exists=False)
@cli_utils.force_option("If set will override an existing configuration file (if it exists)")
def config_init(path, force) -> None:
    """Initialize a new configuration files."""
    if os.path.exists(path):
        if force:
            logger.warning(f"Overwriting existing configuration file in `{path}`...")
        else:
            logger.error(f"A file already exists in `{path}`.\n" f"Pass the --force flag to overwrite it.")
            sys.exit(1)

    send_from = logger.prompt(f"Please provide your gmail email address")
    kindle_address = logger.prompt(f"Please provide your free kindle address (e.g. my_kindle@kindle.com)")
    if "@" in kindle_address:
        kindle_address = kindle_address.split("@")[0]
    password = logger.prompt(f"Please provide your gmail app password", hide_input=True)
    config_obj = get_config(path)
    config_obj.reset({"send_from": send_from, "kindle_address": kindle_address, "password": password})
    logger.info("Successfully set the configuration!")
