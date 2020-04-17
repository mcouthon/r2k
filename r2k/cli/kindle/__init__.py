import click

from .kindle_send import kindle_send


@click.group()
def kindle() -> None:
    """Send articles to your Kindle."""
    pass


kindle.add_command(kindle_send)
