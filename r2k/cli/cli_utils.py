from typing import Callable

import click

from r2k.constants import CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH


def config_path_option(exists: bool = True) -> Callable:
    """
    A convenience decorator

    As we'll probably want to be able to specify the config in pretty much every console command
    """

    def decorator(f: Callable) -> Callable:
        option = click.option(
            "-p",
            "--path",
            default=DEFAULT_CONFIG_PATH,
            envvar=CONFIG_ENV_VAR,
            show_default=True,
            type=click.types.Path(exists=exists),
            help="Path to the configuration file",
        )
        return option(f)

    return decorator


def force_option(help_text: str) -> Callable:
    """
    A convenience decorator

    For various --force click options, that allows one to provide a custom help text
    """

    def decorator(f: Callable) -> Callable:
        option = click.option(
            "--force", default=False, show_default=True, is_flag=True, type=click.types.BOOL, help=help_text,
        )
        return option(f)

    return decorator


def get_global_context() -> click.Context:
    """Return the top-level global Click context"""
    ctx = click.get_current_context()
    while ctx.parent:
        ctx = ctx.parent
    return ctx


def is_verbose() -> bool:
    """Return True if --verbose was passed to the top-level click command"""
    return get_global_context().params["verbose"]
