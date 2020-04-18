from typing import List

import feedparser


def get_articles_from_feed(feed_url: str) -> List[feedparser.FeedParserDict]:
    feed = feedparser.parse(feed_url)
    return [feed]
