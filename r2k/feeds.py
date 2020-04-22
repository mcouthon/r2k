from datetime import datetime, timedelta
from typing import List, Optional

import feedparser
from pick import pick

from .dates import get_pretty_date_str, parse_date


class Feed(feedparser.FeedParserDict):
    """Represents a single, feedparser-parsed RSS feed"""

    def __init__(self, feed_url: str):
        """Constructor"""
        super().__init__(feedparser.parse(feed_url))

    def find_unread_articles_from_user(self) -> List[feedparser.FeedParserDict]:
        """Ask the user what was the last article they have already read, and return all the newer ones"""
        last_read_index = self.find_last_read_article()
        return self.entries[:last_read_index]

    def find_last_read_article(self) -> int:
        """Find the last article from the feed that the user has already read, and return its index"""
        options = [f"{entry.title} ({self.get_str_date_from_entry(entry)})" for entry in self.entries]
        options.append("I haven't read any of these :(")
        title = "Please choose the *last* article from this feed that you've already read"
        _, index = pick(options, title)
        return index

    def get_parsed_date_from_entry(self, entry: feedparser.FeedParserDict) -> datetime:
        """Return a datetime object parsed from the string date value"""
        raw_date = self.get_raw_date_from_entry(entry)
        return parse_date(raw_date)

    @staticmethod
    def get_raw_date_from_entry(entry: feedparser.FeedParserDict) -> str:
        """Return the raw string date as set up in the entry"""
        default = str(datetime.utcnow() - timedelta(days=30))
        return entry.get("published") or entry.get("updated") or default

    def get_str_date_from_entry(self, entry: feedparser.FeedParserDict) -> str:
        """Return a nicely formatted string from the date in the entry"""
        raw_date = self.get_raw_date_from_entry(entry)
        return get_pretty_date_str(raw_date)

    def find_unread_articles_from_date(self, last_updated: str) -> List[feedparser.FeedParserDict]:
        """Find all the new articles since `last_updated`"""
        last_updated_date = parse_date(last_updated)
        return [entry for entry in self.entries if self.get_parsed_date_from_entry(entry) > last_updated_date]

    def get_unread_articles(self, last_updated: Optional[str]) -> List[feedparser.FeedParserDict]:
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
        return unread_articles
