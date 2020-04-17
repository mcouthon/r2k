import click

from .feed_add import feed_add
from .feed_import import feed_import
from .feed_remove import feed_remove
from .feed_show import feed_show


@click.group()
def feed() -> None:
    """Interact with the RSS feeds."""
    pass


feed.add_command(feed_import)
feed.add_command(feed_show)
feed.add_command(feed_remove)
feed.add_command(feed_add)
