from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type

from bs4 import BeautifulSoup


class ParserBase(ABC):
    """
    Base class for parsers
    """

    @abstractmethod
    def __enter__(self) -> ParserBase:
        """Context manager __enter__"""
        pass

    @abstractmethod
    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> bool:
        """Context manager __exit__"""
        pass

    @abstractmethod
    def parse(self, url: str) -> dict:
        """Main function used to parse the article from a URL"""
        pass

    @staticmethod
    def fix_blockquotes(html: str) -> str:
        """Mobi doesn't seem to deal well with <p> tags inside <blockquote> tags. So we replace <p> with <div>"""
        soup = BeautifulSoup(html, "html.parser")
        for quote in soup.find_all("blockquote"):
            if not quote.p:
                continue
            quote.p.wrap(soup.new_tag("div"))  # Wrap all <p> elements with <div>
            quote.p.unwrap()  # Unwrap removes the element and replaces it with its content

        return soup.decode(pretty_print=True)
