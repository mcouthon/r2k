import sys
import urllib.parse

import click
import feedparser
import requests
from bs4 import BeautifulSoup
from pick import pick

from r2k.cli import cli_utils, logger
from r2k.config import Config, config


@click.command("add")
@cli_utils.config_path_option()
@click.option("-t", "--title", type=str, required=True, help="The title of the feed")
@click.option("-u", "--url", type=str, required=True, help="The URL of the feed")
@cli_utils.force_option("If set will update existing feeds")
def feed_add(title: str, url: str, force: bool) -> None:
    """Add an RSS feed."""
    validate_existing_feeds(title, config, force)

    feeds = get_feeds_from_url(url)

    if not feeds:
        logger.error("Could not find an RSS feed")
        sys.exit(1)
    elif len(feeds) == 1:
        feed = feeds[0]
    else:
        feed, _ = pick(feeds, "Please choose the correct feed from this list:")

    config.feeds[title] = {"url": url}
    config.save()
    logger.info("Successfully added the feed!")


def validate_existing_feeds(title: str, config: Config, force: bool) -> None:
    """Error out if no force flag was passed and the feed already exists"""
    if title in config.feeds:
        if force:
            logger.confirm(f"Going to overwrite the following feed: {title}")
        else:
            logger.error(
                f"The following feed already exists: {title}\nPass the --force flag if you'd like to overwrite it"
            )
            sys.exit(1)


def get_feeds_from_url(url: str) -> list:
    """
    Try to parse the URL and find any RSS feeds in the webpage

    Adapted from: https://gist.github.com/alexmill/9bc634240531d81c3abe
    """
    logger.info(f"Attempting to find RSS feeds from {url}...")

    # If the URL itself is a proper RSS feed, just return it
    if is_rss_feed(url):
        logger.debug("URL is already a proper RSS feed")
        return [url]

    html = get_html(url)
    possible_feeds = get_feeds_from_links(html) + get_feeds_from_atags(url, html)

    return [url for url in set(possible_feeds) if is_rss_feed(url)]


def get_html(url: str) -> BeautifulSoup:
    """Parse the URL with bs4"""
    raw = requests.get(url).text
    return BeautifulSoup(raw, features="lxml")


def get_feeds_from_links(html: BeautifulSoup) -> list:
    """Try to find RSS feeds from link elements in the webpage"""
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


def get_feeds_from_atags(url: str, html: BeautifulSoup) -> list:
    """Try to find RSS feeds from a tags in the webpage"""
    possible_feeds = []

    parsed_url = urllib.parse.urlparse(url)
    if not (parsed_url.scheme and parsed_url.hostname):
        return []
    base = parsed_url.scheme + "://" + parsed_url.hostname
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href", None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base + href)
    return possible_feeds


def is_rss_feed(url: str) -> bool:
    """Test whether the URL is a proper RSS feed"""
    f = feedparser.parse(url)
    return len(f.entries) > 0
