import requests
from bs4 import BeautifulSoup

from r2k.feeds import Article


class SingleArticle(Article):
    """Represents a single (i.e. not part of a feed) article for sending it to kindle"""

    def __init__(self, url: str) -> None:
        """Constructor"""
        super().__init__({"link": url})
        reqs = requests.get(self.link)
        self._soup = BeautifulSoup(reqs.text, "html.parser")

        self.set_title()
        self.set_author()

    def set_title(self) -> None:
        """Set the article's title"""
        titles = self._soup.find_all("title")
        if titles:
            self.title = titles[0].get_text()
        else:
            self.title = self.link

    def set_author(self) -> None:
        """Set the article's author"""
        metas = self._soup.find_all("meta")
        for meta in metas:
            if meta.attrs.get("name") == "author":
                self.author = meta.attrs.get("content")
