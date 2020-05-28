from enum import Enum
from os.path import dirname, expanduser, join

CONFIG_ENV_VAR = "RSS_TO_KINDLE_CONFIG"

HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}

DEFAULT_APP_PATH = expanduser("~/.r2k")
DEFAULT_CONFIG_PATH = join(DEFAULT_APP_PATH, "config.yml")

PACKAGE_DIR = dirname(__file__)
TOP_LEVEL_DIR = dirname(PACKAGE_DIR)
TEMPLATES_DIR = join(TOP_LEVEL_DIR, "templates")

# Number of articles to put in a single EPUB eBook. Otherwise the email size might exceed GMAIL's 25MB limit
ARTICLE_EBOOK_LIMIT = 20


class Parser(Enum):
    """A convenience class to represent the available parsing options"""

    PUSH_TO_KINDLE = "pushtokindle"
    MERCURY = "mercury"
    READABILITY = "readability"

    __values__ = PUSH_TO_KINDLE, MERCURY, READABILITY
