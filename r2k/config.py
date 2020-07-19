from dataclasses import asdict, dataclass, field, fields
from typing import Any, List, Optional

import yaml

from .cli import logger
from .constants import Parser


@dataclass
class Config:
    """Global configuration for the project"""

    feeds: dict
    password: str
    kindle_address: str
    send_from: str
    send_to: str = field(init=False, default="")
    parser: Parser = Parser.READABILITY

    # Internal properties not accessible outside the class
    _path: str = field(init=False, repr=False)
    _loaded: bool = field(init=False, repr=False, default=False)

    def __post_load__(self) -> None:
        """Tasks to perform after loading the config from the YAML"""
        self._loaded = True
        if self.parser == Parser.PUSH_TO_KINDLE:
            kindle_address = self.kindle_address.split("@")[0]
            self.send_to = f"{kindle_address}@pushtokindle.com"
        else:
            self.send_to = self.kindle_address

    def load(self, path: str) -> None:
        """Load configurations from a YAML file"""
        self._path = path

        logger.debug(f"Loading config from {self._path}")
        with open(self._path) as f:
            file_config = yaml.safe_load(f)

        self.__dict__.update(file_config)
        self.__post_load__()

    def __setattr__(self, key: str, value: Any) -> None:
        """Override in order to allow dumping changes to file"""
        super().__setattr__(key, value)
        self.save()

    def save(self, path: Optional[str] = None) -> None:
        """Dump the contents of the internal dict to file"""
        if not self._loaded:
            return

        if not self._path:
            if path:
                self._path = path
            else:
                raise FileNotFoundError("Path not set in Config. Need to run config.load before running config.save")

        with open(self._path, "w") as f:
            yaml.safe_dump(self.as_dict(), f, default_flow_style=False)

    def as_dict(self) -> dict:
        """Return the underlying dict"""
        return asdict(self)

    @classmethod
    def fields(cls) -> List[str]:
        """Return a list with all the publicly exposed fields of the Config class"""
        # Ignoring mypy typing validation here, as for some reason it assumes that f.type is always Field, but it isn't
        return [f.name for f in fields(cls) if issubclass(f.type, (str, Parser)) and not f.name.startswith("_")]


config = Config(feeds={}, kindle_address="", password="", send_from="")
