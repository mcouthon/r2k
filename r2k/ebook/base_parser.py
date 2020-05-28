from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type


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
