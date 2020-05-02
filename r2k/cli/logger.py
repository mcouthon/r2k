from typing import Any, Optional

import click

from .cli_utils import is_verbose, no_ansi


def style(msg: str, fg: str, bold: bool) -> str:
    """
    Styles a text with ANSI styles and returns the new string

    If the --no-ansi flag was passed, no styles are applied
    """
    if no_ansi():
        return msg
    else:
        return click.style(msg, fg=fg, bold=bold)


def secho(msg: Any, fg: str, bold: bool = False) -> None:
    """Similar to click.secho"""
    if not isinstance(msg, (str, bytes)):
        msg = str(msg)
    click.echo(style(msg, fg=fg, bold=bold))


def warning(msg: Any) -> None:
    """click.echo in a yellow color"""
    secho(f"WARNING: {msg}", "yellow")


def error(msg: Any) -> None:
    """click.echo in a red color"""
    secho(f"ERROR: {msg}", "red")


def info(msg: Any) -> None:
    """click.echo in a blue color"""
    secho(msg, "blue")


def notice(msg: Any) -> None:
    """click.echo in a green color"""
    secho(msg, "green")


def log(msg: Any) -> None:
    """click.echo in a white color"""
    secho(msg, "white")


def debug(msg: Any) -> None:
    """click.echo in a white color, only if the --verbose flag was set"""
    if is_verbose():
        log(msg)


def prompt(
    text: str, hide_input: bool = False, fg: str = "cyan", default: Any = None, type: Optional[click.ParamType] = None
) -> Any:
    """Ask the user to enter a value, and return the result"""
    text = style(text, fg=fg, bold=True)
    return click.prompt(text, hide_input=hide_input, default=default, type=type)


def confirm(text: str, default: bool = True, fg: str = "cyan") -> bool:
    """Ask the user for confirmation and return the bool result"""
    text = style(text, fg=fg, bold=True)
    return click.confirm(text, default=default)
