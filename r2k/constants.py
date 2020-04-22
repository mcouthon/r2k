import os

CONFIG_ENV_VAR = "RSS_TO_KINDLE_CONFIG"

DEFAULT_APP_PATH = os.path.expanduser("~/.r2k")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_APP_PATH, "config.yml")


class Parser:
    """A convenience class to represent the available parsing options"""

    PUSH_TO_KINDLE = "pushtokindle"
    MERCURY = "mercury"
    SUPPORTED_PARSERS = [MERCURY, PUSH_TO_KINDLE]
