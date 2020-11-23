import click
from pick import pick

from r2k.cli import cli_utils, logger
from r2k.config import config


@click.command("remove")
@cli_utils.config_path_option()
@click.option("-t", "--title", type=str, required=False, help="The title of the feed")
def feed_remove(title: str) -> None:
    """Remove a feed from the config."""
    if not title:
        feed_titles = list(config.feeds.keys())
        title, _ = pick(feed_titles, "Please choose the feed to remove")

    found = config.feeds.pop(title, False)
    config.save()

    if found:
        logger.info(f"Successfully removed `{title}` from the list of feeds")
    else:
        logger.info(f"Could not find `{title}` in the list of feeds")
