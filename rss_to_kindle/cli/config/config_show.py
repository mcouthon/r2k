import yaml
import click

from rss_to_kindle.cli import cli_utils, logger
from rss_to_kindle.config import get_config


@click.command("show")
@cli_utils.config_path_option()
def config_show(path) -> None:
    """Show all the available configuration."""

    _config = get_config(path)
    result = _config.as_dict()
    if "password" in result:
        result["password"] = "XXXXXXX"
    logger.info(yaml.safe_dump(result))
