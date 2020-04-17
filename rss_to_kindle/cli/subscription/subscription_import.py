import sys
from xml.etree import ElementTree

import click
import yaml

from rss_to_kindle.cli import cli_utils, logger, unicode
from rss_to_kindle.config import get_config


@click.command("import")
@cli_utils.config_path_option()
@click.argument("opml-path", required=True, type=click.types.Path(exists=True))
@cli_utils.force_option("If set will update existing subscriptions")
def subscription_import(path, opml_path, force) -> None:
    """Import subscriptions from an OPML file."""
    subscriptions = convert_opml_to_dict(opml_path)
    config = get_config(path)

    validate_conflicts(subscriptions, config, force)

    config.subscriptions.update(subscriptions)
    config.save()

    logger.info("Successfully imported the subscriptions!")


def validate_conflicts(subscriptions, config, force) -> None:
    new_subscriptions = set(subscriptions.keys())
    old_subscriptions = set(config.subscriptions.keys())
    conflicts = new_subscriptions & old_subscriptions
    if conflicts:
        conflicts = sorted(list(conflicts))
        conflicts_str = yaml.safe_dump(conflicts)  # Just here to like nicer in the output
        if force:
            logger.confirm(f"Going to overwrite the following subscriptions:\n{conflicts_str}")
        else:
            logger.error(
                f"Found the following existing subscriptions:\n{conflicts_str}\n"
                f"Pass the --force flag if you'd like to overwrite them."
            )
            sys.exit(1)


def convert_opml_to_dict(path) -> dict:
    tree = parse_ompl(path)
    char_map = unicode.get_common_char_mapping()
    subscriptions = {}
    for node in tree.findall(".//outline"):
        rss_type = node.attrib.get("type")
        url = node.attrib.get("xmlUrl")
        title = node.attrib.get("title")
        title = convert_common_unicode_chars(title, char_map)
        if rss_type != "rss":
            logger.debug(f"Unknown type for `{title}`: {rss_type}")
            continue
        subscriptions[title] = url
    return subscriptions


def convert_common_unicode_chars(string, char_map) -> str:
    for char, replacement in char_map.items():
        if char in string:
            string = string.replace(char, replacement)
    return string


def parse_ompl(path) -> ElementTree.ElementTree:
    with open(path) as f:
        try:
            return ElementTree.parse(f)
        except ElementTree.ParseError:
            logger.error(f"Could not parse `{path}`.\nIt's probably not a proper OPML file.")
            sys.exit(1)
