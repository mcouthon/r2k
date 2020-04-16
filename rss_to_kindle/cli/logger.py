import click

from .cli_utils import is_verbose


def secho(msg, fg, bold=True, **styles):
    if not isinstance(msg, str):
        msg = str(msg)
    styles["bold"] = bold
    return click.secho(msg, fg=fg, **styles)


def warning(msg, **styles):
    secho(msg, "yellow", **styles)


def error(msg, **styles):
    secho(msg, "red", **styles)


def info(msg, **styles):
    secho(msg, "blue", **styles)


def debug(msg):
    if is_verbose():
        secho(msg, "white", bold=False)


def prompt(text, hide_input=False, fg="cyan", **styles):
    styles["bold"] = True
    text = click.style(text, fg=fg, **styles)
    return click.prompt(text, hide_input=hide_input)


def confirm(text, default=True, fg="cyan", **styles):
    styles["bold"] = True
    text = click.style(text, fg=fg, **styles)
    return click.confirm(text, default=default)
