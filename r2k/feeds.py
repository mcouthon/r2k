# from datetime import datetime, timedelta
from typing import List, Optional

import arrow
import feedparser
from pick import pick

from .dates import get_pretty_date_str, parse_date


class Article(feedparser.FeedParserDict):
    """Represents a single article in a feed"""

    def get_parsed_date(self: feedparser.FeedParserDict) -> arrow.Arrow:
        """Return a datetime object parsed from the string date value"""
        raw_date = self.get_raw_date()
        return parse_date(raw_date)

    def get_raw_date(self: feedparser.FeedParserDict) -> str:
        """Return the raw string date as set up in the entry"""
        default = str(arrow.now().shift(days=-30))
        return self.get("published") or self.get("updated") or default

    def get_str_date(self: feedparser.FeedParserDict) -> str:
        """Return a nicely formatted string from the date in the entry"""
        raw_date = self.get_raw_date()
        return get_pretty_date_str(raw_date)


class Feed(feedparser.FeedParserDict):
    """Represents a single, feedparser-parsed RSS feed"""

    def __init__(self, feed_url: str, feed_title: str):
        """Constructor"""
        super().__init__(feedparser.parse(feed_url))
        self.title = feed_title

    def find_unread_articles_from_user(self) -> List[Article]:
        """Ask the user what was the last article they have already read, and return all the newer ones"""
        last_read_index = self.find_last_read_article()
        return [Article(entry) for entry in self.entries[:last_read_index]]

    def find_last_read_article(self) -> int:
        """Find the last article from the feed that the user has already read, and return its index"""
        articles = [Article(entry) for entry in self.entries]
        options = [f"{article.title} ({article.get_str_date()})" for article in articles]
        options.append("I haven't read any of these :(")
        title = f"Please choose the *last* article from `{self.title}` that you've already read"
        _, index = pick(options, title)
        return index

    def find_unread_articles_from_date(self, last_updated: arrow.Arrow) -> List[Article]:
        """Find all the new articles since `last_updated`"""
        # Some fancy walrus operator fun, because why not?
        return [article for entry in self.entries if (article := Article(entry)).get_parsed_date() > last_updated]

    def get_unread_articles(self, last_updated: Optional[arrow.Arrow]) -> List[Article]:
        """
        Return all the new articles

            * either since the last time r2k has ran, or
            * if this is the first time r2k is running for this feed, by asking the user which was the last article
            from the feed that they have already read, and only sending them the ones that came after
        """
        if last_updated:
            unread_articles = self.find_unread_articles_from_date(last_updated)
        else:
            unread_articles = self.find_unread_articles_from_user()

        # Reverse, as we want the oldest articles first
        unread_articles.reverse()
        return unread_articles
