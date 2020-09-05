from __future__ import annotations

from types import TracebackType
from typing import Optional, Type

from readability import Document
from requests import get

from r2k.constants import HTML_HEADERS

from .base_parser import ParserBase


class ReadabilityParser(ParserBase):
    """
    Parser that uses the readability module
    """

    def __enter__(self) -> ReadabilityParser:
        """Nothing to do here"""
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> bool:
        """Nothing to do here"""
        pass

    def parse(self, url: str) -> dict:
        """Download the article and parse it"""
        r = get(url, headers=HTML_HEADERS)
        doc = Document(r.text, url=url)
        html = doc.summary(html_partial=True)
        clean_html = self.fix_blockquotes(html)
        return {"content": clean_html}
