import click
import orjson as json
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import config as _config


@click.command("show")
@cli_utils.config_path_option()
@click.option(
    "-j",
    "--json",
    "is_json",
    is_flag=True,
    help="When passed the output will be in JSON format (e.g. for use with jq).\n"
    "Use with the --no-ansi flag for best results",
)
def config_show(is_json: bool) -> None:
    """Show all the available configuration."""
    result = _config.as_dict()
    if "password" in result:
        result["password"] = "XXXXXXX"
    if is_json:
        logger.info(json.dumps(result))
    else:
        logger.info(yaml.safe_dump(result))
