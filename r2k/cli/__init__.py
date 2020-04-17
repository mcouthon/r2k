import click

from .config import config
from .subscription import subscription


@click.group()
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="If set, will print DEBUG messages",
)
def main(verbose: bool) -> None:
    """A tool to send items from RSS subscriptions to Kindle"""
    ctx = click.get_current_context()
    setattr(ctx, "verbose", verbose)


main.add_command(config)
main.add_command(subscription)


if __name__ == "__main__":
    main()
