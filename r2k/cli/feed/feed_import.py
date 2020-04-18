import sys
from typing import Optional
from xml.etree import ElementTree

import click
import yaml

from r2k.cli import cli_utils, logger
from r2k.config import config
from r2k.unicode import strip_common_unicode_chars


@click.command("import")
@cli_utils.config_path_option()
@click.argument("opml-path", required=True, type=click.types.Path(exists=True))
@cli_utils.force_option("If set will update existing feeds")
def feed_import(opml_path: str, force: bool) -> None:
    """Import feeds from an OPML file."""
    feeds = convert_opml_to_dict(opml_path)

    validate_conflicts(feeds, force)

    config.feeds.update(feeds)
    config.save()

    logger.info("Successfully imported the feeds!")


def validate_conflicts(feeds: dict, force: bool) -> None:
    """Error out if the force flag was not passed and there are conflicts between new and existing feeds"""
    new_feeds = set(feeds.keys())
    old_feeds = set(config.feeds.keys())
    conflicts = new_feeds & old_feeds
    if conflicts:
        conflicts_str = yaml.safe_dump(sorted(list(conflicts)))  # Just here to like nicer in the output
        if force:
            logger.confirm(f"Going to overwrite the following feeds:\n{conflicts_str}")
        else:
            logger.error(
                f"Found the following existing feeds:\n{conflicts_str}\n"
                f"Pass the --force flag if you'd like to overwrite them."
            )
            sys.exit(1)


def convert_opml_to_dict(path: str) -> dict:
    """Convert an OPML file to a dictionary, for easier storing in the configuration YAML"""
    tree = parse_ompl(path)
    feeds = {}
    for node in tree.findall(".//outline"):
        if title := get_title(node):
            if url := get_url(node, title):
                if is_rss(node, title):
                    feeds[title] = {"url": url}
    return feeds


def get_title(node: ElementTree.Element) -> Optional[str]:
    """Retrieve the feed's title from the XML element"""
    # The `title` and `text` are usually identical
    title = node.attrib.get("title", node.attrib.get("text"))
    if title:
        title = strip_common_unicode_chars(title)
    else:
        logger.debug("Could not find title for RSS feed")
    return title


def get_url(node: ElementTree.Element, title: str) -> Optional[str]:
    """Retrieve the feed's URL from the XML element"""
    url = node.attrib.get("xmlUrl")
    if not url:
        logger.debug(f"Could not find URL for `{title}`")
    return url


def is_rss(node: ElementTree.Element, title: str) -> bool:
    """Return true if the element is indeed an RSS feed"""
    rss_type = node.attrib.get("type")
    if rss_type != "rss":
        logger.debug(f"Unknown type for `{title}`: {rss_type}")
        return False
    return True


def parse_ompl(path: str) -> ElementTree.ElementTree:
    """Parse the OPML file and error out if it's in the wrong format"""
    with open(path) as f:
        try:
            return ElementTree.parse(f)
        except ElementTree.ParseError:
            logger.error(f"Could not parse `{path}`.\nIt's probably not a proper OPML file.")
            sys.exit(1)
