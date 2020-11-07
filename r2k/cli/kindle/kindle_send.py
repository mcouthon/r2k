import os
import sys
from typing import List

import arrow
import click

from r2k.cli import cli_utils, logger
from r2k.config import config
from r2k.constants import ARTICLE_EBOOK_LIMIT, Parser
from r2k.dates import get_pretty_date_str, now
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
    validate_parser()
    logger.info(f"[Parsing articles with the `{config.parser}` parser]\n")
    if feed_title:
        send_articles_for_feed(feed_title)
    else:
        logger.notice("Sending articles from all feeds...\n")
        for feed_title in config.feeds:
            send_articles_for_feed(feed_title)


def validate_parser() -> None:
    """Run various validations for the different parsers"""
    parser = Parser(config.parser)
    if parser == Parser.MERCURY:
        try:
            import docker  # noqa
        except ModuleNotFoundError:
            logger.error(
                "The `docker` module is not installed, but is required to use the `mercury` parser\n"
                "Consider either switching to a different parser (by running `r2k config set -k parser --force`)\n"
                "Or install the optional `docker` library by running `pip install 'r2k[docker]'`"
            )
            sys.exit(1)


def send_articles_for_feed(feed_title: str) -> None:
    """Find all the new/unread articles for a certain feed and send them to the user's kindle"""
    logger.notice(f"\nNow working on `{feed_title}`...")

    local_feed = get_local_feed(feed_title)
    unread_articles = get_unread_articles_for_feed(local_feed, feed_title)
    send_updates(unread_articles, feed_title)

    local_feed["updated"] = arrow.utcnow()
    config.save()


def get_unread_articles_for_feed(local_feed: dict, feed_title: str) -> List[Article]:
    """Find the all new articles for a certain feed"""
    rss_feed = Feed(local_feed["url"], feed_title)
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
            successful_count = send_epub_books(unread_articles, feed_title)

        if successful_count:
            logger.notice(f"Successfully sent {successful_count} articles from the `{feed_title}` feed!")
        else:
            logger.error(f"Failed to send any articles to `{feed_title}`. See errors above")
    else:
        logger.info(f"No new content for `{feed_title}`")


def send_epub_books(unread_articles: List[Article], feed_title: str) -> int:
    """
    Chunk the list of unread articles into chunks of max size ARTICLE_EBOOK_LIMIT

    This is in order to avoid creating too large of an EPUB and exceeding GMAIL's 25MB attachment size limit
    """
    successful_count = 0
    for i in range(0, len(unread_articles), ARTICLE_EBOOK_LIMIT):
        successful_count += send_epub_book(unread_articles[i : i + ARTICLE_EBOOK_LIMIT], feed_title)
    return successful_count


def send_epub_book(unread_articles: List[Article], feed_title: str) -> int:
    """Create an EPUB book from all the unread articles and send it via email"""
    date_range = get_unread_articles_date_range(unread_articles)
    title = f"{feed_title} [{date_range}]"
    epub_book = create_epub(unread_articles, title)
    try:
        success = send_epub(title, epub_book)
    finally:
        os.remove(epub_book)
    return len(unread_articles) if success else 0


def get_unread_articles_date_range(unread_articles: List[Article]) -> str:
    """Return a nicely formatted string with the range of dates for the article list"""
    if len(unread_articles) == 1:
        date = unread_articles[0].get_parsed_date()
        show_year = date.year != now().year
        return get_pretty_date_str(date, show_year=show_year)
    else:
        first_date = unread_articles[0].get_parsed_date()
        last_date = unread_articles[-1].get_parsed_date()
        show_year = not (first_date.year == last_date.year == now().year)
        first_date_str = get_pretty_date_str(first_date, show_year=show_year)
        last_date_str = get_pretty_date_str(last_date, show_year=show_year)
        return f"{first_date_str} — {last_date_str}"
