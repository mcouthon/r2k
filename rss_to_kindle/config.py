import os
from typing import Union

import yaml

from .cli import logger
from .constants import CONFIG_ENV_VAR


class Config:
    DEFAULT_VALUES: dict = {"subscriptions": {}}

    def __init__(self, path) -> None:
        self._path = path
        self._config = Config.DEFAULT_VALUES.copy()

    def load_config(self) -> None:
        if not os.path.exists(self._path):
            logger.warning(
                f"Could not locate a configuration in the path {self._path}\n"
                f"If you want to create a new configuration, run `rss-to-kindle init`.\n"
                f"If you already have a configuration file, pass it as an env var to `{CONFIG_ENV_VAR}`"
            )

        with open(self._path) as f:
            file_config = yaml.safe_load(f)

        self._config.update(file_config)

    def __getattr__(self, item) -> Union[str, dict]:
        # Allow for private arguments
        if item.startswith("_"):
            return super().__getattribute__(item)

        if item in self._config:
            return self._config[item]
        raise AttributeError(f"Could not find a `{item}` attribute in the config")

    def __setattr__(self, key, value) -> None:
        # Allow for private arguments
        if key.startswith("_"):
            return super().__setattr__(key, value)

        self._config[key] = value
        self.save()

    def save(self):
        with open(self._path, "w") as f:
            yaml.safe_dump(self._config, f, default_flow_style=False)

    @property
    def send_to(self) -> str:
        return f"{self.kindle_address}@pushtokindle.com"

    def as_dict(self) -> dict:
        return self._config

    def reset(self, new_config) -> None:
        self._config = Config.DEFAULT_VALUES.copy()
        self._config.update(new_config)
        self.save()

    def __iter__(self):
        return self._config.__iter__()


_config = None


def get_config(path, load=True) -> Config:
    global _config
    if not _config:
        _config = Config(path)
        if load:
            _config.load_config()
    return _config
