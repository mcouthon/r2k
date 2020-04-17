import smtplib

import click

from r2k.cli import cli_utils, logger
from r2k.config import Config, get_config


@click.command("add")
@cli_utils.config_path_option()
@click.option(
    "-f", "--feed", type=str, required=False, help="Title of a (optional) feed. If not passed, all feeds will be sent"
)
def kindle_send(path: str, feed: str) -> None:
    """Send updates from one or all feeds."""
    config = get_config(path)

    logger.info(f"{config}{feed}")


def create_message(config: Config, title: str, url: str) -> str:
    """Generate an SMTP message"""
    return f"""\
From: {config.send_from}
To: {", ".join([config.send_to, config.send_to])}
Subject: {title}

{url}
"""


def send_webpage_to_kindle(config: Config, title: str, url: str) -> None:
    """Send a webpage to Kindle"""
    body = create_message(config, title, url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.ehlo()
        server.login(config.send_from, config.password)
        server.sendmail(config.send_from, config.sent_to, body)

    logger.debug("Email successfully sent!")
