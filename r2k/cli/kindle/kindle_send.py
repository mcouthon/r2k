import sys
from datetime import datetime
from typing import List

import click

from r2k.cli import cli_utils, logger
from r2k.config import config
from r2k.constants import Parser
from r2k.ebook.epub_builder import create_epub
from r2k.email_sender import send_epub, send_urls
from r2k.feeds import Article, Feed


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
    logger.info(f"[Parsing articles with the `{config.parser}` parser]\n")
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

    local_feed["updated"] = datetime.now().astimezone()
    config.save()


def get_unread_articles_for_feed(local_feed: dict) -> List[Article]:
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


def send_updates(unread_articles: List[Article], feed_title: str) -> None:
    """Iterate over `unread_articles`, and send each one to the kindle"""
    if unread_articles:
        if Parser(config.parser) == Parser.PUSH_TO_KINDLE:
            successful_count = send_urls([(article.title, article.link) for article in unread_articles])
        else:
            successful_count = send_epub_book(unread_articles, feed_title)

        logger.info(f"Successfully sent {successful_count} articles from the `{feed_title}` feed!")
    else:
        logger.info(f"No new content for `{feed_title}`")


def send_epub_book(unread_articles: List[Article], feed_title: str) -> int:
    """Create an EPUB book from all the unread articles and send it via email"""
    date_range = get_unread_articles_date_range(unread_articles)
    title = f"{feed_title} [{date_range}]"
    epub_book = create_epub(unread_articles, title)
    success = send_epub(title, epub_book)
    return len(unread_articles) if success else 0


def get_unread_articles_date_range(unread_articles: List[Article]) -> str:
    """Return a nicely formatted string with the range of dates for the article list"""
    if len(unread_articles) == 1:
        return unread_articles[0].get_str_date(short_date=True)
    else:
        first_date = unread_articles[-1].get_str_date(short_date=True)
        last_date = unread_articles[0].get_str_date(short_date=True)
        return f"{first_date} — {last_date}"
