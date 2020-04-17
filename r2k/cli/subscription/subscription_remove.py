import click

from r2k.cli import cli_utils, logger
from r2k.config import get_config


@click.command("remove")
@cli_utils.config_path_option()
@click.option("-t", "--title", type=str, required=True, help="The title of the subscription")
def subscription_remove(path: str, title: str) -> None:
    """Remove a subscription from the config."""
    config = get_config(path)

    found = config.subscriptions.pop(title, False)
    config.save()

    if found:
        logger.info(f"Successfully removed `{title}` from the list of subscriptions")
    else:
        logger.info(f"Could not find `{title}` in the list of subscriptions")
