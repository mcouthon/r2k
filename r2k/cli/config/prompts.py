import click

from r2k.cli import logger
from r2k.constants import Parser


class Prompt:
    """A convenience class to get the correct prompt per config value"""

    send_from = dict(text="Please provide your gmail email address")
    password = dict(text="Please provide your gmail app password", hide_input=True)
    kindle_address = dict(text="Please provide your free kindle address (e.g. my_kindle@kindle.com)")
    parser = dict(
        text="Please choose the parser you're going to use",
        default=Parser.READABILITY.value,
        type=click.Choice(Parser.__values__),
    )

    @classmethod
    def get(cls, key: str) -> str:
        """Get a config value (using click's prompt)"""
        kwargs = getattr(cls, key, dict(text=f"Please provide a new value for {key}"))
        return logger.prompt(**kwargs)
