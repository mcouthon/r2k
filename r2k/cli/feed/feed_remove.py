import click

from r2k.cli import cli_utils, logger
from r2k.config import config


@click.command("remove")
@cli_utils.config_path_option()
@click.option("-t", "--title", type=str, required=True, help="The title of the feed")
def feed_remove(title: str) -> None:
    """Remove a feed from the config."""
    found = config.feeds.pop(title, False)
    config.save()

    if found:
        logger.info(f"Successfully removed `{title}` from the list of feeds")
    else:
        logger.info(f"Could not find `{title}` in the list of feeds")
