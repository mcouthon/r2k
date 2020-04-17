import sys
import urllib.parse

import click
import feedparser
import requests
from bs4 import BeautifulSoup
from pick import pick

from rss_to_kindle.cli import cli_utils, logger
from rss_to_kindle.config import get_config


@click.command("add")
@cli_utils.config_path_option()
@click.option("-t", "--title", type=str, required=True, help="The title of the subscription")
@click.option("-u", "--url", type=str, required=True, help="The URL of the subscription")
@cli_utils.force_option("If set will update existing subscriptions")
def subscription_add(path, title, url, force) -> None:
    """Add an RSS subscription."""
    config = get_config(path)

    validate_existing_subscriptions(title, config, force)

    feeds = get_feeds_from_url(url)

    if not feeds:
        logger.error("Could not find an RSS feed")
        sys.exit(1)
    elif len(feeds) == 1:
        feed = feeds[0]
    else:
        feed, _ = pick(feeds, "Please choose the correct feed from this list:")

    config.subscriptions[title] = feed
    config.save()
    logger.info("Successfully added the subscription!")


def validate_existing_subscriptions(title, config, force) -> None:
    if title in config.subscriptions:
        if force:
            logger.confirm(f"Going to overwrite the following subscription: {title}")
        else:
            logger.error(
                f"The following subscription already exists: {title}\n"
                f"Pass the --force flag if you'd like to overwrite it"
            )
            sys.exit(1)


def get_feeds_from_url(url) -> list:
    """ Adapted from: https://gist.github.com/alexmill/9bc634240531d81c3abe """
    logger.info(f"Attempting to find RSS feeds from {url}...")

    # If the URL itself is a proper RSS feed, just return it
    if is_rss_feed(url):
        logger.debug("URL is already a proper RSS feed")
        return [url]

    html = get_html(url)
    possible_feeds = get_feeds_from_links(html) + get_feeds_from_atags(url, html)

    return [url for url in set(possible_feeds) if is_rss_feed(url)]


def get_html(url) -> BeautifulSoup:
    raw = requests.get(url).text
    return BeautifulSoup(raw, features="lxml")


def get_feeds_from_links(html) -> list:
    possible_feeds = []

    feed_urls = html.findAll("link", rel="alternate")
    for f in feed_urls:
        t = f.get("type", None)
        if t:
            if "rss" in t or "xml" in t:
                href = f.get("href", None)
                if href:
                    possible_feeds.append(href)
    return possible_feeds


def get_feeds_from_atags(url, html) -> list:
    possible_feeds = []

    parsed_url = urllib.parse.urlparse(url)
    base = parsed_url.scheme + "://" + parsed_url.hostname
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href", None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base + href)
    return possible_feeds


def is_rss_feed(url) -> bool:
    f = feedparser.parse(url)
    return len(f.entries) > 0
