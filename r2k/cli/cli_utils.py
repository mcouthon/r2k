import os
from typing import Any, Callable, Union

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
            type=str,
            # When `expose_value` is set to False, the option is not passed to the click Commands.
            # In our case, the config path should always exist, unless we're in `r2k config init`.
            # As we're loading the config using the `load_config` callback, there's no need to pass the option on.
            expose_value=not exists,
            callback=load_config,
            help="Path to the configuration file",
        )
        return option(f)

    return decorator


def load_config(ctx: click.Context, param: Union[click.Option, click.Parameter], value: Any) -> Any:
    """Load the config immediately after getting the path"""
    if not value or ctx.resilient_parsing:
        return
    from r2k.config import config

    if param.expose_value:
        if is_verbose():
            click.echo("Not loading config as we're in `r2k config init`")
        return value
    else:
        if os.path.exists(value):
            config.load(value)
        else:
            click.secho(
                f"Could not locate a configuration in the specified path {value}\n"
                f"If you want to create a new configuration, run `r2k init`.\n"
                f"If you already have a configuration file, pass `-p PATH` to any of the CLI commands,\n"
                f"or pass it as as an env var to `{CONFIG_ENV_VAR}`",
                fg="red",
                bold=True,
            )
            ctx.exit(1)


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


def get_dummy_context() -> click.Context:
    """Return a dummy click context to allow using eg click.echo when not running an actual click command"""
    ctx = click.Context(click.Command("dummy"))
    ctx.params["verbose"] = True
    return ctx


def get_global_context() -> click.Context:
    """Return the top-level global Click context"""
    ctx = click.get_current_context(silent=True) or get_dummy_context()

    while ctx.parent:
        ctx = ctx.parent
    return ctx


def is_verbose() -> bool:
    """Return True if --verbose was passed to the top-level click command"""
    return get_global_context().params.get("verbose", False)


def no_ansi() -> bool:
    """Return True if --no-ansi was passed to the top-level click command"""
    return get_global_context().params.get("no_ansi", False)
