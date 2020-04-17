import os
from typing import Any, Iterator

import yaml

from .cli import logger
from .constants import CONFIG_ENV_VAR


class Config:
    """Global configuration for the project"""

    DEFAULT_VALUES: dict = {"subscriptions": {}}

    def __init__(self, path: str) -> None:
        """Constructor"""
        self._path = path
        self._config = Config.DEFAULT_VALUES.copy()

    def load_config(self) -> None:
        """Load configurations from a YAML file"""
        if not os.path.exists(self._path):
            logger.warning(
                f"Could not locate a configuration in the path {self._path}\n"
                f"If you want to create a new configuration, run `r2k init`.\n"
                f"If you already have a configuration file, pass it as an env var to `{CONFIG_ENV_VAR}`"
            )

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
        with open(self._path, "w") as f:
            yaml.safe_dump(self._config, f, default_flow_style=False)

    @property
    def send_to(self) -> str:
        """Override in order to set the pushtokindle hostname"""
        # TODO: Make configurable
        return f"{self.kindle_address}@pushtokindle.com"

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


_config = None


def get_config(path: str, load: bool = True) -> Config:
    """Return an initialized Config object"""
    global _config
    if not _config:
        _config = Config(path)
        if load:
            _config.load_config()
    return _config
