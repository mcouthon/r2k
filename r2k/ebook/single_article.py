import requests
from bs4 import BeautifulSoup

from r2k.feeds import Article


class SingleArticle(Article):
    """Represents a single (i.e. not part of a feed) article for sending it to kindle"""

    def __init__(self, url: str) -> None:
        """Constructor"""
        super().__init__({"link": url})

        self.title = self.get_title()

    def get_title(self) -> str:
        """Find the article's title"""
        reqs = requests.get(self.link)
        soup = BeautifulSoup(reqs.text, "html.parser")

        for title in soup.find_all("title"):
            return title.get_text()
        raise RuntimeError("No title found for article")
