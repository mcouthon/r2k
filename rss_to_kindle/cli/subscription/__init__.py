import click

from .subscription_add import subscription_add
from .subscription_import import subscription_import
from .subscription_remove import subscription_remove
from .subscription_show import subscription_show


@click.group()
def subscription() -> None:
    """Interact with the RSS subscriptions."""
    pass


subscription.add_command(subscription_import)
subscription.add_command(subscription_show)
subscription.add_command(subscription_remove)
subscription.add_command(subscription_add)
