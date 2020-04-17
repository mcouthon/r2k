import click
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import get_config


@click.command("show")
@cli_utils.config_path_option()
def subscription_show(path: str) -> None:
    """List all existing RSS subscriptions"""
    config = get_config(path)

    if config.subscriptions:
        subscriptions = yaml.safe_dump(config.subscriptions)  # Just here to make the output nicer
        logger.info("Here are the existing subscriptions:")
        logger.secho(subscriptions, fg="white", bold=False)
    else:
        logger.info("There are no subscriptions available.\n" "Add more by running `r2k subscriptions import/add`")
