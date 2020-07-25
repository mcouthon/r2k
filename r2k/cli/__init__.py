import click

from r2k.cli.config import config
from r2k.cli.feed import feed
from r2k.cli.kindle import kindle


@click.group()
@click.option("-v", "--verbose", is_flag=True, default=False, help="If set, will print DEBUG messages")
@click.option("--no-ansi", is_flag=True, default=False, help="Disable ANSI output")
@click.pass_context
def main(ctx: click.Context, verbose: bool, no_ansi: bool) -> None:
    """A tool to send items from RSS feeds to Kindle"""
    setattr(ctx, "verbose", verbose)
    setattr(ctx, "no_ansi", no_ansi)


main.add_command(config)
main.add_command(feed)
main.add_command(kindle)


if __name__ == "__main__":
    main()
