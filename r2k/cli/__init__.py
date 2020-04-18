import click

from .config import config
from .feed import feed
from .kindle import kindle


@click.group()
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="If set, will print DEBUG messages",
)
def main(verbose: bool) -> None:
    """A tool to send items from RSS feeds to Kindle"""
    ctx = click.get_current_context()
    setattr(ctx, "verbose", verbose)


main.add_command(config)
main.add_command(feed)
main.add_command(kindle)


if __name__ == "__main__":
    main()
