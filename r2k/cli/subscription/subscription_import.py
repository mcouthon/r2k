import sys
from xml.etree import ElementTree

import click
import yaml

from r2k.cli import cli_utils, logger, unicode
from r2k.config import Config, get_config


@click.command("import")
@cli_utils.config_path_option()
@click.argument("opml-path", required=True, type=click.types.Path(exists=True))
@cli_utils.force_option("If set will update existing subscriptions")
def subscription_import(path: str, opml_path: str, force: bool) -> None:
    """Import subscriptions from an OPML file."""
    subscriptions = convert_opml_to_dict(opml_path)
    config = get_config(path)

    validate_conflicts(subscriptions, config, force)

    config.subscriptions.update(subscriptions)
    config.save()

    logger.info("Successfully imported the subscriptions!")


def validate_conflicts(subscriptions: dict, config: Config, force: bool) -> None:
    """Error out if the force flag was not passed and there are conflicts between new and existing subscriptions"""
    new_subscriptions = set(subscriptions.keys())
    old_subscriptions = set(config.subscriptions.keys())
    conflicts = new_subscriptions & old_subscriptions
    if conflicts:
        conflicts_str = yaml.safe_dump(sorted(list(conflicts)))  # Just here to like nicer in the output
        if force:
            logger.confirm(f"Going to overwrite the following subscriptions:\n{conflicts_str}")
        else:
            logger.error(
                f"Found the following existing subscriptions:\n{conflicts_str}\n"
                f"Pass the --force flag if you'd like to overwrite them."
            )
            sys.exit(1)


def convert_opml_to_dict(path: str) -> dict:
    """Convert an OPML file to a dictionary, for easier storing in the configuration YAML"""
    tree = parse_ompl(path)
    char_map = unicode.get_common_char_mapping()
    subscriptions = {}
    for node in tree.findall(".//outline"):
        # The `title` and `text` are usually identical
        title = node.attrib.get("title", node.attrib.get("text"))
        if not title:
            logger.debug("Could not find title for RSS feed")
            continue
        title = convert_common_unicode_chars(title, char_map)

        url = node.attrib.get("xmlUrl")
        if not url:
            logger.debug(f"Could not find URL for `{title}`")
            continue

        rss_type = node.attrib.get("type")
        if rss_type != "rss":
            logger.debug(f"Unknown type for `{title}`: {rss_type}")
            continue

        subscriptions[title] = url
    return subscriptions


def convert_common_unicode_chars(string: str, char_map: dict) -> str:
    """Replace common unicode characters with comparable ASCII values"""
    for char, replacement in char_map.items():
        if char in string:
            string = string.replace(char, replacement)
    return string


def parse_ompl(path: str) -> ElementTree.ElementTree:
    """Parse the OPML file and error out if it's in the wrong format"""
    with open(path) as f:
        try:
            return ElementTree.parse(f)
        except ElementTree.ParseError:
            logger.error(f"Could not parse `{path}`.\nIt's probably not a proper OPML file.")
            sys.exit(1)
