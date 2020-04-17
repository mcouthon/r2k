import click
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import get_config


@click.command("show")
@cli_utils.config_path_option()
def feed_show(path: str) -> None:
    """List all existing RSS feeds."""
    config = get_config(path)

    if config.feeds:
        feeds = yaml.safe_dump(config.feeds)  # Just here to make the output nicer
        logger.info("Here are the existing feeds:")
        logger.secho(feeds, fg="white", bold=False)
    else:
        logger.info("There are no feeds available.\n" "Add more by running `r2k feeds import/add`")
