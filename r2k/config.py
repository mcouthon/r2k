from typing import Any, Iterator

import yaml

from .cli import logger


class Config:
    """Global configuration for the project"""

    DEFAULT_VALUES: dict = {"feeds": {}}

    def __init__(self) -> None:
        """Constructor"""
        self._path = ""
        self._config = Config.DEFAULT_VALUES.copy()

    def load(self, path: str) -> None:
        """Load configurations from a YAML file"""
        self._path = path

        logger.debug(f"Loading config from {self._path}")
        with open(self._path) as f:
            file_config = yaml.safe_load(f)

        self._config.update(file_config)

    def __getattr__(self, item: str) -> Any:
        """Override in order to allow accessing attributes from internal dict"""
        # Allow for private arguments
        if item.startswith("_"):
            return super().__getattribute__(item)

        if item in self._config:
            return self._config[item]
        raise AttributeError(f"Could not find a `{item}` attribute in the config")

    def __setattr__(self, key: str, value: Any) -> None:
        """Override in order to allow setting attributes to internal dict"""
        # Allow for private arguments
        if key.startswith("_"):
            return super().__setattr__(key, value)

        self._config[key] = value
        self.save()

    def save(self) -> None:
        """Dump the contents of the internal dict to file"""
        if not self._path:
            raise FileNotFoundError("Path not set in Config. Need to run config.load before running config.save")

        with open(self._path, "w") as f:
            yaml.safe_dump(self._config, f, default_flow_style=False)

    @property
    def send_to(self) -> str:
        """Override in order to set the pushtokindle hostname"""
        # TODO: Make configurable - consider services other than pushtokindle, as well as cleaning out the article
        # using newspaper
        kindle_address = self.kindle_address.split("@")[0]
        return f"{kindle_address}@pushtokindle.com"

    def as_dict(self) -> dict:
        """Return the underlying dict"""
        return self._config

    def reset(self, new_config: dict) -> None:
        """Set a new config instead of the existing one"""
        self._config = Config.DEFAULT_VALUES.copy()
        self._config.update(new_config)
        self.save()

    def __iter__(self) -> Iterator:
        """Iterate over the internal dict"""
        return self._config.__iter__()


config = Config()
