import click
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import config as _config


@click.command("show")
@cli_utils.config_path_option()
def config_show() -> None:
    """Show all the available configuration."""
    result = _config.as_dict()
    if "password" in result:
        result["password"] = "XXXXXXX"
    logger.info(yaml.safe_dump(result))
