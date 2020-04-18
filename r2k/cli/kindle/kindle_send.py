import sys
from datetime import datetime
from typing import List

import click
import feedparser

from r2k.cli import cli_utils, logger
from r2k.config import config
from r2k.email import send_webpage_to_kindle
from r2k.feeds import Feed


@click.command("send")
@cli_utils.config_path_option()
@click.option(
    "-f",
    "--feed-title",
    type=str,
    required=False,
    help="Title of a (optional) feed. If not passed, updates for all feeds will be sent",
)
def kindle_send(feed_title: str) -> None:
    """Send updates from one or all feeds."""
    if feed_title:
        send_articles_for_feed(feed_title)
    else:
        logger.info("Sending articles from all feeds...")
        for feed_title in config.feeds:
            send_articles_for_feed(feed_title)


def send_articles_for_feed(feed_title: str) -> None:
    """Find all the new/unread articles for a certain feed and send them to the user's kindle"""
    logger.info(f"Getting articles from `{feed_title}`...")

    local_feed = get_local_feed(feed_title)
    unread_articles = get_unread_articles_for_feed(local_feed)

    send_updates(unread_articles, feed_title)
    local_feed["updated"] = str(datetime.now().astimezone())
    config.save()


def get_unread_articles_for_feed(local_feed: dict) -> List[feedparser.FeedParserDict]:
    """Find the all new articles for a certain feed"""
    rss_feed = Feed(local_feed["url"])
    last_updated = local_feed.get("updated")
    return rss_feed.get_unread_articles(last_updated)


def get_local_feed(feed_title: str) -> dict:
    """Get the feed if it exists in the feeds dict, or exit with an error"""
    feed = config.feeds.get(feed_title)
    if not feed:
        logger.error(f"Tried to fetch articles from an unknown feed `{feed_title}`")
        sys.exit(1)
    return feed


def send_updates(unread_articles: list, feed_title: str) -> None:
    """Iterate over `unread_articles`, and send each one to the kindle"""
    if unread_articles:
        for article in unread_articles:
            logger.info(f"Sending `{article.title}`...")
            send_webpage_to_kindle(article.title, article.link)
            logger.debug("Email successfully sent!")

        logger.info(f"Successfully sent {len(unread_articles)} articles from the `{feed_title}` feed!")
    else:
        logger.info(f"No new content for `{feed_title}`")
