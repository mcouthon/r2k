from typing import Any, Optional

import click

from .cli_utils import is_verbose


def secho(msg: Any, fg: str, bold: bool = False) -> None:
    """Similar to click.secho"""
    if not isinstance(msg, str):
        msg = str(msg)
    click.echo(click.style(msg, fg=fg, bold=bold))


def warning(msg: Any) -> None:
    """click.echo in a yellow color"""
    secho(f"WARNING: {msg}", "yellow")


def error(msg: Any) -> None:
    """click.echo in a red color"""
    secho(f"ERROR: {msg}", "red")


def info(msg: Any) -> None:
    """click.echo in a blue color"""
    secho(msg, "blue")


def debug(msg: Any) -> None:
    """click.echo in a white color"""
    if is_verbose():
        secho(msg, "white", bold=False)


def prompt(
    text: str, hide_input: bool = False, fg: str = "cyan", default: Any = None, type: Optional[click.ParamType] = None
) -> Any:
    """Ask the user to enter a value, and return the result"""
    text = click.style(text, fg=fg, bold=True)
    return click.prompt(text, hide_input=hide_input, default=default, type=type)


def confirm(text: str, default: bool = True, fg: str = "cyan") -> bool:
    """Ask the user for confirmation and return the bool result"""
    text = click.style(text, fg=fg, bold=True)
    return click.confirm(text, default=default)
