import click
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import get_config


@click.command("show")
@cli_utils.config_path_option()
def config_show(path: str) -> None:
    """Show all the available configuration."""
    _config = get_config(path)
    result = _config.as_dict()
    if "password" in result:
        result["password"] = "XXXXXXX"
    logger.info(yaml.safe_dump(result))
